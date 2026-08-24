/**
 * Tela de configuração do servidor: permite apontar o app para qualquer
 * backend em tempo de execução, sem precisar gerar um novo instalador —
 * camada screens.
 */

import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Button, HelperText, IconButton, TextInput } from 'react-native-paper';

import { DbsLogoIcon } from '../components/DbsLogo';
import { getApiBaseUrl, getBuiltInApiBaseUrl, setApiBaseUrl } from '../services/apiClient';
import type { ScreenProps } from '../navigation/AppNavigator';
import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';

// #region Tela

type TestStatus = { kind: 'idle' } | { kind: 'testing' } | { kind: 'success' } | { kind: 'error'; message: string };

export function ServerConfigScreen({ navigation }: ScreenProps<'ServerConfig'>) {
  const [url, setUrl] = useState(getApiBaseUrl());
  const [testStatus, setTestStatus] = useState<TestStatus>({ kind: 'idle' });
  const [isSaving, setIsSaving] = useState(false);

  /** Testa o endereço digitado (ainda não salvo) fazendo uma requisição direta, sem afetar a URL em uso pelo resto do app. */
  const handleTest = async () => {
    setTestStatus({ kind: 'testing' });
    try {
      const response = await fetch(`${withoutTrailingSlash(url.trim())}/health`);
      if (!response.ok) {
        setTestStatus({ kind: 'error', message: `O servidor respondeu, mas com erro (${response.status}).` });
        return;
      }
      setTestStatus({ kind: 'success' });
    } catch {
      setTestStatus({
        kind: 'error',
        message: 'Não conseguimos alcançar esse endereço. Confira o IP, a porta e se o celular está na mesma rede do backend.',
      });
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await setApiBaseUrl(withoutTrailingSlash(url.trim()));
      navigation.goBack();
    } finally {
      setIsSaving(false);
    }
  };

  const handleRestoreDefault = () => {
    setUrl(getBuiltInApiBaseUrl());
    setTestStatus({ kind: 'idle' });
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <IconButton icon="arrow-left" onPress={() => navigation.goBack()} />
          <DbsLogoIcon size={30} />
        </View>

        <View style={styles.intro}>
          <Text style={styles.title}>Configurar servidor</Text>
          <Text style={styles.subtitle}>
            Informe o endereço do backend (ex.: http://192.168.0.10:8000). Essa configuração fica
            salva neste aparelho — não precisa gerar um novo instalador pra apontar pra outro backend.
          </Text>
        </View>

        <View style={styles.form}>
          <TextInput
            mode="outlined"
            label="URL do backend"
            placeholder="http://192.168.0.10:8000"
            value={url}
            onChangeText={(text) => {
              setUrl(text);
              setTestStatus({ kind: 'idle' });
            }}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            outlineColor={colors.border}
            activeOutlineColor={colors.laranjaVibrante}
          />

          {testStatus.kind === 'success' ? (
            <HelperText type="info" style={styles.successText}>
              Conexão OK — o backend respondeu.
            </HelperText>
          ) : null}
          {testStatus.kind === 'error' ? <HelperText type="error">{testStatus.message}</HelperText> : null}

          <Button
            mode="outlined"
            textColor={colors.laranjaVibrante}
            loading={testStatus.kind === 'testing'}
            disabled={!url.trim() || testStatus.kind === 'testing'}
            onPress={handleTest}
          >
            Testar conexão
          </Button>

          <Button mode="text" textColor={colors.textMuted} onPress={handleRestoreDefault}>
            Restaurar endereço padrão
          </Button>
        </View>

        <View style={styles.footer}>
          <Button
            mode="contained"
            buttonColor={colors.laranjaVibrante}
            textColor={colors.white}
            loading={isSaving}
            disabled={!url.trim() || isSaving}
            contentStyle={styles.saveButtonContent}
            style={styles.saveButton}
            onPress={handleSave}
          >
            Salvar
          </Button>
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

// #endregion

// #region Auxiliares (ordem alfabética)

/** Remove uma barra final da URL, se houver, pra evitar `//` na concatenação com o path. Retorna a URL normalizada. */
function withoutTrailingSlash(value: string): string {
  return value.endsWith('/') ? value.slice(0, -1) : value;
}

// #endregion

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.white,
    flex: 1,
  },
  footer: {
    paddingBottom: 24,
    paddingHorizontal: 28,
  },
  form: {
    gap: 10,
    paddingHorizontal: 28,
    paddingTop: 12,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingHorizontal: 12,
    paddingTop: 8,
  },
  intro: {
    gap: 10,
    paddingHorizontal: 28,
    paddingTop: 28,
  },
  saveButton: {
    borderRadius: 28,
  },
  saveButtonContent: {
    height: 56,
  },
  subtitle: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 14.5,
    lineHeight: 21,
  },
  successText: {
    color: colors.online,
  },
  title: {
    color: colors.cinzaEscuro,
    fontFamily,
    fontSize: 26,
    fontWeight: '800',
  },
});
