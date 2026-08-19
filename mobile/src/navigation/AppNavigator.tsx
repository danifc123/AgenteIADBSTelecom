/**
 * Navegação do app: Home -> Identification -> Chat — camada navigation.
 */

import { NativeStackScreenProps, createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';

import { ChatScreen } from '../screens/ChatScreen';
import { HomeScreen } from '../screens/HomeScreen';
import { IdentificationScreen } from '../screens/IdentificationScreen';

// #region Tipos de navegação

export type RootStackParamList = {
  Home: undefined;
  Identification: undefined;
  Chat: undefined;
};

export type ScreenProps<Screen extends keyof RootStackParamList> = NativeStackScreenProps<RootStackParamList, Screen>;

// #endregion

const Stack = createNativeStackNavigator<RootStackParamList>();

// #region Navegador

export function AppNavigator() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Home" component={HomeScreen} />
      <Stack.Screen name="Identification" component={IdentificationScreen} />
      <Stack.Screen name="Chat" component={ChatScreen} />
    </Stack.Navigator>
  );
}

// #endregion
