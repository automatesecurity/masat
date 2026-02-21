import Link from "next/link";
import { ReactNode } from "react";
import styles from "./appShell.module.css";

export default function AppShell({
  active,
  title,
  subtitle,
  pills,
  children,
}: {
  active: "scan" | "runs";
  title: string;
  subtitle?: string;
  pills?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.logo} />
          <div className={styles.brandText}>
            <div className={styles.brandName}>MASAT</div>
            <div className={styles.brandSub}>Attack surface signals</div>
          </div>
        </div>

        <nav className={styles.nav} aria-label="Primary">
          <Link
            className={`${styles.navItem} ${active === "scan" ? styles.navItemActive : ""}`}
            href="/"
          >
            Scan
          </Link>
          <Link
            className={`${styles.navItem} ${active === "runs" ? styles.navItemActive : ""}`}
            href="/runs"
          >
            Runs
          </Link>
        </nav>
      </aside>

      <main className={styles.content}>
        <div className={styles.topbar}>
          <div className={styles.pageTitle}>
            <h1 className={styles.title}>{title}</h1>
            {subtitle ? <p className={styles.subtitle}>{subtitle}</p> : null}
          </div>

          {pills ? <div className={styles.pills}>{pills}</div> : null}
        </div>

        <div className={styles.grid}>{children}</div>
      </main>
    </div>
  );
}
