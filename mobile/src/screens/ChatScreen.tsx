/**
 * Tela principal de chat: mensagens, badge de departamento e quick-replies — camada screens.
 */

import React, { useEffect, useRef, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { IconButton, TextInput } from 'react-native-paper';

import { ChatBubble } from '../components/ChatBubble';
import { DbsLogoIcon } from '../components/DbsLogo';
import { DepartmentBadge } from '../components/DepartmentBadge';
import { QuickReplyButtons } from '../components/QuickReplyButtons';
import { TypingIndicator } from '../components/TypingIndicator';
import { useSession } from '../context/SessionContext';
import { sendChatMessage } from '../services/chatService';
import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';
import type { ChatBubbleMessage, Department } from '../domain/types';

// #region Tela

export function ChatScreen() {
  const { customer, greetingMessage, sessionId } = useSession();

  const [messages, setMessages] = useState<ChatBubbleMessage[]>([]);
  const [department, setDepartment] = useState<Department | null>(null);
  const [quickReplies, setQuickReplies] = useState<string[] | null>(null);
  const [draft, setDraft] = useState('');
  const [isSending, setIsSending] = useState(false);

  const nextMessageId = useRef(0);
  const listRef = useRef<FlatList<ChatBubbleMessage>>(null);

  // Lifecycle: assim que a tela monta, exibe a saudação personalizada já
  // recebida na identificação — sem round-trip extra ao backend.
  useEffect(() => {
    if (greetingMessage) {
      setMessages([createMessage('assistant', greetingMessage, nextMessageId)]);
    }
  }, [greetingMessage]);

  const handleQuickReply = (option: string) => {
    setQuickReplies(null);
    void sendMessage(option);
  };

  const handleSend = () => {
    const text = draft.trim();
    if (!text) return;
    setDraft('');
    void sendMessage(text);
  };

  /** Envia a mensagem ao backend e atualiza a lista de mensagens, departamento e quick-replies. Não retorna valor. */
  const sendMessage = async (text: string) => {
    if (!sessionId) return;

    setMessages((current) => [...current, createMessage('user', text, nextMessageId)]);
    setIsSending(true);

    try {
      const result = await sendChatMessage(sessionId, text);
      setMessages((current) => [...current, createMessage('assistant', result.reply, nextMessageId)]);
      setDepartment(result.department);
      setQuickReplies(result.quickReplies);
    } catch {
      setMessages((current) => [
        ...current,
        createMessage('assistant', 'Não consegui responder agora. Pode tentar de novo?', nextMessageId),
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <IconButton icon="arrow-left" size={18} />
            <DbsLogoIcon size={34} />
            <View>
              <Text style={styles.headerTitle}>DBS TELECOM</Text>
              <View style={styles.headerStatusRow}>
                <View style={styles.onlineDot} />
                <Text style={styles.headerStatus}>{customer ? `Atendendo ${customer.name}` : 'Assistente virtual'}</Text>
              </View>
            </View>
          </View>
          {department ? <DepartmentBadge department={department} /> : null}
        </View>

        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => <ChatBubble message={item} />}
          contentContainerStyle={styles.listContent}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          ListFooterComponent={
            <>
              {isSending ? (
                <View style={styles.typingRow}>
                  <TypingIndicator />
                </View>
              ) : null}
              {quickReplies && !isSending ? (
                <QuickReplyButtons options={quickReplies} onSelect={handleQuickReply} />
              ) : null}
            </>
          }
        />

        <View style={styles.inputRow}>
          <TextInput
            mode="flat"
            placeholder="Digite sua mensagem..."
            value={draft}
            onChangeText={setDraft}
            style={styles.textInput}
            underlineColor="transparent"
            activeUnderlineColor="transparent"
            dense
          />
          <IconButton
            icon="send"
            mode="contained"
            containerColor={colors.laranjaVibrante}
            iconColor={colors.white}
            onPress={handleSend}
            disabled={isSending}
          />
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

// #endregion

// #region Helpers

/** Cria uma mensagem de chat com id único incremental. Retorna o `ChatBubbleMessage`. */
function createMessage(role: ChatBubbleMessage['role'], text: string, counter: React.MutableRefObject<number>): ChatBubbleMessage {
  counter.current += 1;
  return { id: `${role}-${counter.current}`, role, text };
}

// #endregion

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.background,
    flex: 1,
  },
  header: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  headerLeft: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  headerStatus: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 11.5,
    fontWeight: '600',
  },
  headerStatusRow: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 5,
    marginTop: 2,
  },
  headerTitle: {
    color: colors.cinzaEscuro,
    fontFamily,
    fontSize: 14.5,
    fontWeight: '800',
  },
  inputRow: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: 'row',
    paddingHorizontal: 8,
    paddingVertical: 8,
  },
  listContent: {
    gap: 4,
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  onlineDot: {
    backgroundColor: colors.online,
    borderRadius: 3,
    height: 6,
    width: 6,
  },
  textInput: {
    backgroundColor: colors.inputBackground,
    borderRadius: 24,
    flex: 1,
    fontFamily,
    fontSize: 13.5,
    marginRight: 6,
  },
  typingRow: {
    alignItems: 'flex-start',
    marginTop: 4,
  },
});
