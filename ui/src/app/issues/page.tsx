import AppShell from "@/app/_components/AppShell";
import Pagination from "@/app/_components/Pagination";
import styles from "@/app/_components/appShell.module.css";
import { fetchIssuesPage } from "@/lib/masatApi";
import Link from "next/link";

export const dynamic = "force-dynamic";

function severityLabel(sev: number) {
  if (sev >= 9) return { label: "Critical", cls: styles.badgeHigh };
  if (sev >= 7) return { label: "High", cls: styles.badgeHigh };
  if (sev >= 4) return { label: "Medium", cls: styles.badgeMed };
  if (sev >= 1) return { label: "Low", cls: styles.badgeLow };
  return { label: "Info", cls: "" };
}

export default async function IssuesPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};

  const status = typeof sp.status === "string" ? sp.status : "";
  const pageRaw = typeof sp.page === "string" ? sp.page : "1";
  const pageSizeRaw = typeof sp.pageSize === "string" ? sp.pageSize : "30";

  const pageSize = Math.max(10, Math.min(100, Number(pageSizeRaw) || 30));
  const page = Math.max(1, Number(pageRaw) || 1);
  const offset = (page - 1) * pageSize;

  const issuesPage = await fetchIssuesPage({ limit: pageSize, offset, status: status || undefined }).catch(() => ({
    items: [],
    total: 0,
    limit: pageSize,
    offset,
  }));

  return (
    <AppShell
      active="dashboard"
      title="Issues"
      subtitle="Top issues impacting posture. This is an actionable queue (triage workflow is coming next)."
      pills={
        <>
          <span className={styles.pill}>Total: {issuesPage.total}</span>
          {status ? <span className={styles.pill}>Status: {status}</span> : null}
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Filters</div>
          <div className={styles.meta}>Status filtering is persisted.</div>
        </div>
        <div className={styles.actions}>
          <Link className={styles.actionLink} href="/issues">
            All
          </Link>
          <Link className={styles.actionLink} href="/issues?status=open">
            Open
          </Link>
          <Link className={styles.actionLink} href="/issues?status=triaged">
            Triaged
          </Link>
          <Link className={styles.actionLink} href="/issues?status=in_progress">
            In progress
          </Link>
          <Link className={styles.actionLink} href="/issues?status=fixed">
            Fixed
          </Link>
          <Link className={styles.actionLink} href="/issues?status=accepted">
            Accepted
          </Link>
          <Link className={styles.actionLink} href="/issues?status=false_positive">
            False positive
          </Link>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Queue</div>
          <div className={styles.meta}>Sorted by severity, then recency.</div>
        </div>

        <Pagination
          basePath="/issues"
          page={page}
          pageSize={pageSize}
          total={issuesPage.total}
          params={{ status, pageSize: String(pageSize) }}
        />

        <div className={styles.tableWrap}>
          <table className={styles.table} style={{ minWidth: 980 }}>
            <thead>
              <tr>
                <th style={{ width: 110 }}>Severity</th>
                <th>Title</th>
                <th style={{ width: 220 }}>Asset</th>
                <th style={{ width: 140 }}>Status</th>
                <th style={{ width: 130 }}>Last run</th>
              </tr>
            </thead>
            <tbody>
              {issuesPage.items.map((i) => {
                const sev = severityLabel(i.severity || 0);
                return (
                  <tr key={i.fingerprint}>
                    <td>
                      <span className={`${styles.badge} ${sev.cls}`}>{sev.label}</span>
                    </td>
                    <td>
                      <div style={{ fontWeight: 900 }}>{i.title}</div>
                      <div className={styles.meta}>{i.category}</div>
                      {i.remediation ? (
                        <div className={styles.meta}>
                          <strong>Remediation:</strong> {i.remediation}
                        </div>
                      ) : null}
                    </td>
                    <td>
                      <Link className={styles.actionLink} href={`/assets/${encodeURIComponent(i.asset)}`}>
                        {i.asset}
                      </Link>
                      {i.environment ? <div className={styles.meta}>{i.environment}</div> : null}
                      {i.owner ? <div className={styles.meta}>{i.owner}</div> : null}
                    </td>
                    <td className={styles.meta}>{i.status}</td>
                    <td>
                      <Link className={styles.actionLink} href={`/runs/${i.last_run_id}`}>
                        #{i.last_run_id}
                      </Link>
                      <div className={styles.meta}>{new Date(i.last_seen_ts * 1000).toLocaleString()}</div>
                    </td>
                  </tr>
                );
              })}
              {issuesPage.items.length === 0 ? (
                <tr>
                  <td colSpan={5} className={styles.meta}>
                    No issues yet. Run a scan, store it, then refresh.
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
