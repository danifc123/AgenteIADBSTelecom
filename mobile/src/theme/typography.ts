/**
 * Tipografia da marca DBS TELECOM — camada theme.
 *
 * Regra de negócio: a fonte oficial da marca é Montserrat. Como este MVP
 * não empacota os arquivos .ttf da fonte, usamos a pilha de fontes do
 * sistema como aproximação visual (mesma decisão tomada no canvas de
 * design) — trocar por Montserrat real é só adicionar os .ttf em
 * `assets/fonts` e carregar via `expo-font` em `App.tsx`.
 */

import { Platform } from 'react-native';

export const fontFamily = Platform.select({
  android: 'sans-serif',
  default: 'System',
  ios: 'System',
});
