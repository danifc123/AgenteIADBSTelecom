/**
 * Tela de identificação: telefone/CPF do cliente -> POST /api/identify — camada screens.
 */

import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Button, HelperText, IconButton, TextInput } from 'react-native-paper';

import { DbsLogoIcon } from '../components/DbsLogo';
import { useSession } from '../context/SessionContext';
import { identifyCustomer } from '../services/identificationService';
import type { ScreenProps } from '../navigation/AppNavigator';
import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';

// #region Tela

export function IdentificationScreen({ navigation }: ScreenProps<'Identification'>) {
  const { startSession } = useSession();
  const [contact, setContact] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleContinue = async () => {
    if (!contact.trim()) {
      setErrorMessage('Informe seu telefone ou CPF para continuar.');
      return;
    }

    setErrorMessage(null);
    setIsLoading(true);
    try {
      const result = await identifyCustomer(contact.trim());
      if (!result.success) {
        setErrorMessage(result.message);
        return;
      }
      startSession(result.sessionId, result.customer, result.greetingMessage);
      navigation.navigate('Chat');
    } catch {
      setErrorMessage('Não conseguimos falar com o servidor agora. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <IconButton icon="arrow-left" onPress={() => navigation.goBack()} />
          <DbsLogoIcon size={30} />
        </View>

        <View style={styles.intro}>
          <Text style={styles.title}>Vamos te identificar</Text>
          <Text style={styles.subtitle}>
            Informe seu telefone ou CPF cadastrado para começarmos o atendimento.
          </Text>
        </View>

        <View style={styles.form}>
          <TextInput
            mode="outlined"
            label="Telefone ou CPF"
            placeholder="(64) 99999-9999"
            value={contact}
            onChangeText={setContact}
            keyboardType="phone-pad"
            outlineColor={colors.border}
            activeOutlineColor={colors.laranjaVibrante}
          />
          {errorMessage ? <HelperText type="error">{errorMessage}</HelperText> : null}
          <Text style={styles.privacyNote}>
            Seus dados são usados apenas para localizar seu cadastro na DBS TELECOM.
          </Text>
        </View>

        <View style={styles.footer}>
          <Button
            mode="contained"
            buttonColor={colors.laranjaVibrante}
            textColor={colors.white}
            loading={isLoading}
            disabled={isLoading}
            contentStyle={styles.continueButtonContent}
            style={styles.continueButton}
            onPress={handleContinue}
          >
            Continuar
          </Button>
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

// #endregion

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.white,
    flex: 1,
  },
  continueButton: {
    borderRadius: 28,
  },
  continueButtonContent: {
    height: 56,
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
  privacyNote: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 12,
    lineHeight: 17,
  },
  subtitle: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 14.5,
    lineHeight: 21,
  },
  title: {
    color: colors.cinzaEscuro,
    fontFamily,
    fontSize: 26,
    fontWeight: '800',
  },
});
