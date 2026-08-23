/**
 * Indicador de "digitando..." exibido enquanto aguarda a resposta do assistente — camada components.
 */

import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, View } from 'react-native';

import { colors } from '../theme/colors';

// #region Componente

export function TypingIndicator() {
  const dotOpacity = useRef([new Animated.Value(0.3), new Animated.Value(0.3), new Animated.Value(0.3)]).current;

  // Lifecycle: inicia a animação de pulsação ao montar, e limpa ao desmontar.
  useEffect(() => {
    const animations = dotOpacity.map((value, index) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(index * 150),
          Animated.timing(value, { duration: 350, toValue: 1, useNativeDriver: true }),
          Animated.timing(value, { duration: 350, toValue: 0.3, useNativeDriver: true }),
        ]),
      ),
    );
    animations.forEach((animation) => animation.start());
    return () => animations.forEach((animation) => animation.stop());
  }, [dotOpacity]);

  return (
    <View style={styles.container}>
      {dotOpacity.map((opacity, index) => (
        <Animated.View key={index} style={[styles.dot, { opacity }]} />
      ))}
    </View>
  );
}

// #endregion

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    backgroundColor: colors.white,
    borderColor: colors.border,
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 4,
    paddingHorizontal: 15,
    paddingVertical: 14,
  },
  dot: {
    backgroundColor: colors.textMuted,
    borderRadius: 3,
    height: 6,
    width: 6,
  },
});
