import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchScans, fetchRuns } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};
  const target = typeof sp.target === "string" ? sp.target : "";
  const scans = typeof sp.scans === "string" ? sp.scans : "";
  const error = typeof sp.error === "string" ? sp.error : "";

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

  return (
    <AppShell
      active="scan"
      title="Scan"
      subtitle="Create a stored run (safe on refresh). You can browse and export results from Runs."
      pills={
        <>
          <span className={styles.pill}>
            API: {process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000"}
          </span>
          <span className={styles.pill}>Scanners: {availableScans.length}</span>
          <span className={styles.pill}>Recent runs: {runs.length}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>New scan</div>
          <div className={styles.meta}>Uses POST → store → redirect (no accidental rescan on refresh).</div>
        </div>

        <form method="POST" action="/api/scan" className={styles.form}>
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
              required
            />
          </label>

          <label className={styles.label}>
            Scans
            <span className={styles.hint}>
              Optional comma-separated list (try: {availableScans.slice(0, 6).map((s) => s.id).join(", ")}
              {availableScans.length > 6 ? ", …" : ""})
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

            <button type="submit" className={styles.button}>
              Run scan
            </button>
          </div>
        </form>
      </section>

      {error ? (
        <section className={`${styles.card} ${styles.error}`}>
          <div className={styles.sectionTitle}>Error</div>
          <div className={styles.meta} style={{ marginTop: 10 }}>
            <strong>Scan failed:</strong> {error}
          </div>
        </section>
      ) : null}

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Recent runs</div>
          <div className={styles.meta}>Stored in SQLite by the API server.</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 86 }}>Run</th>
                <th>Target</th>
                <th style={{ width: 210 }}>Time</th>
                <th>Scans</th>
                <th style={{ width: 260 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>
                    <strong>#{r.id}</strong>
                  </td>
                  <td>{r.target}</td>
                  <td>{new Date(r.ts * 1000).toLocaleString()}</td>
                  <td className={styles.meta}>{r.scans.join(", ")}</td>
                  <td>
                    <div className={styles.actions}>
                      <a className={styles.actionLink} href={`/runs/${r.id}`}>
                        View
                      </a>
                      <a className={styles.actionLink} href={`/api/runs/${r.id}/export/json`}>
                        JSON
                      </a>
                      <a className={styles.actionLink} href={`/api/runs/${r.id}/export/md`}>
                        Markdown
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={5} className={styles.meta}>
                    No stored runs yet.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
