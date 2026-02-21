import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { KpiRow } from "@/app/_components/KpiRow";
import { fetchRuns } from "@/lib/masatApi";
import Link from "next/link";

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

export default async function Home() {
  const runs = await fetchRuns(100).catch(() => []);
  const targets = Array.from(new Set(runs.map((r) => r.target))).slice(0, 20);

  const diffs = await Promise.all(targets.map((t) => fetchDiff(t)));
  const rows = targets
    .map((t, idx) => ({ target: t, diff: diffs[idx] }))
    .filter((x) => x.diff) as { target: string; diff: DiffSummary }[];

  // quick KPIs
  const totalTargets = targets.length;
  const changedTargets = rows.filter((r) => {
    const d = r.diff;
    const ports = (d.exposure?.added_ports?.length || 0) + (d.exposure?.removed_ports?.length || 0);
    const findings = (d.new_findings || []).length + (d.resolved_findings || []).length;
    return ports + findings > 0 || Boolean(d.exposure?.server_header);
  }).length;

  return (
    <AppShell
      active="changes"
      title="Changes"
      subtitle="EASM drift dashboard (home)."
      pills={
        <>
          <span className={styles.pill}>Targets: {totalTargets}</span>
          <span className={styles.pill}>Changed: {changedTargets}</span>
          <span className={styles.pill}>Runs loaded: {runs.length}</span>
        </>
      }
    >
      <KpiRow
        items={[
          { label: "Targets", value: totalTargets },
          { label: "Changed", value: changedTargets, meta: "based on last 2 runs" },
          { label: "Runs loaded", value: runs.length },
          { label: "API", value: "Connected", meta: process.env.NEXT_PUBLIC_MASAT_API_BASE || "127.0.0.1:8000" },
        ]}
      />

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Drift summary</div>
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
                <th style={{ width: 180 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ target, diff }) => {
                const added = diff.exposure?.added_ports?.length || 0;
                const removed = diff.exposure?.removed_ports?.length || 0;
                const nf = (diff.new_findings || []).length;
                const rf = (diff.resolved_findings || []).length;

                return (
                  <tr key={target}>
                    <td>
                      <strong>{target}</strong>
                    </td>
                    <td className={styles.meta}>
                      #{diff.old_run_id}→#{diff.new_run_id}
                    </td>
                    <td className={styles.meta}>
                      +{added} / -{removed}
                    </td>
                    <td className={styles.meta}>
                      +{nf} / -{rf}
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <a className={styles.actionLink} href={`/runs/${diff.new_run_id}`}>
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

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Run a new scan</div>
          <div className={styles.meta}>Go to Scan to create a new stored run.</div>
        </div>
        <div className={styles.actions}>
          <Link className={styles.actionLink} href="/scan">
            Run a scan
          </Link>
          <Link className={styles.actionLink} href="/runs">
            Browse runs
          </Link>
          <Link className={styles.actionLink} href="/assets">
            Browse assets
          </Link>
        </div>
      </section>
    </AppShell>
  );
}
