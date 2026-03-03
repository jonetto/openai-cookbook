import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Streaming comprobantes table that grows as batches arrive.
 * Shows a shimmer row at the bottom when still loading.
 */
export default function ComprobantesTable({ items, status }) {
  if (!items || items.length === 0) {
    if (status === 'pending') return null;
    if (status === 'running') {
      return (
        <div style={styles.emptyState}>
          <div style={styles.shimmerRow} />
          <div style={styles.shimmerRow} />
          <div style={styles.shimmerRow} />
        </div>
      );
    }
    return <p style={styles.noData}>Sin comprobantes en el período seleccionado.</p>;
  }

  // Calculate totals
  const totalImporte = items.reduce((sum, c) => sum + (c.importe_total || 0), 0);

  return (
    <div style={styles.container}>
      <div style={styles.summaryBar}>
        <span style={styles.summaryCount}>{items.length} comprobantes</span>
        <span style={styles.summaryTotal}>Total: ${totalImporte.toLocaleString('es-AR', { minimumFractionDigits: 2 })}</span>
      </div>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Fecha</th>
              <th style={styles.th}>Tipo</th>
              <th style={styles.th}>Número</th>
              <th style={styles.th}>Contraparte</th>
              <th style={{ ...styles.th, textAlign: 'right' }}>Importe</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c, i) => (
              <tr key={`${c.numero}-${i}`} style={i % 2 === 0 ? styles.trEven : styles.trOdd}>
                <td style={styles.td}>{c.fecha_emision_display || c.fecha_emision}</td>
                <td style={styles.td}>
                  <span style={styles.tipoBadge}>{c.tipo_comprobante}</span>
                </td>
                <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: 12 }}>{c.numero}</td>
                <td style={styles.td}>{c.denominacion_contraparte}</td>
                <td style={{ ...styles.td, textAlign: 'right', fontFamily: 'monospace' }}>
                  {c.importe_total_display || `$${(c.importe_total || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}`}
                </td>
              </tr>
            ))}
            {status === 'running' && (
              <tr>
                <td colSpan={5} style={styles.shimmerCell}>
                  <div style={styles.shimmerRow} />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  summaryBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
  },
  summaryCount: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.grey,
  },
  summaryTotal: {
    fontFamily: fonts.body,
    fontSize: 14,
    fontWeight: fontWeights.semiBold,
    color: colors.grey900,
  },
  tableWrapper: {
    overflowX: 'auto',
    border: `1px solid ${colors.grey100}`,
    borderRadius: radii.card,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontFamily: fonts.body,
    fontSize: 13,
  },
  th: {
    padding: '10px 12px',
    textAlign: 'left',
    fontWeight: fontWeights.semiBold,
    fontSize: 12,
    color: colors.grey,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    borderBottom: `2px solid ${colors.grey100}`,
    background: colors.grey50,
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '8px 12px',
    color: colors.grey800,
    borderBottom: `1px solid ${colors.grey50}`,
    whiteSpace: 'nowrap',
  },
  trEven: {},
  trOdd: {
    background: colors.grey50 + '40', // very subtle
  },
  tipoBadge: {
    fontSize: 11,
    padding: '1px 6px',
    borderRadius: radii.badge,
    background: colors.primary50,
    color: colors.primary600,
    whiteSpace: 'nowrap',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    padding: 16,
  },
  shimmerRow: {
    height: 16,
    background: `linear-gradient(90deg, ${colors.grey50} 25%, ${colors.grey100} 50%, ${colors.grey50} 75%)`,
    backgroundSize: '200% 100%',
    animation: 'shimmer 1.5s infinite',
    borderRadius: radii.input,
  },
  shimmerCell: {
    padding: '8px 12px',
  },
  noData: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.grey400,
    textAlign: 'center',
    padding: 24,
  },
};
