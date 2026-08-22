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

  const handleContactChange = (text: string) => {
    const digits = text.replace(/\D/g, '').slice(0, 14);
    setContact(maskContact(digits));
  };

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
            onChangeText={handleContactChange}
            keyboardType="phone-pad"
            maxLength={18}
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

// #region Máscara (ordem alfabética)

/**
 * Formata os dígitos digitados como telefone, CPF ou CNPJ, conforme a
 * quantidade — o campo aceita os três, e o backend tenta telefone e
 * depois CPF/CNPJ na identificação. Retorna o texto já mascarado.
 */
function maskContact(digits: string): string {
  if (digits.length > 11) {
    return maskCnpj(digits);
  }
  // 11 dígitos é ambíguo entre celular e CPF — celular sempre começa o
  // número local (após o DDD) com 9, então usamos isso pra decidir.
  if (digits.length === 11 && digits[2] !== '9') {
    return maskCpf(digits);
  }
  return maskPhone(digits);
}

/** Aplica a máscara XX.XXX.XXX/XXXX-XX progressivamente. Retorna o texto mascarado. */
function maskCnpj(digits: string): string {
  let result = digits.slice(0, 2);
  if (digits.length > 2) result += `.${digits.slice(2, 5)}`;
  if (digits.length > 5) result += `.${digits.slice(5, 8)}`;
  if (digits.length > 8) result += `/${digits.slice(8, 12)}`;
  if (digits.length > 12) result += `-${digits.slice(12, 14)}`;
  return result;
}

/** Aplica a máscara XXX.XXX.XXX-XX progressivamente. Retorna o texto mascarado. */
function maskCpf(digits: string): string {
  let result = digits.slice(0, 3);
  if (digits.length > 3) result += `.${digits.slice(3, 6)}`;
  if (digits.length > 6) result += `.${digits.slice(6, 9)}`;
  if (digits.length > 9) result += `-${digits.slice(9, 11)}`;
  return result;
}

/** Aplica a máscara (XX) XXXXX-XXXX (celular) ou (XX) XXXX-XXXX (fixo) progressivamente. Retorna o texto mascarado. */
function maskPhone(digits: string): string {
  if (digits.length === 0) return '';
  const ddd = digits.slice(0, 2);
  if (digits.length <= 2) return `(${ddd}`;

  const rest = digits.slice(2);
  const isMobile = rest.length > 8;
  const prefixLength = isMobile ? 5 : 4;
  const prefix = rest.slice(0, prefixLength);
  const suffix = rest.slice(prefixLength);

  return suffix ? `(${ddd}) ${prefix}-${suffix}` : `(${ddd}) ${prefix}`;
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
