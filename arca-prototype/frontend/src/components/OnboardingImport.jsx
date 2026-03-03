import { useReducer, useState, useCallback } from 'react';
import { colors, fonts, fontWeights, radii } from '../constants/colppy-theme';
import { useSSE } from '../hooks/useSSE';
import ImportCredentialsForm from './ImportCredentialsForm';
import CompanyInfoCard from './CompanyInfoCard';
import ImportProgressPanel from './ImportProgressPanel';
import ImportSummary from './ImportSummary';
import ComprobantesTable from './ComprobantesTable';
import RetencionesTable from './RetencionesTable';
import NotificationsList from './NotificationsList';

// ── State machine ─────────────────────────────────────────────────────────

const initialState = {
  phase: 'idle', // idle | importing | complete | error
  jobId: null,

  // Track A: Enrichment
  enrichment: {
    afip: null,
    rns: null,
  },

  // Track B: ARCA
  arca: {
    login: 'pending', // pending | running | done | error
    comprobantes_recibidos: { status: 'pending', items: [], total: 0 },
    comprobantes_emitidos: { status: 'pending', items: [], total: 0 },
    retenciones: { status: 'pending', items: [], total: 0 },
    notifications: { status: 'pending', items: [], total: 0 },
  },

  // Summary (populated on job_completed)
  summary: null,
  error: null,
};

function reducer(state, action) {
  const { type, payload } = action;

  switch (type) {
    case 'job_started':
      return { ...state, phase: 'importing', jobId: payload.job_id };

    case 'enrichment_afip':
      return { ...state, enrichment: { ...state.enrichment, afip: payload } };

    case 'enrichment_rns':
      return { ...state, enrichment: { ...state.enrichment, rns: payload } };

    case 'arca_login_start':
      return { ...state, arca: { ...state.arca, login: 'running' } };

    case 'arca_login_complete':
      return {
        ...state,
        arca: { ...state.arca, login: payload.success ? 'done' : 'error' },
        ...(payload.success ? {} : { error: payload.message }),
      };

    // Comprobantes Recibidos
    case 'comprobantes_recibidos_start':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_recibidos: { ...state.arca.comprobantes_recibidos, status: 'running' },
        },
      };
    case 'comprobantes_recibidos_batch':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_recibidos: {
            status: 'running',
            items: [...state.arca.comprobantes_recibidos.items, ...payload.comprobantes],
            total: payload.running_total,
          },
        },
      };
    case 'comprobantes_recibidos_complete':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_recibidos: {
            ...state.arca.comprobantes_recibidos,
            status: 'done',
            total: payload.total,
          },
        },
      };

    // Comprobantes Emitidos
    case 'comprobantes_emitidos_start':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_emitidos: { ...state.arca.comprobantes_emitidos, status: 'running' },
        },
      };
    case 'comprobantes_emitidos_batch':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_emitidos: {
            status: 'running',
            items: [...state.arca.comprobantes_emitidos.items, ...payload.comprobantes],
            total: payload.running_total,
          },
        },
      };
    case 'comprobantes_emitidos_complete':
      return {
        ...state,
        arca: {
          ...state.arca,
          comprobantes_emitidos: {
            ...state.arca.comprobantes_emitidos,
            status: 'done',
            total: payload.total,
          },
        },
      };

    // Retenciones
    case 'retenciones_start':
      return {
        ...state,
        arca: {
          ...state.arca,
          retenciones: { ...state.arca.retenciones, status: 'running' },
        },
      };
    case 'retenciones_batch':
      return {
        ...state,
        arca: {
          ...state.arca,
          retenciones: {
            status: 'running',
            items: [...state.arca.retenciones.items, ...payload.retenciones],
            total: payload.running_total,
          },
        },
      };
    case 'retenciones_complete':
      return {
        ...state,
        arca: {
          ...state.arca,
          retenciones: { ...state.arca.retenciones, status: 'done', total: payload.total },
        },
      };

    // Notifications
    case 'notifications_start':
      return {
        ...state,
        arca: {
          ...state.arca,
          notifications: { ...state.arca.notifications, status: 'running' },
        },
      };
    case 'notification':
      return {
        ...state,
        arca: {
          ...state.arca,
          notifications: {
            status: 'running',
            items: [...state.arca.notifications.items, payload],
            total: state.arca.notifications.items.length + 1,
          },
        },
      };
    case 'notifications_complete':
      return {
        ...state,
        arca: {
          ...state.arca,
          notifications: { ...state.arca.notifications, status: 'done', total: payload.total },
        },
      };

    // Job lifecycle
    case 'job_completed':
      return { ...state, phase: 'complete', summary: payload.summary };

    case 'error': {
      if (!payload.recoverable) {
        return { ...state, phase: 'error', error: payload.message };
      }
      // Update specific track status to 'error' based on stage
      const stageMap = {
        comprobantes_recibidos: 'comprobantes_recibidos',
        comprobantes_emitidos: 'comprobantes_emitidos',
        retenciones: 'retenciones',
        notifications: 'notifications',
      };
      const trackKey = stageMap[payload.stage];
      if (trackKey && state.arca[trackKey]) {
        return {
          ...state,
          error: payload.message,
          arca: {
            ...state.arca,
            [trackKey]: { ...state.arca[trackKey], status: 'error' },
          },
        };
      }
      return { ...state, error: payload.message };
    }

    case 'ERROR':
      return { ...state, phase: 'error', error: payload.message };

    case 'RESET':
      return { ...initialState };

    default:
      return state;
  }
}

// ── Component ─────────────────────────────────────────────────────────────

export default function OnboardingImport() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { startImport, cancelImport } = useSSE(dispatch);
  const [activeTab, setActiveTab] = useState('recibidos');

  const handleSubmit = useCallback((cuit, password) => {
    startImport(cuit, password);
  }, [startImport]);

  const handleReset = useCallback(() => {
    cancelImport();
    dispatch({ type: 'RESET' });
  }, [cancelImport]);

  const isImporting = state.phase === 'importing';
  const isComplete = state.phase === 'complete';
  const hasEnrichment = state.enrichment.afip !== null;

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        {/* Phase: Idle — show credentials form centered */}
        {state.phase === 'idle' && (
          <div style={styles.centeredForm}>
            <ImportCredentialsForm onSubmit={handleSubmit} disabled={false} />
          </div>
        )}

        {/* Phase: Importing or Complete */}
        {(isImporting || isComplete || state.phase === 'error') && (
          <>
            {/* Company info card — appears as soon as enrichment arrives */}
            {hasEnrichment && (
              <CompanyInfoCard afip={state.enrichment.afip} rns={state.enrichment.rns} />
            )}

            {/* Progress panel — always visible during import */}
            {isImporting && <ImportProgressPanel arca={state.arca} />}

            {/* Error message */}
            {state.error && state.phase === 'error' && (
              <div style={styles.errorBanner}>
                <p style={styles.errorText}>{state.error}</p>
                <button onClick={handleReset} style={styles.retryButton}>Reintentar</button>
              </div>
            )}

            {/* Data tabs — visible once data starts arriving */}
            {(isImporting || isComplete) && hasAnyData(state.arca) && (
              <div style={styles.dataSection}>
                <div style={styles.tabBar}>
                  {TABS.map((tab) => {
                    const count = getTabCount(state.arca, tab.key);
                    const isActive = activeTab === tab.key;
                    const isRunning = getTabStatus(state.arca, tab.key) === 'running';
                    return (
                      <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key)}
                        style={{
                          ...styles.tab,
                          ...(isActive ? styles.tabActive : {}),
                        }}
                      >
                        {tab.label}
                        {count > 0 && (
                          <span style={{
                            ...styles.tabBadge,
                            ...(isRunning ? styles.tabBadgePulsing : {}),
                          }}>
                            {count}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>

                <div style={styles.tabContent}>
                  {activeTab === 'recibidos' && (
                    <ComprobantesTable
                      items={state.arca.comprobantes_recibidos.items}
                      status={state.arca.comprobantes_recibidos.status}
                    />
                  )}
                  {activeTab === 'emitidos' && (
                    <ComprobantesTable
                      items={state.arca.comprobantes_emitidos.items}
                      status={state.arca.comprobantes_emitidos.status}
                    />
                  )}
                  {activeTab === 'retenciones' && (
                    <RetencionesTable
                      items={state.arca.retenciones.items}
                      status={state.arca.retenciones.status}
                    />
                  )}
                  {activeTab === 'notificaciones' && (
                    <NotificationsList
                      items={state.arca.notifications.items}
                      status={state.arca.notifications.status}
                    />
                  )}
                </div>
              </div>
            )}

            {/* Completion summary */}
            {isComplete && state.summary && (
              <ImportSummary
                summary={state.summary}
                onContinue={() => window.open('https://app.colppy.com', '_blank')}
                onReset={handleReset}
              />
            )}
          </>
        )}
      </div>

      {/* Global CSS for animations */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;500;600;700;800&display=swap');

        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

const TABS = [
  { key: 'recibidos', label: 'Recibidos' },
  { key: 'emitidos', label: 'Emitidos' },
  { key: 'retenciones', label: 'Retenciones' },
  { key: 'notificaciones', label: 'Notificaciones' },
];

function hasAnyData(arca) {
  return (
    arca.comprobantes_recibidos.items.length > 0 ||
    arca.comprobantes_emitidos.items.length > 0 ||
    arca.retenciones.items.length > 0 ||
    arca.notifications.items.length > 0 ||
    arca.comprobantes_recibidos.status === 'running' ||
    arca.comprobantes_emitidos.status === 'running'
  );
}

function getTabCount(arca, key) {
  const map = {
    recibidos: arca.comprobantes_recibidos,
    emitidos: arca.comprobantes_emitidos,
    retenciones: arca.retenciones,
    notificaciones: arca.notifications,
  };
  return map[key]?.items.length || 0;
}

function getTabStatus(arca, key) {
  const map = {
    recibidos: arca.comprobantes_recibidos,
    emitidos: arca.comprobantes_emitidos,
    retenciones: arca.retenciones,
    notificaciones: arca.notifications,
  };
  return map[key]?.status || 'pending';
}

const styles = {
  page: {
    minHeight: '100vh',
    background: colors.grey50,
    fontFamily: fonts.body,
  },
  container: {
    maxWidth: 960,
    margin: '0 auto',
    padding: '40px 24px',
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
  },
  centeredForm: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '60vh',
  },
  dataSection: {
    background: colors.white,
    border: `1px solid ${colors.grey100}`,
    borderRadius: radii.card,
    overflow: 'hidden',
  },
  tabBar: {
    display: 'flex',
    borderBottom: `2px solid ${colors.grey100}`,
    background: colors.grey50,
    overflow: 'auto',
  },
  tab: {
    fontFamily: fonts.body,
    fontSize: 13,
    fontWeight: fontWeights.medium,
    color: colors.grey,
    padding: '12px 20px',
    border: 'none',
    background: 'none',
    cursor: 'pointer',
    borderBottom: '2px solid transparent',
    marginBottom: -2,
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    whiteSpace: 'nowrap',
    transition: 'all .15s ease',
  },
  tabActive: {
    color: colors.primary,
    borderBottomColor: colors.primary,
    fontWeight: fontWeights.semiBold,
  },
  tabBadge: {
    fontFamily: fonts.body,
    fontSize: 11,
    fontWeight: fontWeights.semiBold,
    background: colors.primary50,
    color: colors.primary,
    padding: '1px 6px',
    borderRadius: 10,
    minWidth: 18,
    textAlign: 'center',
  },
  tabBadgePulsing: {
    animation: 'shimmer 1.5s infinite',
    backgroundSize: '200% 100%',
    background: `linear-gradient(90deg, ${colors.primary50} 25%, ${colors.primary100} 50%, ${colors.primary50} 75%)`,
  },
  tabContent: {
    padding: 20,
  },
  errorBanner: {
    background: colors.danger50,
    border: `1px solid ${colors.danger}`,
    borderRadius: radii.card,
    padding: 20,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 16,
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.danger700,
    margin: 0,
  },
  retryButton: {
    fontFamily: fonts.body,
    fontSize: 13,
    fontWeight: fontWeights.semiBold,
    padding: '8px 20px',
    background: colors.danger,
    color: colors.white,
    border: 'none',
    borderRadius: radii.input,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
};
