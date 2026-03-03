import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Displays enrichment data (AFIP + RNS) as a company info card.
 * Shows skeleton/shimmer while loading, fills in as data arrives.
 */
export default function CompanyInfoCard({ afip, rns }) {
  const loading = !afip;
  const hasError = afip?.error;

  if (loading) {
    return (
      <div style={styles.card}>
        <div style={styles.skeleton} />
        <div style={{ ...styles.skeleton, width: '60%', height: 14 }} />
        <div style={{ ...styles.skeleton, width: '40%', height: 14 }} />
      </div>
    );
  }

  if (hasError) {
    return (
      <div style={styles.warningBanner}>
        <span style={styles.warningIcon}>{'\u26A0\uFE0F'}</span>
        <span style={styles.warningText}>
          Datos de AFIP no disponibles — la importación continuará sin enriquecimiento.
        </span>
      </div>
    );
  }

  // Calculate business age from RNS creation_date
  let businessAge = null;
  if (rns?.creation_date) {
    const created = new Date(rns.creation_date);
    const now = new Date();
    const years = Math.floor((now - created) / (365.25 * 24 * 60 * 60 * 1000));
    businessAge = years;
  }

  const condicionBadge = getCondicionBadge(afip.condicion_impositiva);
  const primaryActivity = afip.actividades?.[0];

  return (
    <div style={styles.card}>
      <div style={styles.row}>
        <h3 style={styles.companyName}>{afip.razon_social}</h3>
        {condicionBadge && (
          <span style={{ ...styles.badge, ...condicionBadge.style }}>
            {condicionBadge.label}
          </span>
        )}
      </div>

      <div style={styles.detailsGrid}>
        {afip.direccion && (
          <DetailItem label="Domicilio" value={`${afip.direccion}, ${afip.localidad || ''} ${afip.provincia || ''}`} />
        )}
        {primaryActivity && (
          <DetailItem label="Actividad principal" value={primaryActivity.descripcion} />
        )}
        {rns?.tipo_societario && (
          <DetailItem label="Tipo societario" value={rns.tipo_societario} />
        )}
        {businessAge !== null && (
          <DetailItem
            label="Antigüedad"
            value={`Constituida en ${rns.creation_date?.slice(0, 4)} (${businessAge} años)`}
          />
        )}
        {afip.estado && (
          <DetailItem
            label="Estado"
            value={afip.estado}
            valueStyle={afip.estado === 'ACTIVO' ? { color: colors.success700 } : { color: colors.danger }}
          />
        )}
      </div>
    </div>
  );
}

function DetailItem({ label, value, valueStyle }) {
  return (
    <div style={styles.detailItem}>
      <span style={styles.detailLabel}>{label}</span>
      <span style={{ ...styles.detailValue, ...valueStyle }}>{value}</span>
    </div>
  );
}

function getCondicionBadge(condicion) {
  if (!condicion) return null;
  const lower = condicion.toLowerCase();
  if (lower.includes('responsable inscripto')) {
    return { label: 'Resp. Inscripto', style: { background: colors.info50, color: colors.info } };
  }
  if (lower.includes('monotributo')) {
    return { label: 'Monotributo', style: { background: colors.warning50, color: colors.warning700 } };
  }
  if (lower.includes('exento')) {
    return { label: 'Exento', style: { background: colors.grey50, color: colors.grey700 } };
  }
  return { label: condicion, style: { background: colors.grey50, color: colors.grey700 } };
}

const styles = {
  card: {
    background: colors.white,
    border: `1px solid ${colors.grey100}`,
    borderRadius: radii.card,
    padding: 24,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  skeleton: {
    height: 20,
    width: '80%',
    background: `linear-gradient(90deg, ${colors.grey50} 25%, ${colors.grey100} 50%, ${colors.grey50} 75%)`,
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: radii.input,
  },
  row: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap',
  },
  companyName: {
    fontFamily: fonts.body,
    fontSize: 20,
    fontWeight: fontWeights.bold,
    color: colors.grey900,
    margin: 0,
  },
  badge: {
    fontFamily: fonts.body,
    fontSize: 12,
    fontWeight: fontWeights.semiBold,
    padding: '2px 10px',
    borderRadius: radii.badge,
    whiteSpace: 'nowrap',
  },
  detailsGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 12,
  },
  detailItem: {
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
  },
  detailLabel: {
    fontFamily: fonts.body,
    fontSize: 12,
    fontWeight: fontWeights.medium,
    color: colors.grey,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  detailValue: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.grey800,
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.warning700,
    margin: 0,
  },
  warningBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 16px',
    background: colors.warning50 || '#FFF9E6',
    border: `1px solid ${colors.warning || '#F5BF00'}33`,
    borderRadius: radii.card,
  },
  warningIcon: {
    fontSize: 14,
    flexShrink: 0,
  },
  warningText: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.grey700 || '#4A4A4A',
  },
};
