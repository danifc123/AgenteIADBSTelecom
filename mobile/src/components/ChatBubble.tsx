/**
 * Balão de mensagem do chat — camada components.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';
import type { ChatBubbleMessage } from '../domain/types';

// #region Componente

export function ChatBubble({ message }: { message: ChatBubbleMessage }) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.row, isUser && styles.rowUser]}>
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAssistant]}>
        <Text style={[styles.text, isUser && styles.textUser]}>{renderWithBold(message.text)}</Text>
      </View>
    </View>
  );
}

// #endregion

// #region Helpers

/**
 * Interpreta `**trecho**` como negrito. O modelo de IA às vezes usa essa
 * marcação apesar da instrução para não usar Markdown — em vez de mostrar
 * os asteriscos literalmente (poluindo a mensagem), renderiza como negrito
 * de verdade. Retorna os nós de texto prontos para o `<Text>` pai.
 */
function renderWithBold(text: string): React.ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, index) => {
    const boldMatch = part.match(/^\*\*([^*]+)\*\*$/);
    if (boldMatch) {
      return (
        <Text key={index} style={styles.textBold}>
          {boldMatch[1]}
        </Text>
      );
    }
    return part;
  });
}

// #endregion

const styles = StyleSheet.create({
  bubble: {
    borderRadius: 16,
    maxWidth: '78%',
    paddingHorizontal: 15,
    paddingVertical: 12,
  },
  bubbleAssistant: {
    backgroundColor: colors.white,
    borderBottomLeftRadius: 4,
    borderColor: colors.border,
    borderWidth: 1,
  },
  bubbleUser: {
    backgroundColor: colors.laranjaVibrante,
    borderBottomRightRadius: 4,
  },
  row: {
    flexDirection: 'row',
    marginVertical: 4,
  },
  rowUser: {
    justifyContent: 'flex-end',
  },
  text: {
    color: colors.cinzaEscuro,
    fontFamily,
    fontSize: 14,
    lineHeight: 20,
  },
  textBold: {
    fontWeight: '700',
  },
  textUser: {
    color: colors.white,
  },
});
