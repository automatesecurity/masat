import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchRun, type Finding } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

function sevLabel(sev: number): { label: string; cls: string } {
  if (sev >= 8) return { label: "High", cls: styles.badgeHigh };
  if (sev >= 4) return { label: "Medium", cls: styles.badgeMed };
  return { label: "Low", cls: styles.badgeLow };
}

function bySeverityDesc(a: Finding, b: Finding) {
  return (b.severity ?? 0) - (a.severity ?? 0);
}

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const runId = Number(id);

  const run = await fetchRun(runId);
  const findings = (run.findings || []).slice().sort(bySeverityDesc);

  return (
    <AppShell
      active="runs"
      title={`Run #${run.id}`}
      subtitle={`Target: ${run.target}`}
      pills={
        <>
          <span className={styles.pill}>{new Date(run.ts * 1000).toLocaleString()}</span>
          <span className={styles.pill}>Scans: {(run.scans || []).length}</span>
          <span className={styles.pill}>Findings: {findings.length}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Summary</div>
          <div className={styles.actions}>
            <a className={styles.actionLink} href={`/api/runs/${run.id}/export/json`}>
              Export JSON
            </a>
            <a className={styles.actionLink} href={`/api/runs/${run.id}/export/md`}>
              Export Markdown
            </a>
          </div>
        </div>

        <div className={styles.meta}>
          <div>
            <strong>Target:</strong> {run.target}
          </div>
          <div>
            <strong>Scans:</strong> {(run.scans || []).join(", ") || "(none)"}
          </div>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Findings</div>
          <div className={styles.meta}>Sorted by severity</div>
        </div>

        {findings.length === 0 ? (
          <div className={styles.meta}>No findings returned.</div>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table} style={{ minWidth: 900 }}>
              <thead>
                <tr>
                  <th style={{ width: 120 }}>Severity</th>
                  <th>Title</th>
                  <th style={{ width: 170 }}>Category</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f, idx) => {
                  const sev = sevLabel(f.severity ?? 0);
                  return (
                    <tr key={`${f.category}-${f.title}-${idx}`}>
                      <td>
                        <span className={`${styles.badge} ${sev.cls}`}>{sev.label}</span>
                      </td>
                      <td>
                        <div style={{ fontWeight: 900 }}>{f.title}</div>
                        {f.details ? <div className={styles.meta}>{f.details}</div> : null}
                        {f.remediation ? (
                          <div className={styles.meta}>
                            <strong>Remediation:</strong> {f.remediation}
                          </div>
                        ) : null}
                      </td>
                      <td className={styles.meta}>{f.category}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Raw data</div>
          <div className={styles.meta}>As stored in SQLite</div>
        </div>

        <details>
          <summary className={styles.meta}>Results JSON</summary>
          <pre className={styles.kv}>{JSON.stringify(run.results, null, 2)}</pre>
        </details>

        <details style={{ marginTop: 10 }}>
          <summary className={styles.meta}>Findings JSON</summary>
          <pre className={styles.kv}>{JSON.stringify(run.findings, null, 2)}</pre>
        </details>
      </section>
    </AppShell>
  );
}
