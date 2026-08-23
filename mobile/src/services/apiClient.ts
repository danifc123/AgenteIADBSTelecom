/**
 * Cliente HTTP para o backend da DBS TELECOM — camada services.
 *
 * Regra de negócio de segurança: este é o ÚNICO arquivo do app mobile que
 * conhece a URL do backend. Nenhum outro arquivo sob `mobile/` deve montar
 * uma URL ou falar HTTP diretamente — e em especial, nenhum arquivo aqui
 * conhece a URL/token da IXC, que fica só no backend.
 *
 * A URL padrão vem gravada no app em tempo de build (`EXPO_PUBLIC_API_URL`),
 * mas pode ser sobrescrita em tempo de execução (tela "Configurar servidor")
 * e persiste no aparelho via AsyncStorage — assim o mesmo instalador (.apk)
 * funciona contra qualquer backend, sem precisar gerar um build novo.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

const BUILT_IN_API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';
const STORAGE_KEY = 'dbs.apiBaseUrl';

let apiBaseUrl = BUILT_IN_API_URL;

// #region Configuração da URL do backend (ordem alfabética)

/** URL do backend gravada em tempo de build, usada como padrão/restauração. Retorna a URL. */
export function getBuiltInApiBaseUrl(): string {
  return BUILT_IN_API_URL;
}

/** URL do backend em uso agora (padrão de build ou sobrescrita salva). Retorna a URL. */
export function getApiBaseUrl(): string {
  return apiBaseUrl;
}

/** Carrega, se existir, a URL do backend salva no aparelho e a aplica. Não retorna valor. */
export async function loadStoredApiBaseUrl(): Promise<void> {
  const stored = await AsyncStorage.getItem(STORAGE_KEY);
  if (stored) {
    apiBaseUrl = stored;
  }
}

/** Define e persiste no aparelho a URL do backend a ser usada. Não retorna valor. */
export async function setApiBaseUrl(url: string): Promise<void> {
  apiBaseUrl = url;
  await AsyncStorage.setItem(STORAGE_KEY, url);
}

// #endregion

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
  const response = await fetch(`${apiBaseUrl}${path}`);
  return parseResponse<T>(response);
}

/** Faz uma requisição POST no backend com corpo JSON. Retorna o corpo da resposta já parseado. */
export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
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
