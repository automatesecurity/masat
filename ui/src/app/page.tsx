import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { KpiRow } from "@/app/_components/KpiRow";
import SeverityBar from "@/app/_components/SeverityBar";
import { fetchDashboard } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const m = await fetchDashboard().catch(() => null);

  return (
    <AppShell
      active="dashboard"
      title="Dashboard"
      subtitle="Executive summary of your current attack surface posture based on stored assets and scan history."
      pills={
        m ? (
          <>
            <span className={styles.pill}>Score: {m.score}/100</span>
            <span className={styles.pill}>Coverage (30d): {m.coverage_30d_pct}%</span>
            <span className={styles.pill}>Runs (7d): {m.runs_7d}</span>
          </>
        ) : (
          <>
            <span className={styles.pill}>API: offline</span>
          </>
        )
      }
    >
      {m ? (
        <>
          <KpiRow
            items={[
              { label: "Posture score", value: `${m.score}/100`, meta: "heuristic" },
              { label: "Total assets", value: m.total_assets },
              { label: "Coverage", value: `${m.coverage_30d_pct}%`, meta: "assets scanned in 30d" },
              { label: "Open ports", value: m.open_ports_total, meta: "from latest scans" },
            ]}
          />

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.sectionTitle}>Risk snapshot</div>
              <div className={styles.meta}>Based on latest run per target.</div>
            </div>

            <SeverityBar
              buckets={{
                critical: m.findings_by_sev.critical || 0,
                high: m.findings_by_sev.high || 0,
                medium: m.findings_by_sev.medium || 0,
                low: m.findings_by_sev.low || 0,
                info: m.findings_by_sev.info || 0,
              }}
            />

            <div className={styles.actions} style={{ marginTop: 12 }}>
              <a className={styles.actionLink} href="/changes">
                View drift (Changes)
              </a>
              <a className={styles.actionLink} href="/assets">
                Review inventory
              </a>
              <a className={styles.actionLink} href="/scan">
                Run a scan
              </a>
            </div>
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.sectionTitle}>Activity & coverage</div>
              <div className={styles.meta}>Operational metrics for program health.</div>
            </div>

            <KpiRow
              items={[
                { label: "Runs (24h)", value: m.runs_24h },
                { label: "Runs (7d)", value: m.runs_7d },
                { label: "Total runs", value: m.total_runs },
                {
                  label: "Targets seen",
                  value: m.targets_seen,
                  meta: m.latest_run_ts ? `latest run: ${new Date(m.latest_run_ts * 1000).toLocaleString()}` : "",
                },
              ]}
            />

            <div className={styles.meta} style={{ marginTop: 12 }}>
              Assets scanned in 30 days: <strong>{m.assets_scanned_30d}</strong> / <strong>{m.total_assets}</strong>
            </div>

            <div className={styles.kv} style={{ fontFamily: "var(--font-sans)", background: "rgba(255,255,255,0.02)" }}>
              <div className={styles.sectionTitle} style={{ margin: 0 }}>
                Inventory breakdown
              </div>
              <div className={styles.meta} style={{ marginTop: 10 }}>
                {Object.entries(m.assets_by_env || {}).length ? (
                  <>
                    {Object.entries(m.assets_by_env || {}).map(([k, v]) => (
                      <span key={k} className={styles.pill} style={{ marginRight: 8 }}>
                        {k}: {v}
                      </span>
                    ))}
                  </>
                ) : (
                  <>No assets inventory yet. Use Seeding to discover assets and import them.</>
                )}
              </div>
            </div>
          </section>
        </>
      ) : (
        <section className={styles.card}>
          <div className={styles.sectionTitle}>Dashboard unavailable</div>
          <div className={styles.meta} style={{ marginTop: 10 }}>
            Unable to load metrics from the API. Start the API server and refresh.
          </div>
        </section>
      )}
    </AppShell>
  );
}
