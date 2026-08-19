/**
 * Ponto de entrada do app: provedores globais (tema, navegação, sessão).
 */

import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PaperProvider } from 'react-native-paper';
import type { IconProps } from 'react-native-paper/lib/typescript/components/MaterialCommunityIcon';

import { SessionProvider } from './src/context/SessionContext';
import { AppNavigator } from './src/navigation/AppNavigator';
import { paperTheme } from './src/theme/paperTheme';

// Expo managed workflow: usa @expo/vector-icons (já linkado) em vez do
// resolvedor padrão do Paper, que depende de react-native-vector-icons
// com linking nativo manual.
const paperIconSettings = {
  icon: ({ name, color, size }: IconProps) => (
    <MaterialCommunityIcons name={name as never} color={color ?? '#4B4C51'} size={size} />
  ),
};

export default function App() {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={paperTheme} settings={paperIconSettings}>
        <SessionProvider>
          <NavigationContainer>
            <AppNavigator />
            <StatusBar style="dark" />
          </NavigationContainer>
        </SessionProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
}
