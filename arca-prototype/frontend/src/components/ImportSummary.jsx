import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Final import summary shown when all tracks complete.
 * Displays totals in summary cards with a CTA button.
 */
export default function ImportSummary({ summary, onContinue, onReset }) {
  const cards = [
    { label: 'Comprobantes Recibidos', value: summary.comprobantes_recibidos, icon: '\u{1F4E5}' },
    { label: 'Comprobantes Emitidos', value: summary.comprobantes_emitidos, icon: '\u{1F4E4}' },
    { label: 'Retenciones', value: summary.retenciones, icon: '\u{1F4CB}' },
    { label: 'Notificaciones DFE', value: summary.notifications, icon: '\u{1F4EC}' },
  ];

  const totalItems = Object.values(summary).reduce((a, b) => a + (typeof b === 'number' ? b : 0), 0);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.checkmark}>{'\u2705'}</span>
        <h3 style={styles.title}>Importación completada</h3>
        <p style={styles.subtitle}>{totalItems} elementos importados desde ARCA</p>
      </div>

      <div style={styles.grid}>
        {cards.map((card) => (
          <div key={card.label} style={styles.card}>
            <span style={styles.cardIcon}>{card.icon}</span>
            <span style={styles.cardValue}>{card.value}</span>
            <span style={styles.cardLabel}>{card.label}</span>
          </div>
        ))}
      </div>

      <div style={styles.actions}>
        <button onClick={onContinue} style={styles.primaryButton}>
          Continuar a Colppy
        </button>
        <button onClick={onReset} style={styles.secondaryButton}>
          Nueva importación
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
    padding: 24,
    background: colors.white,
    border: `1px solid ${colors.grey100}`,
    borderRadius: radii.card,
  },
  header: {
    textAlign: 'center',
  },
  checkmark: {
    fontSize: 40,
    display: 'block',
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
    marginTop: 4,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
  },
  card: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 4,
    padding: 16,
    background: colors.grey50,
    borderRadius: radii.card,
  },
  cardIcon: {
    fontSize: 24,
  },
  cardValue: {
    fontFamily: fonts.body,
    fontSize: 28,
    fontWeight: fontWeights.bold,
    color: colors.grey900,
  },
  cardLabel: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.grey,
    textAlign: 'center',
  },
  actions: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
  },
  primaryButton: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.semiBold,
    padding: '12px 32px',
    backgroundColor: colors.primary,
    color: colors.white,
    border: 'none',
    borderRadius: radii.input,
    cursor: 'pointer',
    transition: 'all .2s ease-out',
  },
  secondaryButton: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.semiBold,
    padding: '12px 32px',
    backgroundColor: 'transparent',
    color: colors.primary,
    border: `1px solid ${colors.primary}`,
    borderRadius: radii.input,
    cursor: 'pointer',
    transition: 'all .2s ease-out',
  },
};
