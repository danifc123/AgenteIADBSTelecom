/**
 * Tema do React Native Paper com a paleta da DBS TELECOM — camada theme.
 */

import { MD3LightTheme } from 'react-native-paper';

import { colors } from './colors';

export const paperTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    background: colors.background,
    error: '#D64545',
    onPrimary: colors.white,
    outline: colors.border,
    primary: colors.laranjaVibrante,
    secondary: colors.laranja,
    surface: colors.white,
  },
};
