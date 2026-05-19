// Higgins 2.0 — UI Message Stream parser (vanilla JS, no React)
// REQ-002 Phase 2.
//
// Consumes the AI SDK v6 `toUIMessageStreamResponse()` payload, which is a
// line-buffered SSE-flavored stream of JSON parts. Yields each part to the
// caller via an async generator.
//
// Recognised part `type` values (subset — full list in AI SDK docs):
//   start, start-step, finish-step, finish, error
//   text-start { id }
//   text-delta { id, delta }
//   text-end   { id }
//   tool-input-start    { toolCallId, toolName }
//   tool-input-delta    { toolCallId, inputTextDelta }
//   tool-input-available{ toolCallId, input }
//   tool-output-available{ toolCallId, output }
//
// Phase 3 will add artifact tool handling; for Phase 2 only the text-* parts
// matter — the helper `forTextDeltas` below is the convenience path.

/**
 * Stream parts out of a Response body. Tolerates either bare-JSON lines
 * or SSE-style `data: <json>` lines.
 */
export async function* parseHigginsStream(response) {
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} ${response.statusText}`);
  }
  if (!response.body) throw new Error('Response has no body');

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let newlineIdx;
      // eslint-disable-next-line no-cond-assign
      while ((newlineIdx = buffer.indexOf('\n')) !== -1) {
        const rawLine = buffer.slice(0, newlineIdx);
        buffer = buffer.slice(newlineIdx + 1);
        const line = rawLine.replace(/\r$/, '').trim();
        if (!line) continue;

        const payload = line.startsWith('data:') ? line.slice(5).trim() : line;
        if (!payload || payload === '[DONE]') continue;

        try {
          yield JSON.parse(payload);
        } catch (err) {
          console.warn('[higgins-stream] parse error', err, payload);
        }
      }
    }

    // Flush any trailing partial line
    const tail = buffer.trim();
    if (tail) {
      const payload = tail.startsWith('data:') ? tail.slice(5).trim() : tail;
      if (payload && payload !== '[DONE]') {
        try { yield JSON.parse(payload); } catch { /* ignore */ }
      }
    }
  } finally {
    try { reader.releaseLock(); } catch { /* ignore */ }
  }
}

/**
 * Convenience: yield only text deltas as plain strings.
 * Phase 2's only consumer needs this — Phase 3 will use the raw stream.
 */
export async function* forTextDeltas(response) {
  for await (const part of parseHigginsStream(response)) {
    if (part?.type === 'text-delta' && typeof part.delta === 'string') {
      yield part.delta;
    } else if (part?.type === 'error') {
      throw new Error(part.errorText || part.message || 'Stream error');
    }
  }
}
