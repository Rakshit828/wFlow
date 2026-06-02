/** Base URL for FastAPI — use Vite proxy in dev (empty string) or full origin in prod */
export const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? '';

type RequestOptions = RequestInit & {
  json?: unknown;
};

/**
 * Fetch wrapper: sends cookies (JWT in httpOnly cookies) and JSON bodies when needed.
 */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { json, headers: initHeaders, ...rest } = options;
  const headers = new Headers(initHeaders);

  if (json !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    ...rest,
    headers,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (!res.ok) {
    let message = `Request failed: ${res.status}`;
    try {
      const errBody = await res.json();
      if (errBody?.message) message = errBody.message;
    } catch {
      /* ignore */
    }
    throw new Error(message);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json() as Promise<T>;
}
