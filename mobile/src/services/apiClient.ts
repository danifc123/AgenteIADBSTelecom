/**
 * Cliente HTTP para o backend da DBS TELECOM — camada services.
 *
 * Regra de negócio de segurança: este é o ÚNICO arquivo do app mobile que
 * conhece a URL do backend. Nenhum outro arquivo sob `mobile/` deve montar
 * uma URL ou falar HTTP diretamente — e em especial, nenhum arquivo aqui
 * conhece a URL/token da IXC, que fica só no backend.
 */

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

// #region Erros

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

// #endregion

// #region Requisições (ordem alfabética)

/** Faz uma requisição GET no backend e retorna o corpo já parseado como JSON. */
export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return parseResponse<T>(response);
}

/** Faz uma requisição POST no backend com corpo JSON. Retorna o corpo da resposta já parseado. */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    body: JSON.stringify(body),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  return parseResponse<T>(response);
}

/** Valida o status HTTP e parseia o corpo como JSON, lançando `ApiError` em caso de falha. Retorna o corpo tipado. */
async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(`Falha na comunicação com o servidor (${response.status})`, response.status);
  }
  return (await response.json()) as T;
}

// #endregion
