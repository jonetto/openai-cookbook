import { useState } from 'react';
import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * CUIT + Clave Fiscal entry form.
 * Format-masks CUIT as XX-XXXXXXXX-X as the user types.
 */
export default function ImportCredentialsForm({ onSubmit, disabled }) {
  const [cuit, setCuit] = useState('');
  const [password, setPassword] = useState('');

  const formatCuit = (raw) => {
    const digits = raw.replace(/\D/g, '').slice(0, 11);
    if (digits.length <= 2) return digits;
    if (digits.length <= 10) return `${digits.slice(0, 2)}-${digits.slice(2)}`;
    return `${digits.slice(0, 2)}-${digits.slice(2, 10)}-${digits.slice(10)}`;
  };

  const handleCuitChange = (e) => {
    setCuit(formatCuit(e.target.value));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanCuit = cuit.replace(/\D/g, '');
    if (cleanCuit.length === 11 && password) {
      onSubmit(cleanCuit, password);
    }
  };

  const cleanCuit = cuit.replace(/\D/g, '');
  const isValid = cleanCuit.length === 11 && password.length > 0;

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.header}>
        <h2 style={styles.title}>Importar datos de ARCA</h2>
        <p style={styles.subtitle}>
          Ingresá tu CUIT y Clave Fiscal para descargar automáticamente tus comprobantes,
          retenciones y notificaciones.
        </p>
      </div>

      <div style={styles.fieldGroup}>
        <label style={styles.label}>CUIT</label>
        <input
          type="text"
          value={cuit}
          onChange={handleCuitChange}
          placeholder="XX-XXXXXXXX-X"
          disabled={disabled}
          style={{
            ...styles.input,
            ...(disabled ? styles.inputDisabled : {}),
          }}
          autoFocus
        />
      </div>

      <div style={styles.fieldGroup}>
        <label style={styles.label}>Clave Fiscal</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Tu clave fiscal de AFIP/ARCA"
          disabled={disabled}
          style={{
            ...styles.input,
            ...(disabled ? styles.inputDisabled : {}),
          }}
        />
      </div>

      <button
        type="submit"
        disabled={!isValid || disabled}
        style={{
          ...styles.button,
          ...((!isValid || disabled) ? styles.buttonDisabled : {}),
        }}
      >
        {disabled ? 'Importando...' : 'Importar datos de ARCA'}
      </button>

      <p style={styles.disclaimer}>
        Tus credenciales se usan una sola vez para descargar tus datos. No las almacenamos.
      </p>
    </form>
  );
}

const styles = {
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    width: '100%',
    maxWidth: 440,
  },
  header: {
    marginBottom: 8,
  },
  title: {
    fontFamily: fonts.body,
    fontSize: 24,
    fontWeight: fontWeights.bold,
    color: colors.grey900,
    margin: 0,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.grey,
    marginTop: 8,
    lineHeight: 1.5,
  },
  fieldGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  label: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.semiBold,
    color: colors.grey900,
  },
  input: {
    fontFamily: fonts.body,
    fontSize: 14,
    padding: '10px 16px',
    border: `1px solid ${colors.grey300}`,
    borderRadius: radii.input,
    outline: 'none',
    transition: 'border-color .15s ease-in-out',
    color: colors.grey900,
    background: colors.white,
  },
  inputDisabled: {
    background: colors.grey50,
    color: colors.grey,
    borderColor: colors.grey100,
  },
  button: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.semiBold,
    padding: '12px 24px',
    backgroundColor: colors.primary,
    color: colors.white,
    border: 'none',
    borderRadius: radii.input,
    cursor: 'pointer',
    transition: 'all .2s ease-out',
    marginTop: 8,
  },
  buttonDisabled: {
    backgroundColor: colors.grey300,
    cursor: 'not-allowed',
  },
  disclaimer: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.grey400,
    textAlign: 'center',
    marginTop: 4,
  },
};
