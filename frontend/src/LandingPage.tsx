import "./LandingPage.css";

function LandingPage() {
  return (
    <div className="landing-page">
      <nav className="landing-nav">
        <div className="landing-logo">TREMOR</div>

        <div className="landing-nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="/dashboard">Dashboard</a>
          <a
            href="https://github.com/VaradSinghal/TREMOR"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </div>
      </nav>

      <main className="landing-hero">
        <section>
          <div className="landing-eyebrow">
            REAL-TIME ANOMALY DETECTION
          </div>

          <h1 className="landing-title">
            See the anomaly
            <br />
            <span>before it becomes an incident.</span>
          </h1>

          <p className="landing-description">
            TREMOR continuously monitors application logs, learns normal
            behaviour, and surfaces meaningful anomalies in real time.
          </p>

          <div className="landing-actions">
            <a
              href="/dashboard"
              className="landing-button landing-button-primary"
            >
              Launch Dashboard
            </a>

            <a
              href="https://github.com/VaradSinghal/TREMOR"
              target="_blank"
              rel="noreferrer"
              className="landing-button landing-button-secondary"
            >
              View on GitHub
            </a>
          </div>
        </section>

        <section className="landing-visual">
          <div className="landing-visual-label">
            LIVE SYSTEM ACTIVITY
          </div>

          <div className="landing-wave" />

          <div className="landing-alert">
            <div className="landing-alert-label">
              ANOMALY DETECTED
            </div>

            <div className="landing-alert-value">
              HIGH SEVERITY
            </div>

            <div className="landing-alert-meta">
              Error rate · 31.8%
              <br />
              Baseline · 4.2%
              <br />
              Z-score · 7.4
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

export default LandingPage;