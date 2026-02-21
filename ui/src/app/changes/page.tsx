import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchRuns } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

type DiffSummary = {
  target: string;
  old_run_id: number;
  new_run_id: number;
  new_findings: unknown[];
  resolved_findings: unknown[];
  exposure?: { added_ports?: string[]; removed_ports?: string[]; server_header?: unknown };
};

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

async function fetchDiff(target: string): Promise<DiffSummary | null> {
  const url = `${apiBase()}/diff?target=${encodeURIComponent(target)}&last=2&format=json`;
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) return null;
  return (await res.json()) as DiffSummary;
}

export default async function ChangesPage() {
  const runs = await fetchRuns(50).catch(() => []);
  const targets = Array.from(new Set(runs.map((r) => r.target))).slice(0, 12);

  const diffs = await Promise.all(targets.map((t) => fetchDiff(t)));

  const rows = targets
    .map((t, idx) => ({ target: t, diff: diffs[idx] }))
    .filter((x) => x.diff);

  return (
    <AppShell
      active="changes"
      title="Changes"
      subtitle="Drift across the last two stored runs per target."
      pills={
        <>
          <span className={styles.pill}>Targets: {targets.length}</span>
          <span className={styles.pill}>Rows: {rows.length}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Recent drift</div>
          <div className={styles.meta}>Computed from stored history (no scans triggered)</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Target</th>
                <th style={{ width: 120 }}>Runs</th>
                <th style={{ width: 130 }}>Ports Δ</th>
                <th style={{ width: 140 }}>Findings Δ</th>
                <th style={{ width: 160 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ target, diff }) => {
                const d = diff as DiffSummary;
                const added = d.exposure?.added_ports?.length || 0;
                const removed = d.exposure?.removed_ports?.length || 0;
                const nf = (d.new_findings || []).length;
                const rf = (d.resolved_findings || []).length;

                return (
                  <tr key={target}>
                    <td>
                      <strong>{target}</strong>
                    </td>
                    <td className={styles.meta}>
                      #{d.old_run_id}→#{d.new_run_id}
                    </td>
                    <td className={styles.meta}>
                      +{added} / -{removed}
                    </td>
                    <td className={styles.meta}>
                      +{nf} / -{rf}
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <a className={styles.actionLink} href={`/runs/${d.new_run_id}`}>
                          View run
                        </a>
                        <a
                          className={styles.actionLink}
                          href={`${apiBase()}/diff?target=${encodeURIComponent(target)}&last=2&format=md`}
                        >
                          Diff report
                        </a>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className={styles.meta}>
                    No diffs available yet. Run and store at least 2 scans for a target.
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
