import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { api } from '@/services/api';

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe('api.sendChatMessageStream', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('maps backend SSE chunk/final frames to normalized stream events', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      body: makeStream([
        'event: chunk\ndata: {"delta":"Hello "}\n\n',
        'event: chunk\ndata: {"delta":"world"}\n\n',
        'event: final\ndata: {"message":"Hello world","source_refs":[{"document_id":"doc-1","document_title":"Doc 1"}]}\n\n',
      ]),
    });

    const onEvent = vi.fn();
    await api.sendChatMessageStream('session-1', { message: 'hi' }, { onEvent });

    expect(onEvent).toHaveBeenNthCalledWith(1, { type: 'chunk', content: 'Hello ' });
    expect(onEvent).toHaveBeenNthCalledWith(2, { type: 'chunk', content: 'world' });
    expect(onEvent).toHaveBeenNthCalledWith(3, {
      type: 'final',
      content: 'Hello world',
      source_refs: [{ document_id: 'doc-1', document_title: 'Doc 1' }],
    });
  });

  it('keeps support for already-normalized stream payloads and ignores malformed frames', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      body: makeStream([
        'data: {"type":"chunk","content":"legacy chunk"}\n\n',
        'event: chunk\ndata: not json\n\n',
        'data: {"type":"final","content":"legacy final","source_refs":[]}\n\n',
      ]),
    });

    const onEvent = vi.fn();
    await api.sendChatMessageStream('session-2', { message: 'hello' }, { onEvent });

    expect(onEvent).toHaveBeenCalledTimes(2);
    expect(onEvent).toHaveBeenNthCalledWith(1, { type: 'chunk', content: 'legacy chunk' });
    expect(onEvent).toHaveBeenNthCalledWith(2, { type: 'final', content: 'legacy final', source_refs: [] });
  });
});
