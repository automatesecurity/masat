import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchRun, fetchRunDelta, type Finding } from "@/lib/masatApi";

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

  const [run, delta] = await Promise.all([fetchRun(runId), fetchRunDelta(runId).catch(() => null)]);
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

      {delta ? (
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.sectionTitle}>What changed</div>
            <div className={styles.meta}>
              Compared to {delta.prevRunId ? `run #${delta.prevRunId}` : "the prior run"}
            </div>
          </div>

          {!delta.prevRunId ? (
            <div className={styles.meta}>No prior run found for this target yet.</div>
          ) : (
            <>
              <div className={styles.row} style={{ gap: 20, flexWrap: "wrap" }}>
                <span className={styles.pill}>New findings: {delta.newFindings.length}</span>
                <span className={styles.pill}>Resolved findings: {delta.resolvedFindings.length}</span>
                <span className={styles.pill}>New ports: {delta.newPorts.length}</span>
                <span className={styles.pill}>Closed ports: {delta.closedPorts.length}</span>
              </div>

              {delta.newPorts.length || delta.closedPorts.length ? (
                <div className={styles.meta} style={{ marginTop: 10 }}>
                  <strong>Ports:</strong>{" "}
                  {delta.newPorts.length ? `+${delta.newPorts.join(", ")}` : ""}
                  {delta.newPorts.length && delta.closedPorts.length ? "  " : ""}
                  {delta.closedPorts.length ? `-${delta.closedPorts.join(", ")}` : ""}
                </div>
              ) : null}

              {delta.newFindings.length ? (
                <div style={{ marginTop: 10 }}>
                  <div className={styles.sectionTitle}>New findings</div>
                  <ul className={styles.meta} style={{ marginTop: 6, paddingLeft: 18 }}>
                    {delta.newFindings.slice(0, 12).map((f, idx) => (
                      <li key={`${f.category}-${f.title}-${idx}`}>
                        <strong>{f.title}</strong> ({f.category})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {delta.resolvedFindings.length ? (
                <div style={{ marginTop: 10 }}>
                  <div className={styles.sectionTitle}>Resolved since last run</div>
                  <ul className={styles.meta} style={{ marginTop: 6, paddingLeft: 18 }}>
                    {delta.resolvedFindings.slice(0, 12).map((f, idx) => (
                      <li key={`${f.category}-${f.title}-${idx}`}>
                        <strong>{f.title}</strong> ({f.category})
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </>
          )}
        </section>
      ) : null}

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
