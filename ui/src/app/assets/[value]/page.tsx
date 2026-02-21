import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchAssetDetail } from "@/lib/masatApi";
import Link from "next/link";

export const dynamic = "force-dynamic";

export default async function AssetDetailPage({ params }: { params: Promise<{ value: string }> }) {
  const { value } = await params;
  const decoded = decodeURIComponent(value);

  const d = await fetchAssetDetail(decoded).catch(() => null);

  const title = decoded;

  return (
    <AppShell
      active="assets"
      title={title}
      subtitle="Asset details: ownership metadata + latest scan evidence."
      pills={
        d?.latestRun ? (
          <>
            <span className={styles.pill}>Latest run: #{d.latestRun.id}</span>
            <span className={styles.pill}>{new Date(d.latestRun.ts * 1000).toLocaleString()}</span>
            <span className={styles.pill}>Ports: {d.openPorts?.length || 0}</span>
            <span className={styles.pill}>Findings: {d.runDetail?.findings?.length || 0}</span>
          </>
        ) : (
          <>
            <span className={styles.pill}>No runs yet</span>
          </>
        )
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Asset</div>
          <div className={styles.meta}>From local inventory (if imported).</div>
        </div>

        {d?.asset ? (
          <div className={styles.kv} style={{ fontFamily: "var(--font-sans)" }}>
            <div className={styles.meta}>
              <strong>Kind:</strong> {d.asset.kind}
            </div>
            <div className={styles.meta}>
              <strong>Owner:</strong> {d.asset.owner || "—"}
            </div>
            <div className={styles.meta}>
              <strong>Environment:</strong> {d.asset.environment || "—"}
            </div>
            <div className={styles.meta}>
              <strong>Tags:</strong> {(d.asset.tags || []).join(", ") || "—"}
            </div>
          </div>
        ) : (
          <div className={styles.meta}>
            This asset is not in the inventory yet. You can still scan it.
          </div>
        )}

        <div className={styles.actions} style={{ marginTop: 12 }}>
          <Link className={styles.actionLink} href={`/scan?target=${encodeURIComponent(decoded)}`}>
            Scan this asset
          </Link>
          <Link className={styles.actionLink} href="/assets">
            Back to assets
          </Link>
          {d?.latestRun ? (
            <Link className={styles.actionLink} href={`/runs/${d.latestRun.id}`}>
              View latest run
            </Link>
          ) : null}
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Exposure</div>
          <div className={styles.meta}>Open ports extracted from latest scan evidence.</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 140 }}>Port</th>
                <th style={{ width: 140 }}>Service</th>
                <th>Version</th>
              </tr>
            </thead>
            <tbody>
              {(d?.openPorts || []).map((p) => (
                <tr key={p.port}>
                  <td>
                    <strong>{p.port}</strong>
                  </td>
                  <td className={styles.meta}>{p.service || "—"}</td>
                  <td className={styles.meta}>{p.version || "—"}</td>
                </tr>
              ))}
              {!d?.latestRun ? (
                <tr>
                  <td colSpan={3} className={styles.meta}>
                    No scan evidence yet. Run a scan to enumerate exposures.
                  </td>
                </tr>
              ) : null}
              {d?.latestRun && (d.openPorts?.length || 0) === 0 ? (
                <tr>
                  <td colSpan={3} className={styles.meta}>
                    No open ports detected in the latest run (or nmap results not present).
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Findings</div>
          <div className={styles.meta}>Normalized findings from the latest run (if available).</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 84 }}>Sev</th>
                <th>Title</th>
                <th style={{ width: 220 }}>Category</th>
                <th style={{ width: 160 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(d?.runDetail?.findings || []).slice(0, 200).map((f, idx) => (
                <tr key={`${f.title}-${idx}`}>
                  <td>
                    <span className={styles.badge}>{f.severity}</span>
                  </td>
                  <td>
                    <strong>{f.title}</strong>
                    <div className={styles.meta}>{f.details}</div>
                  </td>
                  <td className={styles.meta}>{f.category}</td>
                  <td className={styles.meta}>{f.remediation}</td>
                </tr>
              ))}
              {!d?.latestRun ? (
                <tr>
                  <td colSpan={4} className={styles.meta}>
                    No scan evidence yet.
                  </td>
                </tr>
              ) : null}
              {d?.latestRun && (d.runDetail?.findings?.length || 0) === 0 ? (
                <tr>
                  <td colSpan={4} className={styles.meta}>
                    No findings in latest run.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        {d?.latestRun && (d.runDetail?.findings?.length || 0) > 200 ? (
          <div className={styles.meta} style={{ marginTop: 10 }}>
            Showing first 200 findings. View the run for full details.
          </div>
        ) : null}
      </section>
    </AppShell>
  );
}
