/**
 * Server-Sent Events (SSE) ユーティリティ
 */

/**
 * SSE イベントの型定義（型安全性のための Discriminated Union）
 *
 * 各イベントタイプごとに data の型が明確に定義されている。
 * これにより型アサーションが不要になり、TypeScript の型推論が正しく機能する。
 */
export type SSEEvent =
  | {
      event: "metadata";
      data: {
        participant_id?: number;
        speaker_id?: number;
      };
    }
  | {
      event: "text_chunk";
      data: {
        text: string;
      };
    }
  | {
      event: "audio_chunk";
      data: {
        audio_base64: string;
        sequence: number;
        text: string;
      };
    }
  | {
      event: "complete";
      data: {
        text: string;
        audio_sequence_count?: number;
      };
    }
  | {
      event: "error";
      data: {
        message: string;
      };
    };

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
              event: eventMatch[1] as SSEEvent["event"],
              data: JSON.parse(dataMatch[1]),
            } as SSEEvent;
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
