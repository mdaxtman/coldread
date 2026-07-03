import { describe, expect, it } from 'vitest'
import { INITIAL_RUN_STREAM_STATE, runStreamReducer } from '../useRunStream'

const ev = (event: string, data: Record<string, unknown>) => ({ event, data })

describe('runStreamReducer', () => {
  it('tracks the full happy path', () => {
    let s = INITIAL_RUN_STREAM_STATE
    s = runStreamReducer(s, ev('run_started', { runId: 'r1', kind: 'fit' }))
    expect(s.status).toBe('streaming')
    expect(s.runId).toBe('r1')

    s = runStreamReducer(s, ev('stage_started', { stage: 'fit', seq: 1 }))
    expect(s.stages).toEqual([{ stage: 'fit', seq: 1, status: 'running' }])

    s = runStreamReducer(
      s,
      ev('stage_finished', {
        stage: 'fit',
        seq: 1,
        model: 'claude-sonnet-4-20250514',
        tokensIn: 3318,
        tokensOut: 1102,
        latencyMs: 2140,
        stopReason: 'tool_use',
        estCostUsd: 0.041,
      }),
    )
    expect(s.stages[0].status).toBe('done')
    expect(s.stages[0].tokensOut).toBe(1102)

    s = runStreamReducer(
      s,
      ev('run_completed', {
        resultId: 'fr-1',
        tokensIn: 3318,
        tokensOut: 1102,
        estCostUsd: 0.041,
        callCount: 1,
        durationMs: 6780,
      }),
    )
    expect(s.status).toBe('complete')
    expect(s.resultId).toBe('fr-1')
    expect(s.totals?.estCostUsd).toBe(0.041)
  })

  it('run_failed preserves the partial trace', () => {
    let s = INITIAL_RUN_STREAM_STATE
    s = runStreamReducer(s, ev('run_started', { runId: 'r1', kind: 'generate' }))
    s = runStreamReducer(s, ev('stage_started', { stage: 'generate', seq: 1 }))
    s = runStreamReducer(s, ev('run_failed', { error: 'generator_failed: boom' }))
    expect(s.status).toBe('failed')
    expect(s.error).toContain('boom')
    expect(s.stages).toHaveLength(1) // partial trace kept
  })

  it('every event appends a trace line', () => {
    let s = INITIAL_RUN_STREAM_STATE
    s = runStreamReducer(s, ev('run_started', { runId: 'r1', kind: 'fit' }))
    s = runStreamReducer(s, ev('stage_started', { stage: 'fit', seq: 1 }))
    expect(s.trace.length).toBe(2)
    expect(s.trace[1].tone).toBe('machine')
  })
})
