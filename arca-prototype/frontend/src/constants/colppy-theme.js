/**
 * Colppy Design Tokens
 *
 * Extracted from lib_ui/src/theme/config/config-theme.ts.
 * Used for inline CSS-in-JS styling to match Colppy's visual identity.
 */

export const colors = {
  primary: '#6633CC',
  primary50: '#F0EBFA',
  primary100: '#E0D6F5',
  primary200: '#C2ADEB',
  primary400: '#855CD6',
  primary600: '#5229A3',
  primary700: '#3D1F7A',

  secondary: '#3B8331',
  secondary50: '#EAF7E9',

  danger: '#F04848',
  danger50: '#FDECEC',
  danger600: '#C03939',
  danger700: '#902B2B',

  success: '#2DCE89',
  success50: '#E9FAF1',
  success700: '#1A7A52',

  warning: '#F5BF00',
  warning50: '#FEF8E1',
  warning700: '#927300',

  info: '#4D69FF',
  info50: '#ECEEFF',

  grey50: '#F2F2F2',
  grey100: '#E6E6E6',
  grey200: '#CFCFCF',
  grey300: '#B5B5B5',
  grey400: '#9C9C9C',
  grey: '#838383',
  grey600: '#696969',
  grey700: '#4F4F4F',
  grey800: '#363636',
  grey900: '#1A1A1A',
  grey950: '#0D0D0D',

  white: '#FFFFFF',
  black950: '#0D0D0D',
};

export const fonts = {
  body: "'Nunito Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
};

export const fontSizes = [10, 12, 14, 16, 18, 20, 24, 28, 32, 40, 48];

export const fontWeights = {
  regular: 400,
  medium: 500,
  semiBold: 600,
  bold: 700,
  extraBold: 800,
};

export const space = [0, 4, 8, 16, 32, 64, 128, 256, 512];

export const radii = {
  input: 4,
  card: 8,
  badge: 17,
};
