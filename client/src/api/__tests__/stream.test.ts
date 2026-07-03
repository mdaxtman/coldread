import { afterEach, describe, expect, it, vi } from 'vitest'
import { parseSseChunk, streamRun } from '../stream'

afterEach(() => vi.unstubAllGlobals())

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(encoder.encode(c))
      controller.close()
    },
  })
}

describe('parseSseChunk', () => {
  it('parses complete events and returns leftover buffer', () => {
    const { events, rest } = parseSseChunk(
      'event: run_started\ndata: {"runId":"r1"}\n\nevent: stage_st',
    )
    expect(events).toEqual([{ event: 'run_started', data: { runId: 'r1' } }])
    expect(rest).toBe('event: stage_st')
  })

  it('ignores comment/keep-alive lines', () => {
    const { events } = parseSseChunk(': keep-alive\n\nevent: x\ndata: {}\n\n')
    expect(events).toEqual([{ event: 'x', data: {} }])
  })
})

describe('streamRun', () => {
  it('emits events split across chunk boundaries', async () => {
    const body = streamFromChunks([
      'event: run_started\ndata: {"runId"',
      ':"r1"}\n\nevent: stage_finished\ndata: {"stage":"fit","tokensIn":10}\n\n',
    ])
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(body, { status: 200 })))
    const seen: string[] = []
    await streamRun('/jds/1/fit/stream', undefined, (e) => seen.push(e.event))
    expect(seen).toEqual(['run_started', 'stage_finished'])
  })

  it('rejects on non-2xx', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('nope', { status: 500 })))
    await expect(streamRun('/x', undefined, () => {})).rejects.toThrow('500')
  })
})
