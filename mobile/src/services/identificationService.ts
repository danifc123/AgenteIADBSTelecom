/**
 * Serviço de identificação do cliente — camada services.
 *
 * Regra de negócio: converte o formato "wire" (snake_case, igual ao
 * backend) para os tipos de domínio (camelCase) usados no resto do app —
 * telas nunca leem o formato snake_case diretamente.
 */

import { apiPost } from './apiClient';
import type { Customer } from '../domain/types';

// #region Formato wire (espelha o backend)

interface ApiCustomer {
  id: string;
  name: string;
  phone?: string | null;
  cpf_cnpj?: string | null;
  plan_name?: string | null;
  status?: string | null;
}

interface IdentifyApiResponse {
  success: boolean;
  session_id?: string | null;
  customer?: ApiCustomer | null;
  greeting_message?: string | null;
  message?: string | null;
}

// #endregion

// #region Resultado do domínio

export type IdentifyResult =
  | { success: true; sessionId: string; customer: Customer; greetingMessage: string }
  | { success: false; message: string };

// #endregion

// #region Serviço

/** Identifica o cliente pelo telefone ou CPF informado. Retorna `IdentifyResult` (sucesso com sessão, ou falha com mensagem). */
export async function identifyCustomer(contact: string): Promise<IdentifyResult> {
  const response = await apiPost<IdentifyApiResponse>('/api/identify', { contact });

  if (!response.success || !response.customer || !response.session_id) {
    return { message: response.message ?? 'Não encontramos seu cadastro.', success: false };
  }

  return {
    customer: mapCustomer(response.customer),
    greetingMessage: response.greeting_message ?? `Olá, ${response.customer.name}!`,
    sessionId: response.session_id,
    success: true,
  };
}

/** Converte o cliente no formato wire (snake_case) para o tipo de domínio (camelCase). Retorna o `Customer`. */
function mapCustomer(raw: ApiCustomer): Customer {
  return {
    cpfCnpj: raw.cpf_cnpj,
    id: raw.id,
    name: raw.name,
    phone: raw.phone,
    planName: raw.plan_name,
    status: raw.status,
  };
}

// #endregion
