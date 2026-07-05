// Minimal fetch-based SSE client. Native EventSource can't POST, so we
// parse the text/event-stream body from a ReadableStream ourselves.

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface RunStreamEvent {
  event: string
  data: Record<string, unknown>
}

/** Parse as many complete SSE events as `buffer` contains; return the rest. */
export function parseSseChunk(buffer: string): { events: RunStreamEvent[]; rest: string } {
  const events: RunStreamEvent[] = []
  const blocks = buffer.split('\n\n')
  const rest = blocks.pop() ?? '' // last piece may be incomplete
  for (const block of blocks) {
    let event = ''
    let data = ''
    for (const line of block.split('\n')) {
      if (line.startsWith('event: ')) event = line.slice(7)
      else if (line.startsWith('data: ')) data = line.slice(6)
      // lines starting with ':' are keep-alive comments — ignored
    }
    if (event && data) {
      events.push({ event, data: JSON.parse(data) as Record<string, unknown> })
    }
  }
  return { events, rest }
}

export async function streamRun(
  path: string,
  body: unknown | undefined,
  onEvent: (e: RunStreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })
  if (!res.ok || !res.body) throw new Error(`API ${res.status}: ${path}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const { events, rest } = parseSseChunk(buffer)
    buffer = rest
    events.forEach(onEvent)
  }
}
