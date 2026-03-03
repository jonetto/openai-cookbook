import ProgressTrack from './ProgressTrack';
import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';

/**
 * Multi-track progress panel showing status of each import operation.
 */
export default function ImportProgressPanel({ arca }) {
  const tracks = [
    {
      label: 'Login a ARCA',
      status: arca.login === 'done' ? 'done' : arca.login === 'running' ? 'running' : arca.login === 'error' ? 'error' : 'pending',
      count: null,
    },
    {
      label: 'Comprobantes Recibidos',
      status: arca.comprobantes_recibidos.status,
      count: arca.comprobantes_recibidos.total,
    },
    {
      label: 'Comprobantes Emitidos',
      status: arca.comprobantes_emitidos.status,
      count: arca.comprobantes_emitidos.total,
    },
    {
      label: 'Retenciones',
      status: arca.retenciones.status,
      count: arca.retenciones.total,
    },
    {
      label: 'Notificaciones DFE',
      status: arca.notifications.status,
      count: arca.notifications.total,
    },
  ];

  return (
    <div style={styles.panel}>
      <h4 style={styles.heading}>Progreso de importación</h4>
      {tracks.map((track) => (
        <ProgressTrack key={track.label} {...track} />
      ))}
    </div>
  );
}

const styles = {
  panel: {
    background: colors.white,
    border: `1px solid ${colors.grey100}`,
    borderRadius: radii.card,
    padding: 24,
  },
  heading: {
    fontFamily: fonts.body,
    fontSize: 16,
    fontWeight: fontWeights.semiBold,
    color: colors.grey900,
    margin: '0 0 12px 0',
  },
};
