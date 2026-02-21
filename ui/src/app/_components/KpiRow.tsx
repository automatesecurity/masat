import styles from "./ui.module.css";

export function KpiRow({
  items,
}: {
  items: { label: string; value: string | number; meta?: string }[];
}) {
  return (
    <div className={styles.kpiGrid}>
      {items.map((k) => (
        <div key={k.label} className={styles.kpi}>
          <div className={styles.kpiLabel}>{k.label}</div>
          <div className={styles.kpiValue}>{k.value}</div>
          {k.meta ? <div className={styles.kpiMeta}>{k.meta}</div> : null}
        </div>
      ))}
    </div>
  );
}
