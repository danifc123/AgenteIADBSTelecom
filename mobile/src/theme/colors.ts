/**
 * Paleta de cores da marca DBS TELECOM (Manual de Marca) — camada theme.
 */

export const colors = {
  background: '#FAFAF9',
  border: '#F0F0F1',
  cinzaEscuro: '#4B4C51',
  inputBackground: '#F5F5F6',
  laranja: '#FB8200',
  laranjaTint: '#FFF1E8',
  laranjaVibrante: '#F84B03',
  online: '#3EBD6B',
  textMuted: '#8B8D93',
  white: '#FFFFFF',
} as const;

/** Cor de destaque (badge) por departamento — mesma paleta da marca, sem inventar cores novas. */
export const departmentColors: Record<'Comercial' | 'Suporte' | 'Financeiro', string> = {
  Comercial: colors.laranjaVibrante,
  Financeiro: colors.laranja,
  Suporte: colors.cinzaEscuro,
};
