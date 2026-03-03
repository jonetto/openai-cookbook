import { useCallback, useRef } from 'react';
import { getApiBase } from '../apiConfig';

/**
 * Hook for streaming SSE events from a POST endpoint.
 *
 * Uses fetch() + ReadableStream instead of EventSource (which only supports GET).
 * Parses SSE-formatted text: "event: <type>\ndata: <json>\n\n"
 */
export function useSSE(dispatch) {
  const abortRef = useRef(null);

  const startImport = useCallback(async (cuit, password, fechaDesde, fechaHasta) => {
    // Cancel any previous stream
    if (abortRef.current) {
      abortRef.current.abort();
    }

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch(`${getApiBase()}/api/onboarding/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cuit,
          password,
          fecha_desde: fechaDesde || '',
          fecha_hasta: fechaHasta || '',
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        dispatch({
          type: 'ERROR',
          payload: { stage: 'connection', message: `HTTP ${response.status}` },
        });
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Parse complete SSE events (separated by double newline)
        const events = buffer.split('\n\n');
        buffer = events.pop(); // Keep incomplete event in buffer

        for (const rawEvent of events) {
          if (!rawEvent.trim()) continue;
          const eventMatch = rawEvent.match(/^event: (.+)$/m);
          const dataMatch = rawEvent.match(/^data: (.+)$/m);
          if (eventMatch && dataMatch) {
            try {
              const eventType = eventMatch[1];
              const data = JSON.parse(dataMatch[1]);
              dispatch({ type: eventType, payload: data });
            } catch {
              // Skip malformed events
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        dispatch({
          type: 'ERROR',
          payload: { stage: 'connection', message: err.message },
        });
      }
    }
  }, [dispatch]);

  const cancelImport = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
  }, []);

  return { startImport, cancelImport };
}
