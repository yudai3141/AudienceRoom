/**
 * Server-Sent Events (SSE) ユーティリティ
 */

export interface SSEEvent {
  event: string;
  data: any;
}

/**
 * SSEストリームを読み取り、イベントを逐次的に返す
 *
 * @param response - fetch APIからのResponse（text/event-stream）
 * @returns SSEイベントの非同期イテレータ
 *
 * @example
 * ```ts
 * const response = await fetch('/api/stream', { method: 'POST', ... });
 * for await (const { event, data } of readSSEStream(response)) {
 *   if (event === 'text_chunk') {
 *     console.log(data.text);
 *   }
 * }
 * ```
 */
export async function* readSSEStream(
  response: Response
): AsyncIterableIterator<SSEEvent> {
  if (!response.body) {
    throw new Error("Response body is null");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;

        const eventMatch = line.match(/^event: (.+)$/m);
        const dataMatch = line.match(/^data: (.+)$/m);

        if (eventMatch && dataMatch) {
          try {
            yield {
              event: eventMatch[1],
              data: JSON.parse(dataMatch[1]),
            };
          } catch (error) {
            console.error("Failed to parse SSE data:", dataMatch[1], error);
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
