import styles from "./appShell.module.css";

function pct(n: number, total: number) {
  if (!total) return 0;
  return Math.round((n / total) * 100);
}

export default function SeverityBar({
  buckets,
}: {
  buckets: { critical: number; high: number; medium: number; low: number; info: number };
}) {
  const total =
    (buckets.critical || 0) + (buckets.high || 0) + (buckets.medium || 0) + (buckets.low || 0) + (buckets.info || 0);

  return (
    <div className={styles.kv} style={{ fontFamily: "var(--font-sans)", background: "rgba(255,255,255,0.03)" }}>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
        <div className={styles.sectionTitle} style={{ margin: 0 }}>
          Findings by severity
        </div>
        <div className={styles.meta}>{total} total</div>
      </div>
      <div style={{ display: "flex", height: 10, borderRadius: 999, overflow: "hidden", border: "1px solid var(--border)" }}>
        <div style={{ width: `${pct(buckets.critical, total)}%`, background: "rgba(255,92,92,0.9)" }} />
        <div style={{ width: `${pct(buckets.high, total)}%`, background: "rgba(255,145,145,0.9)" }} />
        <div style={{ width: `${pct(buckets.medium, total)}%`, background: "rgba(255,204,102,0.9)" }} />
        <div style={{ width: `${pct(buckets.low, total)}%`, background: "rgba(51,209,122,0.85)" }} />
        <div style={{ width: `${pct(buckets.info, total)}%`, background: "rgba(255,255,255,0.14)" }} />
      </div>
      <div className={styles.meta} style={{ marginTop: 10 }}>
        Critical: {buckets.critical || 0} · High: {buckets.high || 0} · Medium: {buckets.medium || 0} · Low: {buckets.low || 0} · Info: {buckets.info || 0}
      </div>
    </div>
  );
}
