import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchRuns, fetchScans } from "@/lib/masatApi";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function RunsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};
  const q = typeof sp.q === "string" ? sp.q.trim() : "";
  const scan = typeof sp.scan === "string" ? sp.scan.trim() : "";
  const limitRaw = typeof sp.limit === "string" ? sp.limit : "100";
  const limit = Math.max(1, Math.min(500, Number(limitRaw) || 100));

  const [runs, availableScans] = await Promise.all([
    fetchRuns(limit).catch(() => []),
    fetchScans().catch(() => []),
  ]);

  const filtered = runs.filter((r) => {
    if (q) {
      const hay = `${r.target} ${r.id}`.toLowerCase();
      if (!hay.includes(q.toLowerCase())) return false;
    }
    if (scan) {
      if (!r.scans.includes(scan)) return false;
    }
    return true;
  });

  return (
    <AppShell
      active="runs"
      title="Runs"
      subtitle="Browse stored scan runs. Filter by target or scan type, drill in for findings, and export." 
      pills={
        <>
          <span className={styles.pill}>Total loaded: {runs.length}</span>
          <span className={styles.pill}>Showing: {filtered.length}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Filters</div>
          <div className={styles.meta}>These are client-side filters (no rescans).</div>
        </div>

        <form method="GET" className={styles.form}>
          <div className={styles.row}>
            <label className={styles.label} style={{ flex: 1, minWidth: 260 }}>
              Search
              <span className={styles.hint}>Target substring or run id</span>
              <input className={styles.input} name="q" placeholder="example.com" defaultValue={q} />
            </label>

            <label className={styles.label} style={{ minWidth: 220 }}>
              Scan
              <span className={styles.hint}>Only runs that include this scan</span>
              <select className={styles.select} name="scan" defaultValue={scan}>
                <option value="">All scans</option>
                {availableScans.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.id}
                  </option>
                ))}
              </select>
            </label>

            <label className={styles.label} style={{ minWidth: 160 }}>
              Limit
              <span className={styles.hint}>Max rows fetched</span>
              <input className={styles.input} name="limit" defaultValue={String(limit)} />
            </label>

            <div className={styles.row} style={{ alignSelf: "end" }}>
              <button className={styles.buttonSecondary} type="submit">
                Apply
              </button>
              <Link className={styles.actionLink} href="/runs">
                Reset
              </Link>
            </div>
          </div>
        </form>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Run history</div>
          <div className={styles.meta}>Click a run to view full results and findings.</div>
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
              {filtered.map((r) => (
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
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className={styles.meta}>
                    No runs match your filters.
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
