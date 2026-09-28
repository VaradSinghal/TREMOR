// useCallback is imported here so uncommenting the polling/WS stubs below
// requires no further import changes.
import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { useWebSocket } from "./useWebSocket";
type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

type Alert = {
  id: string;
  incident_id: string;
  severity: Severity;
  signal_type: string;
  value: number;
  baseline: number;
  z_score: number;
  reason: string;
  status: "OPEN" | "ACKED" | "SILENCED" | "RESOLVED";
  created_at: string;
};

type Point = {
  value: number;
  baseline: number;
};

const MAX_POINTS = 60;

function Dashboard() {
  const [history, setHistory] = useState<Point[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [incidentActive, setIncidentActive] = useState(false);
  const [currentValue, setCurrentValue] = useState(0);
  const [baseline, setBaseline] = useState(0);
  const [zScore, setZScore] = useState(0);
  const [severity, setSeverity] = useState<Severity>("LOW");

  // Keep the drawer in sync: if the alert displayed in the drawer is updated
  // elsewhere (ack/silence from another session, or a status push over WS),
  // reflect that change without requiring the user to close and reopen.
  useEffect(() => {
    if (!selectedAlert) return;
    const live = alerts.find((a) => a.id === selectedAlert.id);
    if (live && live.status !== selectedAlert.status) {
      setSelectedAlert(live);
    }
  }, [alerts, selectedAlert]);

  // ---------------------------------------------------------------------------
  // Live WebSocket Integration
  // ---------------------------------------------------------------------------
  const handleWSMessage = useCallback((message: any) => {
    if (message.type === "snapshot") {
      setAlerts(message.data.alerts || []);
    } else if (message.type === "alert") {
      const alert = message.data;
      setAlerts((previous) => {
        const existing = previous.findIndex(a => a.id === alert.id);
        if (existing !== -1) {
          const next = [...previous];
          next[existing] = alert;
          return next;
        }
        return [alert, ...previous].slice(0, 10);
      });
      if (alert.status === "OPEN") {
         setSelectedAlert(alert);
         setIncidentActive(true);
      } else if (alert.status === "RESOLVED") {
         setIncidentActive(false);
      }
    } else if (message.type === "metric") {
      const tick = message.data;
      
      setCurrentValue(tick.error_rate ?? 0);
      setBaseline(tick.baseline ?? 0);
      setZScore(tick.z ?? 0);
      setSeverity((tick.severity as Severity) || "LOW");

      setHistory((prev) => {
         const val = tick.error_rate ?? 0;
         const base = tick.baseline ?? 0;
         return [...prev.slice(-(MAX_POINTS - 1)), { value: val, baseline: base }];
      });
    }
  }, []);

  useWebSocket<any>("ws://localhost:8000/ws/alerts", handleWSMessage, {
    onOpen: () => console.info("[TREMOR] WS connected"),
    onError: (e) => console.warn("[TREMOR] WS error", e),
  });

  const chart = useMemo(() => {
    const width = 1000;
    const height = 280;

    const maxValue = Math.max(
      35,
      ...history.map((point) => point.value),
      baseline * 2,
    );

    const points = history.map((point, index) => {
      const x = (index / (MAX_POINTS - 1)) * width;
      const y = height - (point.value / maxValue) * (height - 20);

      return `${x},${y}`;
    });

    const baselineY =
      height - (baseline / maxValue) * (height - 20);

    return {
      points: points.join(" "),
      baselineY,
    };
  }, [history, baseline]);

  const acknowledgeAlert = () => {
    if (!selectedAlert) return;

    const updated = {
      ...selectedAlert,
      status: "ACKED" as const,
    };

    setSelectedAlert(updated);

    setAlerts((previous) =>
      previous.map((alert) =>
        alert.id === updated.id ? updated : alert,
      ),
    );
  };

  const silenceAlert = () => {
    if (!selectedAlert) return;

    const updated = {
      ...selectedAlert,
      status: "SILENCED" as const,
    };

    setSelectedAlert(updated);

    setAlerts((previous) =>
      previous.map((alert) =>
        alert.id === updated.id ? updated : alert,
      ),
    );
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <div className="brand">TREMOR</div>
          <div className="subtitle">
            Real-Time Anomaly Detection
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          SYSTEM ONLINE
        </div>
      </header>

      <main className="dashboard">
        {/* TOP METRICS */}
        <section className="overview">
          <div className="metric-card">
            <span className="metric-label">ERROR RATE</span>

            <strong>{currentValue.toFixed(1)}%</strong>

            <span className="metric-change">
              {isAnomaly
                ? "↑ ANOMALOUS"
                : "Within expected range"}
            </span>
          </div>

          <div className="metric-card">
            <span className="metric-label">BASELINE</span>

            <strong>{baseline.toFixed(1)}%</strong>

            <span className="metric-change">
              EWMA · 60s window
            </span>
          </div>

          <div className="metric-card">
            <span className="metric-label">
              ACTIVE INCIDENT
            </span>

            <strong className={`severity-${severity.toLowerCase()}`}>
              {isAnomaly ? severity : "NONE"}
            </strong>

            <span className="metric-change">
              {isAnomaly
                ? alerts[0]?.incident_id ?? "Detecting..."
                : "System normal"}
            </span>
          </div>
        </section>

        {/* CHART */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Error Rate</h2>

              <span>
                60-second sliding window · live
              </span>
            </div>

            <div className="legend">
              <span className="legend-current" />
              Current

              <span className="legend-baseline" />
              Baseline
            </div>
          </div>

          <div className="chart-placeholder">
            <svg
              viewBox="0 0 1000 280"
              preserveAspectRatio="none"
              className="chart"
            >
              <polyline
                points={chart.points}
                fill="none"
                stroke="#b57cff"
                strokeWidth="3"
                vectorEffect="non-scaling-stroke"
              />

              <line
                x1="0"
                x2="1000"
                y1={chart.baselineY}
                y2={chart.baselineY}
                stroke="#55555f"
                strokeWidth="1"
                strokeDasharray="6 5"
                vectorEffect="non-scaling-stroke"
              />
            </svg>

            <div className="chart-label baseline-label">
              BASELINE
            </div>

            <div className="chart-label live-label">
              LIVE
            </div>
          </div>
        </section>

        {/* LIVE ALERTS */}
        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Live Alerts</h2>

              <span>
                Real-time anomaly detections
              </span>
            </div>

            <span className="alert-count">
              {alerts.length} ALERT{alerts.length !== 1 ? "S" : ""}
            </span>
          </div>

          <div className="alert-list">
            {alerts.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">✓</div>

                <strong>No anomalies detected</strong>

                <span>
                  Monitoring the incoming log stream...
                </span>
              </div>
            ) : (
              alerts.map((alert) => (
                <button
                  className="alert-row"
                  key={alert.id}
                  onClick={() => setSelectedAlert(alert)}
                >
                  <span
                    className={`severity severity-${alert.severity.toLowerCase()}`}
                  >
                    {alert.severity}
                  </span>

                  <div className="alert-info">
                    <strong>
                      {alert.signal_type}
                    </strong>

                    <span>
                      {alert.reason}
                    </span>
                  </div>

                  <div className="alert-meta">
                    <span>{alert.status}</span>
                    <time>{alert.created_at}</time>
                  </div>
                </button>
              ))
            )}
          </div>
        </section>
      </main>

      {/* ALERT DRAWER */}
      {selectedAlert && (
        <div
          className="drawer-backdrop"
          onClick={() => setSelectedAlert(null)}
        >
          <aside
            className="alert-drawer"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <span className="metric-label">
                  INCIDENT
                </span>

                <h2>
                  {selectedAlert.incident_id}
                </h2>
              </div>

              <button
                className="close-button"
                onClick={() => setSelectedAlert(null)}
              >
                ×
              </button>
            </div>

            <div
              className={`drawer-severity severity-${selectedAlert.severity.toLowerCase()}`}
            >
              {selectedAlert.severity}
            </div>

            <div className="drawer-section">
              <span className="metric-label">
                SIGNAL
              </span>

              <strong>
                {selectedAlert.signal_type}
              </strong>
            </div>

            <div className="drawer-grid">
              <div>
                <span className="metric-label">
                  CURRENT
                </span>

                <strong>
                  {selectedAlert.value}%
                </strong>
              </div>

              <div>
                <span className="metric-label">
                  BASELINE
                </span>

                <strong>
                  {selectedAlert.baseline}%
                </strong>
              </div>

              <div>
                <span className="metric-label">
                  Z-SCORE
                </span>

                <strong>
                  {selectedAlert.z_score}
                </strong>
              </div>

              <div>
                <span className="metric-label">
                  STATUS
                </span>

                <strong>
                  {selectedAlert.status}
                </strong>
              </div>
            </div>

            <div className="drawer-section">
              <span className="metric-label">
                EXPLANATION
              </span>

              <p>
                {selectedAlert.reason}
              </p>
            </div>

            <div className="drawer-actions">
              <button
                className="action-button"
                onClick={acknowledgeAlert}
              >
                ACKNOWLEDGE
              </button>

              <button
                className="action-button secondary"
                onClick={silenceAlert}
              >
                SILENCE
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
