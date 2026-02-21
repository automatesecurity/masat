import styles from "./ui.module.css";

import InfoIcon from "./InfoIcon";

export function KpiRow({
  items,
}: {
  items: {
    label: string;
    value: string | number;
    meta?: string;
    infoTitle?: string;
    infoBody?: string;
  }[];
}) {
  return (
    <div className={styles.kpiGrid}>
      {items.map((k) => (
        <div key={k.label} className={styles.kpi}>
          {k.infoBody ? (
            <div className={styles.kpiTopRight}>
              <details>
                <summary aria-label="Info">
                  <InfoIcon />
                </summary>
                <div className={styles.tooltip} role="note">
                  <div className={styles.tooltipTitle}>{k.infoTitle || "Info"}</div>
                  <div className={styles.tooltipBody}>{k.infoBody}</div>
                </div>
              </details>
            </div>
          ) : null}

          <div className={styles.kpiLabel}>{k.label}</div>
          <div className={styles.kpiValue}>{k.value}</div>
          {k.meta ? <div className={styles.kpiMeta}>{k.meta}</div> : null}
        </div>
      ))}
    </div>
  );
}
