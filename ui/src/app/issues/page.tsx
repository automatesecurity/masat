import AppShell from "@/app/_components/AppShell";
import Pagination from "@/app/_components/Pagination";
import styles from "@/app/_components/appShell.module.css";
import { fetchIssuesPage } from "@/lib/masatApi";
import Link from "next/link";
import IssuesTable from "./IssuesTable";

export const dynamic = "force-dynamic";

export default async function IssuesPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};

  const status = typeof sp.status === "string" ? sp.status : "";
  const owner = typeof sp.owner === "string" ? sp.owner : "";
  const pageRaw = typeof sp.page === "string" ? sp.page : "1";
  const pageSizeRaw = typeof sp.pageSize === "string" ? sp.pageSize : "30";

  const pageSize = Math.max(10, Math.min(100, Number(pageSizeRaw) || 30));
  const page = Math.max(1, Number(pageRaw) || 1);
  const offset = (page - 1) * pageSize;

  const issuesPage = await fetchIssuesPage({
    limit: pageSize,
    offset,
    status: status || undefined,
    owner: owner || undefined,
  }).catch(() => ({
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

        <IssuesTable items={issuesPage.items} />

        {issuesPage.items.length === 0 ? (
          <div className={styles.meta} style={{ marginTop: 10 }}>
            No issues yet. Run a scan, store it, then refresh.
          </div>
        ) : null}
      </section>
    </AppShell>
  );
}
