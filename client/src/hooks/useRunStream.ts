// SSE events → UI state. A reducer over a stream: same mental model as
// replaying a Redux action log, which makes it trivially unit-testable.

import { useCallback, useEffect, useRef, useState } from 'react'
import type { RunStreamEvent } from '../api/stream'
import { streamRun } from '../api/stream'

export interface StageInfo {
  stage: string
  seq: number
  status: 'running' | 'done'
  model?: string
  tokensIn?: number
  tokensOut?: number
  latencyMs?: number
  estCostUsd?: number
}

export interface TraceLine {
  at: number
  label: string
  message: string
  tone: 'info' | 'machine' | 'success' | 'error'
}

export interface RunStreamState {
  status: 'idle' | 'streaming' | 'complete' | 'failed'
  runId?: string
  stages: StageInfo[]
  trace: TraceLine[]
  error?: string
  resultId?: string
  totals?: { tokensIn: number; tokensOut: number; estCostUsd: number; durationMs?: number }
  startedAt?: number
}

export const INITIAL_RUN_STREAM_STATE: RunStreamState = {
  status: 'idle',
  stages: [],
  trace: [],
}

function traceLine(
  state: RunStreamState,
  label: string,
  message: string,
  tone: TraceLine['tone'],
): TraceLine {
  return { at: state.startedAt ? Date.now() - state.startedAt : 0, label, message, tone }
}

export function runStreamReducer(state: RunStreamState, e: RunStreamEvent): RunStreamState {
  const d = e.data
  switch (e.event) {
    case 'run_started': {
      const next: RunStreamState = {
        ...INITIAL_RUN_STREAM_STATE,
        status: 'streaming',
        runId: d.runId as string,
        startedAt: Date.now(),
      }
      // Run UUIDs are internal — the trace narrates for a human.
      return { ...next, trace: [traceLine(next, 'system', `${d.kind} run started`, 'info')] }
    }
    case 'stage_started': {
      const stage: StageInfo = { stage: d.stage as string, seq: d.seq as number, status: 'running' }
      return {
        ...state,
        stages: [...state.stages, stage],
        trace: [...state.trace, traceLine(state, stage.stage, 'calling model…', 'machine')],
      }
    }
    case 'stage_finished': {
      const stages = state.stages.map((s) =>
        s.seq === d.seq
          ? {
              ...s,
              status: 'done' as const,
              model: d.model as string,
              tokensIn: d.tokensIn as number,
              tokensOut: d.tokensOut as number,
              latencyMs: d.latencyMs as number,
              estCostUsd: d.estCostUsd as number,
            }
          : s,
      )
      const msg = `ok · ${d.tokensOut} tokens out · ${d.latencyMs}ms`
      return {
        ...state,
        stages,
        trace: [...state.trace, traceLine(state, d.stage as string, msg, 'success')],
      }
    }
    case 'run_completed':
      return {
        ...state,
        status: 'complete',
        resultId: d.resultId as string,
        totals: {
          tokensIn: d.tokensIn as number,
          tokensOut: d.tokensOut as number,
          estCostUsd: d.estCostUsd as number,
          durationMs: d.durationMs as number,
        },
        trace: [...state.trace, traceLine(state, 'system', 'run complete', 'success')],
      }
    case 'run_failed':
      return {
        ...state,
        status: 'failed',
        error: d.error as string,
        trace: [...state.trace, traceLine(state, 'system', d.error as string, 'error')],
      }
    default:
      return state
  }
}

export function useRunStream() {
  const [state, setState] = useState(INITIAL_RUN_STREAM_STATE)
  const abortRef = useRef<AbortController | null>(null)

  const start = useCallback(async (path: string, body?: unknown) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setState({ ...INITIAL_RUN_STREAM_STATE, status: 'streaming' })
    try {
      await streamRun(path, body, (e) => setState((s) => runStreamReducer(s, e)), controller.signal)
    } catch (err) {
      setState((s) =>
        s.status === 'complete' || s.status === 'failed'
          ? s
          : { ...s, status: 'failed', error: err instanceof Error ? err.message : 'stream lost' },
      )
    }
  }, [])

  const reset = useCallback(() => setState(INITIAL_RUN_STREAM_STATE), [])

  useEffect(() => () => abortRef.current?.abort(), [])

  return { state, start, reset }
}
