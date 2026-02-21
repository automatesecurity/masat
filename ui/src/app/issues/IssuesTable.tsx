"use client";

import styles from "@/app/_components/appShell.module.css";
import { type IssueRow, updateIssue } from "@/lib/masatApi";
import Link from "next/link";
import { useMemo, useState } from "react";

const STATUSES = [
  "open",
  "triaged",
  "in_progress",
  "fixed",
  "accepted",
  "false_positive",
] as const;

function severityLabel(sev: number) {
  if (sev >= 9) return { label: "Critical", cls: styles.badgeHigh };
  if (sev >= 7) return { label: "High", cls: styles.badgeHigh };
  if (sev >= 4) return { label: "Medium", cls: styles.badgeMed };
  if (sev >= 1) return { label: "Low", cls: styles.badgeLow };
  return { label: "Info", cls: "" };
}

export default function IssuesTable({ items }: { items: IssueRow[] }) {
  const [pending, setPending] = useState<Record<string, boolean>>({});
  const [local, setLocal] = useState<Record<string, { status: string; owner: string }>>({});

  const rows = useMemo(() => {
    return items.map((i) => {
      const o = local[i.fingerprint];
      return {
        ...i,
        status: o?.status ?? i.status,
        owner: o?.owner ?? i.owner,
      };
    });
  }, [items, local]);

  async function save(fp: string, status: string, owner: string) {
    setPending((p) => ({ ...p, [fp]: true }));
    try {
      await updateIssue({ fingerprint: fp, status, owner });
    } finally {
      setPending((p) => ({ ...p, [fp]: false }));
    }
  }

  return (
    <div className={styles.tableWrap}>
      <table className={styles.table} style={{ minWidth: 1200 }}>
        <thead>
          <tr>
            <th style={{ width: 110 }}>Severity</th>
            <th>Title</th>
            <th style={{ width: 240 }}>Asset</th>
            <th style={{ width: 170 }}>Status</th>
            <th style={{ width: 200 }}>Owner</th>
            <th style={{ width: 160 }}>Age</th>
            <th style={{ width: 160 }}>Last seen</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((i) => {
            const sev = severityLabel(i.severity || 0);
            const isPending = pending[i.fingerprint];

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
                </td>
                <td>
                  <select
                    className={styles.select}
                    value={i.status}
                    disabled={isPending}
                    onChange={async (e) => {
                      const next = e.target.value;
                      setLocal((s) => ({ ...s, [i.fingerprint]: { status: next, owner: i.owner } }));
                      await save(i.fingerprint, next, i.owner);
                    }}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <input
                    className={styles.input}
                    value={i.owner || ""}
                    disabled={isPending}
                    placeholder="Team / BU"
                    onChange={(e) => setLocal((s) => ({ ...s, [i.fingerprint]: { status: i.status, owner: e.target.value } }))}
                    onBlur={async (e) => {
                      const nextOwner = e.target.value;
                      await save(i.fingerprint, i.status, nextOwner);
                    }}
                  />
                  {isPending ? <div className={styles.meta}>Saving…</div> : null}
                </td>
                <td>
                  <div style={{ fontWeight: 700 }}>{Math.max(0, Math.floor((Date.now() / 1000 - (i.first_seen_ts || 0)) / 86400))}d</div>
                  <div className={styles.meta}>
                    Since {new Date((i.first_seen_ts || 0) * 1000).toLocaleDateString()}
                  </div>
                  {i.reopened_count ? <div className={styles.meta}>Reopened: {i.reopened_count}</div> : null}
                </td>
                <td>
                  <Link className={styles.actionLink} href={`/runs/${i.last_run_id}`}>
                    #{i.last_run_id}
                  </Link>
                  <div className={styles.meta}>{new Date((i.last_seen_ts || 0) * 1000).toLocaleString()}</div>
                  {i.status_updated_ts ? <div className={styles.meta}>Status updated {new Date(i.status_updated_ts * 1000).toLocaleDateString()}</div> : null}
                </td>
              </tr>
            );
          })}
          {rows.length === 0 ? (
            <tr>
              <td colSpan={7} className={styles.meta}>
                No issues yet.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
