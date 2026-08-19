/**
 * Tela inicial: branding da DBS TELECOM + CTA para iniciar o atendimento — camada screens.
 */

import React from 'react';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { Button } from 'react-native-paper';

import { DbsLogoFull } from '../components/DbsLogo';
import type { ScreenProps } from '../navigation/AppNavigator';
import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';

// #region Tela

export function HomeScreen({ navigation }: ScreenProps<'Home'>) {
  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.decorTop} />
      <View style={styles.decorBottom} />

      <View style={styles.content}>
        <View style={styles.brand}>
          <DbsLogoFull width={220} />
          <Text style={styles.subtitle}>Provedora de internet em Rio Verde - GO</Text>
        </View>

        <View style={styles.tagline}>
          <Text style={styles.taglineText}>A Internet que você merece!</Text>
        </View>

        <View style={styles.ctaArea}>
          <Button
            mode="contained"
            buttonColor={colors.laranjaVibrante}
            textColor={colors.white}
            contentStyle={styles.ctaButtonContent}
            style={styles.ctaButton}
            onPress={() => navigation.navigate('Identification')}
          >
            Falar com a DBS
          </Button>
          <Text style={styles.departmentsHint}>Comercial  •  Suporte  •  Financeiro</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

// #endregion

const styles = StyleSheet.create({
  brand: {
    alignItems: 'center',
    gap: 24,
  },
  container: {
    backgroundColor: colors.white,
    flex: 1,
  },
  content: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'space-between',
    paddingBottom: 36,
    paddingHorizontal: 28,
    paddingTop: 90,
  },
  ctaArea: {
    alignItems: 'center',
    gap: 16,
    width: '100%',
  },
  ctaButton: {
    borderRadius: 28,
    width: '100%',
  },
  ctaButtonContent: {
    height: 56,
  },
  decorBottom: {
    backgroundColor: colors.laranjaVibrante,
    borderRadius: 115,
    bottom: 160,
    height: 230,
    left: -100,
    opacity: 0.07,
    position: 'absolute',
    width: 230,
  },
  decorTop: {
    backgroundColor: colors.laranjaVibrante,
    borderRadius: 140,
    height: 280,
    opacity: 0.09,
    position: 'absolute',
    right: -110,
    top: -90,
    width: 280,
  },
  departmentsHint: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.3,
  },
  subtitle: {
    color: colors.textMuted,
    fontFamily,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  tagline: {
    backgroundColor: colors.cinzaEscuro,
    borderRadius: 24,
    paddingHorizontal: 22,
    paddingVertical: 11,
  },
  taglineText: {
    color: colors.white,
    fontFamily,
    fontSize: 14,
    fontWeight: '700',
  },
});
