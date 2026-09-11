// src/lib/api.ts

// Configurações base
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000';
const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL || window.location.origin;

// Formato de erro padronizado do backend[cite: 1]
export interface ApiError {
  code: string;
  message: string;
  request_id: string;
}

async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  
  // O corpo das requisições e respostas usam JSON[cite: 1]
  if (!headers.has('Content-Type') && options.method !== 'GET') {
    headers.set('Content-Type', 'application/json');
  }

  // Toda mutação exige o cabeçalho Origin exatamente igual ao FRONTEND_URL configurado[cite: 1]
  const isMutation = options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase());
  if (isMutation) {
    headers.set('Origin', FRONTEND_URL);
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    // Clientes web devem enviar credenciais para manter a sessão if_arbitra_session[cite: 1]
    credentials: 'include', 
  });

  if (!response.ok) {
    let errorData: ApiError;
    try {
      errorData = await response.json();
    } catch {
      // Captura o request_id caso o parsing falhe, conforme contrato[cite: 1]
      errorData = {
        code: 'UNKNOWN_ERROR',
        message: 'Ocorreu um erro inesperado de comunicação.',
        request_id: response.headers.get('X-Request-ID') || 'unknown',
      };
    }
    throw errorData; 
  }

  // Tratamento específico para rotas sem corpo (ex: 204 No Content do logout)[cite: 1]
  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string, config?: RequestInit) => 
    fetchApi<T>(endpoint, { ...config, method: 'GET' }),
    
  post: <T>(endpoint: string, body?: any, config?: RequestInit) => 
    fetchApi<T>(endpoint, { ...config, method: 'POST', body: JSON.stringify(body) }),
    
  put: <T>(endpoint: string, body: any, config?: RequestInit) => 
    fetchApi<T>(endpoint, { ...config, method: 'PUT', body: JSON.stringify(body) }),
    
  delete: <T>(endpoint: string, config?: RequestInit) => 
    fetchApi<T>(endpoint, { ...config, method: 'DELETE' }),
};