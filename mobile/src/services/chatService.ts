/**
 * Serviço de chat — camada services.
 */

import { apiPost } from './apiClient';
import type { Department, SupportStage } from '../domain/types';

// #region Formato wire (espelha o backend)

interface ChatApiResponse {
  reply: string;
  department?: Department | null;
  support_stage?: SupportStage | null;
  quick_replies?: string[] | null;
}

// #endregion

// #region Resultado do domínio

export interface ChatTurnResult {
  reply: string;
  department: Department | null;
  supportStage: SupportStage | null;
  quickReplies: string[] | null;
}

// #endregion

// #region Serviço

/** Envia uma mensagem do cliente para o backend e recebe a resposta do assistente. Retorna `ChatTurnResult`. */
export async function sendChatMessage(sessionId: string, message: string): Promise<ChatTurnResult> {
  const response = await apiPost<ChatApiResponse>('/api/chat', { session_id: sessionId, message });

  return {
    department: response.department ?? null,
    quickReplies: response.quick_replies ?? null,
    reply: response.reply,
    supportStage: response.support_stage ?? null,
  };
}

// #endregion
