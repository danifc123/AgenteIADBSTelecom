/**
 * Selo (chip) indicando o departamento atual do atendimento — camada components.
 */

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { colors, departmentColors } from '../theme/colors';
import { fontFamily } from '../theme/typography';
import type { Department } from '../domain/types';

// #region Componente

export function DepartmentBadge({ department }: { department: Department }) {
  return (
    <View style={[styles.badge, { backgroundColor: departmentColors[department] }]}>
      <Text style={styles.text}>{department}</Text>
    </View>
  );
}

// #endregion

const styles = StyleSheet.create({
  badge: {
    borderRadius: 14,
    paddingHorizontal: 13,
    paddingVertical: 7,
  },
  text: {
    color: colors.white,
    fontFamily,
    fontSize: 11.5,
    fontWeight: '700',
  },
});
