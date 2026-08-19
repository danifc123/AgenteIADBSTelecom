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
        <Text style={[styles.text, isUser && styles.textUser]}>{message.text}</Text>
      </View>
    </View>
  );
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
  textUser: {
    color: colors.white,
  },
});
