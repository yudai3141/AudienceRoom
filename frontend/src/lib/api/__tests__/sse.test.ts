import { describe, it, expect } from "vitest";
import { readSSEStream } from "../sse";

describe("readSSEStream", () => {
  it("should parse SSE events correctly", async () => {
    // SSE形式のテキストを作成
    const sseText = `event: text_chunk
data: {"text":"こんにちは"}

event: text_chunk
data: {"text":"。"}

event: complete
data: {"text":"こんにちは。"}

`;

    // ReadableStreamを作成
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(sseText));
        controller.close();
      },
    });

    // Response オブジェクトを作成
    const response = new Response(stream, {
      headers: { "Content-Type": "text/event-stream" },
    });

    // イベントを収集
    const events = [];
    for await (const event of readSSEStream(response)) {
      events.push(event);
    }

    // 検証
    expect(events).toHaveLength(3);
    expect(events[0]).toEqual({
      event: "text_chunk",
      data: { text: "こんにちは" },
    });
    expect(events[1]).toEqual({
      event: "text_chunk",
      data: { text: "。" },
    });
    expect(events[2]).toEqual({
      event: "complete",
      data: { text: "こんにちは。" },
    });
  });

  it("should handle chunked data", async () => {
    // チャンクに分割されたデータ
    const chunks = [
      "event: metadata\n",
      "data: {\"participant",
      "_id\":1}\n\n",
      "event: text_chunk\ndata: ",
      "{\"text\":\"テスト\"}\n\n",
    ];

    const stream = new ReadableStream({
      start(controller) {
        chunks.forEach((chunk) => {
          controller.enqueue(new TextEncoder().encode(chunk));
        });
        controller.close();
      },
    });

    const response = new Response(stream);

    const events = [];
    for await (const event of readSSEStream(response)) {
      events.push(event);
    }

    expect(events).toHaveLength(2);
    expect(events[0]).toEqual({
      event: "metadata",
      data: { participant_id: 1 },
    });
    expect(events[1]).toEqual({
      event: "text_chunk",
      data: { text: "テスト" },
    });
  });

  it("should handle error events", async () => {
    const sseText = `event: error
data: {"message":"エラーが発生しました"}

`;

    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(new TextEncoder().encode(sseText));
        controller.close();
      },
    });

    const response = new Response(stream);

    const events = [];
    for await (const event of readSSEStream(response)) {
      events.push(event);
    }

    expect(events).toHaveLength(1);
    expect(events[0]).toEqual({
      event: "error",
      data: { message: "エラーが発生しました" },
    });
  });

  it("should throw error when response body is null", async () => {
    const response = new Response(null);

    await expect(async () => {
      for await (const _ of readSSEStream(response)) {
        // noop
      }
    }).rejects.toThrow("Response body is null");
  });
});
