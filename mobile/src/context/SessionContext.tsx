/**
 * Contexto de sessão do atendimento — camada context.
 *
 * Regra de negócio: guarda o `sessionId` e o `Customer` identificado
 * durante a navegação entre telas (Identification -> Chat), sem precisar
 * de um gerenciador de estado global mais pesado para o MVP.
 */

import React, { createContext, useContext, useMemo, useState } from 'react';

import type { Customer } from '../domain/types';

// #region Tipos

interface SessionContextValue {
  customer: Customer | null;
  endSession: () => void;
  greetingMessage: string | null;
  sessionId: string | null;
  startSession: (sessionId: string, customer: Customer, greetingMessage: string) => void;
}

// #endregion

const SessionContext = createContext<SessionContextValue | undefined>(undefined);

// #region Provider

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [greetingMessage, setGreetingMessage] = useState<string | null>(null);

  const startSession = (newSessionId: string, newCustomer: Customer, newGreetingMessage: string) => {
    setSessionId(newSessionId);
    setCustomer(newCustomer);
    setGreetingMessage(newGreetingMessage);
  };

  /** Encerra o atendimento atual, limpando a sessão (cliente, saudação e session_id). Não retorna valor. */
  const endSession = () => {
    setSessionId(null);
    setCustomer(null);
    setGreetingMessage(null);
  };

  const value = useMemo(
    () => ({ customer, endSession, greetingMessage, sessionId, startSession }),
    [customer, greetingMessage, sessionId],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

// #endregion

// #region Hook

/** Lê o contexto de sessão do atendimento. Retorna `SessionContextValue`, lançando erro se usado fora do `SessionProvider`. */
export function useSession(): SessionContextValue {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession precisa ser usado dentro de um SessionProvider.');
  }
  return context;
}

// #endregion
