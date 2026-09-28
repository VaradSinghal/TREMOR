// useCallback is imported here so uncommenting the polling/WS stubs below
// requires no further import changes.
import { useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
// import { useWebSocket } from "./useWebSocket";

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

function App() {
  const [history, setHistory] = useState<Point[]>(() =>
    Array.from({ length: MAX_POINTS }, () => ({
      value: 4 + Math.random() * 1.5,
      baseline: 4.2,
    })),
  );

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [incidentActive, setIncidentActive] = useState(false);

  // tickRef avoids a stale-closure bug: if tick were state, the interval
  // callback would always read the value captured at mount (i.e. 0) and the
  // anomaly phase would never advance.
  const tickRef = useRef(0);

  // Simulated live log/error-rate stream.
  useEffect(() => {
    const interval = window.setInterval(() => {
      tickRef.current += 1;

      // Read the current tick synchronously — no stale closure.
      const anomalyPhase = tickRef.current % 25;

      setHistory((previous) => {
        const previousValue = previous[previous.length - 1]?.value ?? 4.2;

        let nextValue: number;

        if (anomalyPhase >= 18 && anomalyPhase <= 23) {
          // Simulated error spike.
          nextValue = 15 + Math.random() * 18;
        } else {
          // Normal traffic with EWMA-style smoothing.
          nextValue = Math.max(
            1,
            previousValue * 0.65 + (4 + Math.random() * 2) * 0.35,
          );
        }

        return [
          ...previous.slice(-(MAX_POINTS - 1)),
          { value: nextValue, baseline: 4.2 },
        ];
      });
    }, 1000);

    return () => window.clearInterval(interval);
  }, []); // empty — intentional; interval reads from ref, not state

  const currentValue = history[history.length - 1]?.value ?? 4.2;
  const baseline = 4.2;

  const zScore = Math.max(0, (currentValue - baseline) / 2);

  const severity: Severity =
    currentValue > 50
      ? "CRITICAL"
      : zScore >= 8
        ? "HIGH"
        : zScore >= 5
          ? "MEDIUM"
          : zScore >= 3
            ? "LOW"
            : "LOW";

  const isAnomaly = currentValue > baseline * 2;

  // Create a demo alert when the simulated stream enters an anomaly.
  //
  // Only `isAnomaly` and `incidentActive` drive this effect. The other values
  // (severity, currentValue, zScore) change every tick during a spike and
  // would fire this handler repeatedly — each time racing the incidentActive
  // guard on the very first tick. Snapshotting them from the closure is safe:
  // they're derived from `history` which is already up to date by the time
  // this effect runs.
  useEffect(() => {
    if (!isAnomaly || incidentActive) return;

    const newAlert: Alert = {
      id: crypto.randomUUID(),
      incident_id: `INC-${String(Date.now()).slice(-4)}`,
      severity,
      signal_type: "ERROR_RATE",
      value: Number(currentValue.toFixed(2)),
      baseline,
      z_score: Number(zScore.toFixed(2)),
      reason: "Error rate significantly above the learned baseline",
      status: "OPEN",
      created_at: new Date().toLocaleTimeString(),
    };

    setAlerts((previous) => [newAlert, ...previous].slice(0, 10));
    setSelectedAlert(newAlert);
    setIncidentActive(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAnomaly, incidentActive]); // severity/currentValue/zScore intentionally omitted

  // Resolve the simulated incident after the spike disappears.
  useEffect(() => {
    if (incidentActive && !isAnomaly && currentValue < baseline * 1.5) {
      setIncidentActive(false);
    }
  }, [incidentActive, isAnomaly, currentValue, baseline]);

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
  // Polling fallback (swap in when WS is unavailable / during demo mode).
  //
  // Uncomment and point POLL_URL at your REST history endpoint.
  // The hook uses a stable callback ref so it won't re-register on every render.
  // ---------------------------------------------------------------------------
  // const POLL_URL = "http://localhost:8000/api/alerts";
  // const POLL_INTERVAL_MS = 5_000;
  //
  // const handlePolledAlerts = useCallback((fetched: Alert[]) => {
  //   setAlerts((previous) => {
  //     const existingIds = new Set(previous.map((a) => a.id));
  //     const newOnes = fetched.filter((a) => !existingIds.has(a.id));
  //     return [...newOnes, ...previous].slice(0, 10);
  //   });
  // }, []);
  //
  // useEffect(() => {
  //   let cancelled = false;
  //   async function poll() {
  //     try {
  //       const res = await fetch(POLL_URL);
  //       if (!res.ok) return;
  //       const data: Alert[] = await res.json();
  //       if (!cancelled) handlePolledAlerts(data);
  //     } catch { /* network error — silently retry */ }
  //   }
  //   poll();
  //   const id = window.setInterval(poll, POLL_INTERVAL_MS);
  //   return () => { cancelled = true; window.clearInterval(id); };
  // }, [handlePolledAlerts]);

  // ---------------------------------------------------------------------------
  // Live WebSocket (uncomment once Kostubh's ws.py hub is up).
  // Replace the simulated interval above with this.
  // ---------------------------------------------------------------------------
  // const handleWSMessage = useCallback((alert: Alert) => {
  //   setAlerts((previous) => [alert, ...previous].slice(0, 10));
  //   setSelectedAlert(alert);
  //   setIncidentActive(true);
  // }, []);
  //
  // useWebSocket<Alert>("ws://localhost:8000/ws/alerts", handleWSMessage, {
  //   onOpen: () => console.info("[TREMOR] WS connected"),
  //   onError: (e) => console.warn("[TREMOR] WS error", e),
  // });

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

export default App;