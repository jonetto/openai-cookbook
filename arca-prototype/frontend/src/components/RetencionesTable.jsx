import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Streaming retenciones table.
 */
export default function RetencionesTable({ items, status }) {
  if (!items || items.length === 0) {
    if (status === 'pending' || status === 'running') return null;
    return <p style={styles.noData}>Sin retenciones en el período seleccionado.</p>;
  }

  const totalImporte = items.reduce((sum, r) => {
    const val = parseFloat(r.importeRetenido || r.importe_retenido || 0);
    return sum + (isNaN(val) ? 0 : val);
  }, 0);

  return (
    <div style={styles.container}>
      <div style={styles.summaryBar}>
        <span style={styles.summaryCount}>{items.length} retenciones</span>
        <span style={styles.summaryTotal}>
          Total: ${totalImporte.toLocaleString('es-AR', { minimumFractionDigits: 2 })}
        </span>
      </div>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Fecha</th>
              <th style={styles.th}>Agente</th>
              <th style={styles.th}>Certificado</th>
              <th style={styles.th}>Régimen</th>
              <th style={{ ...styles.th, textAlign: 'right' }}>Importe</th>
            </tr>
          </thead>
          <tbody>
            {items.map((r, i) => (
              <tr key={`${r.numeroCertificado || i}-${i}`} style={i % 2 === 0 ? {} : { background: colors.grey50 + '40' }}>
                <td style={styles.td}>{r.fechaRetencion || r.fecha_retencion || '-'}</td>
                <td style={styles.td}>{r.cuitAgenteRetencion || r.cuit_agente || '-'}</td>
                <td style={{ ...styles.td, fontFamily: 'monospace', fontSize: 12 }}>
                  {r.numeroCertificado || r.numero_certificado || '-'}
                </td>
                <td style={styles.td}>{r.codigoRegimen || r.codigo_regimen || '-'}</td>
                <td style={{ ...styles.td, textAlign: 'right', fontFamily: 'monospace' }}>
                  ${parseFloat(r.importeRetenido || r.importe_retenido || 0).toLocaleString('es-AR', { minimumFractionDigits: 2 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', gap: 8 },
  summaryBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0' },
  summaryCount: { fontFamily: fonts.body, fontSize: 13, color: colors.grey },
  summaryTotal: { fontFamily: fonts.body, fontSize: 14, fontWeight: fontWeights.semiBold, color: colors.grey900 },
  tableWrapper: { overflowX: 'auto', border: `1px solid ${colors.grey100}`, borderRadius: radii.card },
  table: { width: '100%', borderCollapse: 'collapse', fontFamily: fonts.body, fontSize: 13 },
  th: {
    padding: '10px 12px', textAlign: 'left', fontWeight: fontWeights.semiBold, fontSize: 12,
    color: colors.grey, textTransform: 'uppercase', letterSpacing: 0.5,
    borderBottom: `2px solid ${colors.grey100}`, background: colors.grey50, whiteSpace: 'nowrap',
  },
  td: { padding: '8px 12px', color: colors.grey800, borderBottom: `1px solid ${colors.grey50}`, whiteSpace: 'nowrap' },
  noData: { fontFamily: fonts.body, fontSize: 13, color: colors.grey400, textAlign: 'center', padding: 24 },
};
