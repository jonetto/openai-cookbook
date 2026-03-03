import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Streaming notifications list from DFE.
 */
export default function NotificationsList({ items, status }) {
  if (!items || items.length === 0) {
    if (status === 'pending' || status === 'running') return null;
    return <p style={styles.noData}>Sin notificaciones en el período seleccionado.</p>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.summaryBar}>
        <span style={styles.summaryCount}>{items.length} notificaciones</span>
      </div>
      <div style={styles.list}>
        {items.map((n, i) => (
          <div key={n.id || i} style={styles.notifCard}>
            <div style={styles.notifHeader}>
              <span style={styles.notifOrganismo}>{n.organismo || 'ARCA'}</span>
              <span style={styles.notifDate}>
                {n.fecha_publicacion ? new Date(n.fecha_publicacion).toLocaleDateString('es-AR') : '-'}
              </span>
            </div>
            <p style={styles.notifMessage}>
              {n.mensaje_preview || n.mensaje_completo || 'Sin contenido'}
            </p>
            <div style={styles.notifFooter}>
              {n.clasificacion && (
                <span style={styles.classBadge}>{n.clasificacion}</span>
              )}
              {n.tiene_adjunto && (
                <span style={styles.attachBadge}>PDF adjunto</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const styles = {
  container: { display: 'flex', flexDirection: 'column', gap: 8 },
  summaryBar: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0' },
  summaryCount: { fontFamily: fonts.body, fontSize: 13, color: colors.grey },
  list: { display: 'flex', flexDirection: 'column', gap: 8 },
  notifCard: {
    border: `1px solid ${colors.grey100}`, borderRadius: radii.card,
    padding: 16, background: colors.white,
  },
  notifHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8,
  },
  notifOrganismo: {
    fontFamily: fonts.body, fontSize: 12, fontWeight: fontWeights.semiBold,
    color: colors.primary, textTransform: 'uppercase',
  },
  notifDate: {
    fontFamily: fonts.body, fontSize: 12, color: colors.grey,
  },
  notifMessage: {
    fontFamily: fonts.body, fontSize: 13, color: colors.grey800,
    margin: 0, lineHeight: 1.5,
    display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  notifFooter: {
    display: 'flex', gap: 8, marginTop: 8,
  },
  classBadge: {
    fontFamily: fonts.body, fontSize: 11, padding: '1px 8px',
    borderRadius: radii.badge, background: colors.grey50, color: colors.grey700,
  },
  attachBadge: {
    fontFamily: fonts.body, fontSize: 11, padding: '1px 8px',
    borderRadius: radii.badge, background: colors.info50, color: colors.info,
  },
  noData: {
    fontFamily: fonts.body, fontSize: 13, color: colors.grey400, textAlign: 'center', padding: 24,
  },
};
