/**
 * Tipos de domínio do app — espelham os modelos do backend (camada domain).
 *
 * Regra de negócio: este arquivo não importa nada de `services/` ou
 * `screens/` — só descreve os conceitos do negócio, para as outras camadas
 * falarem a mesma língua.
 */

// #region Enums

export type Department = 'Comercial' | 'Suporte' | 'Financeiro';

export type SupportStage =
  | 'ask_multiple_devices'
  | 'ask_check_cables'
  | 'suggest_restart'
  | 'ask_resolved'
  | 'closed_resolved'
  | 'escalate_n1'
  | 'escalate_n2_visit';

// #endregion

// #region Modelos

export interface Customer {
  id: string;
  name: string;
  phone?: string | null;
  cpfCnpj?: string | null;
  planName?: string | null;
  status?: string | null;
}

/** Uma mensagem exibida na tela de chat (distinta do histórico interno do backend). */
export interface ChatBubbleMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
}

// #endregion
