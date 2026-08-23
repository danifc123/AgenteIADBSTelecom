/**
 * Botões de resposta rápida (ex: Sim/Não do diagnóstico de Suporte) — camada components.
 */

import React from 'react';
import { StyleSheet, TouchableOpacity, Text, View } from 'react-native';

import { colors } from '../theme/colors';
import { fontFamily } from '../theme/typography';

// #region Componente

export function QuickReplyButtons({
  options,
  onSelect,
}: {
  options: string[];
  onSelect: (option: string) => void;
}) {
  return (
    <View style={styles.container}>
      {options.map((option) => (
        <TouchableOpacity key={option} style={styles.button} onPress={() => onSelect(option)}>
          <Text style={styles.text}>{option}</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

// #endregion

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    borderColor: colors.laranjaVibrante,
    borderRadius: 23,
    borderWidth: 1.5,
    height: 46,
    justifyContent: 'center',
  },
  container: {
    gap: 9,
    marginLeft: 32,
    marginTop: 2,
  },
  text: {
    color: colors.laranjaVibrante,
    fontFamily,
    fontSize: 13.5,
    fontWeight: '700',
  },
});
