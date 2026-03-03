import { colors, fonts, fontWeights } from '../constants/colppy-theme';

/**
 * Single progress track row with icon, label, count, and status.
 * Status: 'pending' | 'running' | 'done' | 'error'
 */
export default function ProgressTrack({ label, status, count, error }) {
  const icon = STATUS_ICONS[status] || STATUS_ICONS.pending;
  const statusText = getStatusText(status, count, error);

  return (
    <div style={styles.track}>
      <span style={{ ...styles.icon, ...(status === 'running' ? styles.iconSpinning : {}) }}>
        {icon}
      </span>
      <span style={styles.label}>{label}</span>
      <span style={{ ...styles.status, ...STATUS_COLORS[status] }}>
        {statusText}
      </span>
    </div>
  );
}

const STATUS_ICONS = {
  pending: '\u23F3',   // hourglass
  running: '\u21BB',   // clockwise arrow
  done: '\u2705',      // check
  error: '\u26A0\uFE0F', // warning
};

const STATUS_COLORS = {
  pending: { color: colors.grey400 },
  running: { color: colors.primary },
  done: { color: colors.success700 },
  error: { color: colors.danger },
};

function getStatusText(status, count, error) {
  if (status === 'error') return error || 'Error';
  if (status === 'done') return count != null ? `${count} descargados` : 'Completado';
  if (status === 'running') return count != null ? `${count} descargados...` : 'Descargando...';
  return 'Esperando';
}

const styles = {
  track: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '8px 0',
    borderBottom: `1px solid ${colors.grey50}`,
  },
  icon: {
    fontSize: 16,
    width: 24,
    textAlign: 'center',
    flexShrink: 0,
  },
  iconSpinning: {
    display: 'inline-block',
    animation: 'spin 1s linear infinite',
  },
  label: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.medium,
    color: colors.grey800,
    flex: 1,
  },
  status: {
    fontFamily: fonts.body,
    fontSize: 13,
    fontWeight: fontWeights.regular,
    textAlign: 'right',
    minWidth: 120,
  },
};
