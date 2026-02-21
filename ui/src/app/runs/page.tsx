import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import Pagination from "@/app/_components/Pagination";
import { fetchRunsPage, fetchScans } from "@/lib/masatApi";
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

  const pageRaw = typeof sp.page === "string" ? sp.page : "1";
  const pageSizeRaw = typeof sp.pageSize === "string" ? sp.pageSize : "30";
  const pageSize = Math.max(10, Math.min(100, Number(pageSizeRaw) || 30));
  const page = Math.max(1, Number(pageRaw) || 1);
  const offset = (page - 1) * pageSize;

  const [runsPage, availableScans] = await Promise.all([
    fetchRunsPage({ limit: pageSize, offset }).catch(() => ({ items: [], total: 0, limit: pageSize, offset })),
    fetchScans().catch(() => []),
  ]);

  const runs = runsPage.items;

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
      title="Evidence"
      subtitle="Raw evidence collected over time. Most users should start with Dashboard → Issues → Assets." 
      pills={
        <>
          <span className={styles.pill}>Total: {runsPage.total}</span>
          <span className={styles.pill}>Loaded: {runs.length}</span>
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
              Page size
              <span className={styles.hint}>Rows per page</span>
              <input className={styles.input} name="pageSize" defaultValue={String(pageSize)} />
            </label>
            <input type="hidden" name="page" value="1" />

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

        <Pagination
          basePath="/runs"
          page={page}
          pageSize={pageSize}
          total={runsPage.total}
          params={{ q, scan, pageSize: String(pageSize) }}
        />

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 86 }}>Run</th>
                <th>Target</th>
                <th style={{ width: 210 }}>Time</th>
                <th>Methodology</th>
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
                  <td className={styles.meta}>
                    <details>
                      <summary className={styles.meta}>Show</summary>
                      <div style={{ marginTop: 6 }}>{r.scans.join(", ") || "(none)"}</div>
                    </details>
                  </td>
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
