import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { KpiRow } from "@/app/_components/KpiRow";
import SeverityBar from "@/app/_components/SeverityBar";
import { fetchDashboard, fetchTopExposedPorts } from "@/lib/masatApi";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [dash, topPorts] = await Promise.all([
    fetchDashboard().catch(() => null),
    fetchTopExposedPorts(10).catch(() => []),
  ]);

  const m = dash?.metrics || null;
  const trend7d = dash?.trend?.asof7d || null;
  const trend30d = dash?.trend?.asof30d || null;
  const trend90d = dash?.trend?.asof90d || null;
  const narrative = dash?.narrative || [];

  return (
    <AppShell
      active="dashboard"
      title="Dashboard"
      subtitle="Executive summary of your current attack surface posture based on stored assets and scan history."
      pills={
        m ? (
          <>
            <span className={styles.pill}>
              Score: {m.score}/100 ({m.grade})
            </span>
            {trend7d ? (
              <span className={styles.pill}>
                7d Δ: {m.score - trend7d.score >= 0 ? "+" : ""}
                {m.score - trend7d.score}
              </span>
            ) : null}
            {trend30d ? (
              <span className={styles.pill}>
                30d Δ: {m.score - trend30d.score >= 0 ? "+" : ""}
                {m.score - trend30d.score}
              </span>
            ) : null}
            {trend90d ? (
              <span className={styles.pill}>
                90d Δ: {m.score - trend90d.score >= 0 ? "+" : ""}
                {m.score - trend90d.score}
              </span>
            ) : null}
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
              {
                label: "Posture score",
                value: `${m.score}/100`,
                meta: "weighted",
                infoTitle: "How score is calculated",
                infoBody: `Category scores (0–100) are combined using weights.\n\n${Object.entries(m.score_categories || {})
                  .map(([k, v]) => `${k}: ${v} (w=${m.score_weights?.[k] ?? "—"})`)
                  .join("\n")}\n\nHeuristic model; will be tuned as MASAT adds more signals.`,
              },
              { label: "Total assets", value: m.total_assets },
              { label: "Coverage", value: `${m.coverage_30d_pct}%`, meta: "assets scanned in 30d" },
              { label: "Open ports", value: m.open_ports_total, meta: "latest evidence" },
            ]}
          />

          {narrative.length ? (
            <section className={styles.card}>
              <div className={styles.cardHeader}>
                <div className={styles.sectionTitle}>What changed</div>
                <div className={styles.meta}>Compared to 7 days ago.</div>
              </div>
              <div className={styles.meta}>{narrative.join(" ")}</div>
            </section>
          ) : null}

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
              <Link className={styles.actionLink} href="/onboarding">
                Onboarding
              </Link>
              <Link className={styles.actionLink} href="/changes">
                View drift (Changes)
              </Link>
              <Link className={styles.actionLink} href="/assets">
                Review inventory
              </Link>
              <Link className={styles.actionLink} href="/scan">
                Run a scan
              </Link>
            </div>
          </section>

          <section className={styles.card}>
            <div className={styles.cardHeader}>
              <div className={styles.sectionTitle}>Top exposed ports</div>
              <div className={styles.meta}>Across latest scan evidence; click to filter assets.</div>
            </div>

            <div className={styles.tableWrap}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th style={{ width: 140 }}>Port</th>
                    <th style={{ width: 160 }}>Assets</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {topPorts.map((p) => (
                    <tr key={p.port}>
                      <td>
                        <strong>{p.port}</strong>
                      </td>
                      <td className={styles.meta}>{p.assets}</td>
                      <td>
                        <div className={styles.actions}>
                          <Link className={styles.actionLink} href={`/assets?port=${encodeURIComponent(p.port)}`}>
                            View assets
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {topPorts.length === 0 ? (
                    <tr>
                      <td colSpan={3} className={styles.meta}>
                        No port exposure evidence yet. Run scans with nmap enabled.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
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
                  <>
                    No assets inventory yet. Start with onboarding to seed and confirm in-scope assets: <Link className={styles.actionLink} href="/onboarding">Run onboarding</Link>
                  </>
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
