const API_URL = import.meta.env.VITE_API_URL;
const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL;

async function fetchApi(endpoint, options = {}) {
  const headers = new Headers(options.headers);

  if (!headers.has('Content-Type') && options.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }

  const isMutation =
    options.method &&
    ['POST', 'PUT', 'PATCH', 'DELETE'].includes(
      options.method.toUpperCase()
    );

  if (isMutation) {
    headers.set('Origin', FRONTEND_URL);
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include',
  });

  if (!response.ok) {
    let errorData;

    try {
      errorData = await response.json();
    } catch {
      errorData = {
        code: 'UNKNOWN_ERROR',
        message: 'Ocorreu um erro inesperado de comunicação.',
        request_id:
          response.headers.get('X-Request-ID') || 'unknown',
      };
    }

    throw errorData;
  }

  if (response.status === 204) {
    return {};
  }

  return response.json();
}

export const api = {
  get: (endpoint, config) =>
    fetchApi(endpoint, {
      ...config,
      method: 'GET',
    }),

  post: (endpoint, body, config) =>
    fetchApi(endpoint, {
      ...config,
      method: 'POST',
      body: JSON.stringify(body),
    }),

  put: (endpoint, body, config) =>
    fetchApi(endpoint, {
      ...config,
      method: 'PUT',
      body: JSON.stringify(body),
    }),

  delete: (endpoint, config) =>
    fetchApi(endpoint, {
      ...config,
      method: 'DELETE',
    }),
};