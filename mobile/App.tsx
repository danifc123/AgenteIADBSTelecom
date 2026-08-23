/**
 * Ponto de entrada do app: provedores globais (tema, navegação, sessão).
 */

import MaterialCommunityIcons from '@expo/vector-icons/MaterialCommunityIcons';
import { NavigationContainer } from '@react-navigation/native';
import { StatusBar } from 'expo-status-bar';
import React, { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ActivityIndicator, PaperProvider } from 'react-native-paper';
import type { IconProps } from 'react-native-paper/lib/typescript/components/MaterialCommunityIcon';

import { SessionProvider } from './src/context/SessionContext';
import { AppNavigator } from './src/navigation/AppNavigator';
import { loadStoredApiBaseUrl } from './src/services/apiClient';
import { colors } from './src/theme/colors';
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
  const [isServerConfigLoaded, setIsServerConfigLoaded] = useState(false);

  useEffect(() => {
    loadStoredApiBaseUrl().finally(() => setIsServerConfigLoaded(true));
  }, []);

  if (!isServerConfigLoaded) {
    return (
      <SafeAreaProvider>
        <View style={styles.loadingContainer}>
          <ActivityIndicator animating color={colors.laranjaVibrante} />
        </View>
      </SafeAreaProvider>
    );
  }

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

const styles = StyleSheet.create({
  loadingContainer: {
    alignItems: 'center',
    backgroundColor: colors.white,
    flex: 1,
    justifyContent: 'center',
  },
});
