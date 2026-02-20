import { fetchScans, fetchRuns, runScan, type Finding } from "@/lib/masatApi";
import styles from "./page.module.css";

export const dynamic = "force-dynamic";

function sevLabel(sev: number): { label: string; cls: string } {
  if (sev >= 8) return { label: "High", cls: styles.badgeHigh };
  if (sev >= 4) return { label: "Medium", cls: styles.badgeMed };
  return { label: "Low", cls: styles.badgeLow };
}

function bySeverityDesc(a: Finding, b: Finding) {
  return (b.severity ?? 0) - (a.severity ?? 0);
}

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};
  const target = typeof sp.target === "string" ? sp.target : "";
  const scans = typeof sp.scans === "string" ? sp.scans : "";

  const run = sp.run === "1";

  const smartParam = sp.smart;
  const smartEnabled =
    smartParam === undefined
      ? true
      : Array.isArray(smartParam)
        ? smartParam.includes("1")
        : smartParam === "1";

  const [availableScans, runs] = await Promise.all([
    fetchScans().catch(() => []),
    fetchRuns(20).catch(() => []),
  ]);

  let scanResult: Awaited<ReturnType<typeof runScan>> | null = null;
  let scanError: string | null = null;

  if (run && target) {
    try {
      scanResult = await runScan({
        target,
        scans: scans || undefined,
        smart: smartEnabled,
        store: true,
      });
    } catch (e: unknown) {
      scanError = e instanceof Error ? e.message : String(e);
    }
  }

  const findings = (scanResult?.findings || []).slice().sort(bySeverityDesc);

  return (
    <main className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>MASAT Portal</h1>
        <p className={styles.subtitle}>
          Prototype UI for MASAT. Enter a URL, domain, IP, or CIDR; the UI calls the MASAT FastAPI server.
        </p>
      </header>

      <section className={styles.card}>
        <form method="GET" className={styles.form}>
          <label className={styles.label}>
            Target
            <span className={styles.hint}>URL, domain, IP, or CIDR</span>
            <input
              className={styles.input}
              name="target"
              placeholder="https://example.com"
              defaultValue={target}
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
            />
          </label>

          <label className={styles.label}>
            Scans
            <span className={styles.hint}>
              Optional comma-separated list (try: {availableScans.slice(0, 5).map((s) => s.id).join(", ")}
              {availableScans.length > 5 ? ", …" : ""})
            </span>
            <input
              className={styles.input}
              name="scans"
              placeholder="web,tls,nuclei"
              defaultValue={scans}
              list="scan-ids"
              autoCapitalize="none"
              autoCorrect="off"
              spellCheck={false}
            />
            <datalist id="scan-ids">
              {availableScans.map((s) => (
                <option key={s.id} value={s.id} />
              ))}
            </datalist>
          </label>

          <div className={styles.row}>
            <label className={styles.checkbox}>
              <input type="checkbox" name="smart" value="1" defaultChecked={smartEnabled} />
              Smart mode (auto-select scans)
            </label>

            <button type="submit" name="run" value="1" className={styles.button}>
              Scan
            </button>
          </div>
        </form>
      </section>

      {scanError && (
        <section className={`${styles.card} ${styles.error}`}>
          <strong>Scan failed:</strong> {scanError}
        </section>
      )}

      {scanResult && (
        <section className={styles.card}>
          <h2 className={styles.sectionTitle}>Results</h2>
          <div className={styles.meta}>
            <div>
              <strong>Target:</strong> {scanResult.target}
            </div>
            <div>
              <strong>Run ID:</strong> {String(scanResult.runId)}
            </div>
            <div>
              <strong>Scans:</strong> {scanResult.scans?.join(", ")}
            </div>
            <div>
              <strong>Findings:</strong> {findings.length}
            </div>
          </div>

          <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
            {findings.length === 0 ? (
              <div className={styles.meta}>No findings returned.</div>
            ) : (
              findings.map((f, idx) => {
                const sev = sevLabel(f.severity ?? 0);
                return (
                  <div key={`${f.category}-${f.title}-${idx}`} className={styles.finding}>
                    <div className={styles.findingHeader}>
                      <span className={`${styles.badge} ${sev.cls}`}>{sev.label}</span>
                      <span className={styles.findingTitle}>{f.title}</span>
                      <span className={styles.meta}>({f.category})</span>
                    </div>

                    {f.details ? <div className={styles.meta}>{f.details}</div> : null}

                    {f.remediation ? (
                      <div className={styles.meta}>
                        <strong>Remediation:</strong> {f.remediation}
                      </div>
                    ) : null}
                  </div>
                );
              })
            )}
          </div>

          <details style={{ marginTop: 14 }}>
            <summary>Raw findings JSON</summary>
            <pre className={styles.kv}>{JSON.stringify(scanResult.findings, null, 2)}</pre>
          </details>
        </section>
      )}

      <section className={styles.card}>
        <h2 className={styles.sectionTitle}>Recent runs</h2>
        <p className={styles.meta}>
          Stored by the API server in SQLite (default: <code>~/.masat/masat.db</code>).
        </p>

        <ul className={styles.runs}>
          {runs.map((r) => {
            const qs = new URLSearchParams({
              target: r.target,
              scans: r.scans.join(","),
              smart: "1",
            });
            const rerun = new URLSearchParams({
              target: r.target,
              scans: r.scans.join(","),
              smart: "1",
              run: "1",
            });

            return (
              <li key={r.id} className={styles.runItem}>
                <span>
                  <strong>#{r.id}</strong> — {r.target} — {new Date(r.ts * 1000).toLocaleString()} — [
                  {r.scans.join(", ")}]
                </span>
                <span style={{ display: "flex", gap: 12 }}>
                  <a className={styles.runLink} href={`/?${qs.toString()}`}>
                    Load
                  </a>
                  <a className={styles.runLink} href={`/?${rerun.toString()}`}>
                    Run again
                  </a>
                </span>
              </li>
            );
          })}
        </ul>
      </section>
    </main>
  );
}
