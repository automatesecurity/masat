import Link from "next/link";
import { ReactNode } from "react";
import styles from "./appShell.module.css";
import { Icon } from "./icons";

export default function AppShell({
  active,
  title,
  subtitle,
  pills,
  children,
}: {
  active: "dashboard" | "changes" | "scan" | "runs" | "assets" | "seed" | "issues";
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
            className={`${styles.navItem} ${active === "dashboard" ? styles.navItemActive : ""}`}
            href="/"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="dashboard" />
              Dashboard
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "changes" ? styles.navItemActive : ""}`}
            href="/changes"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="changes" />
              Changes
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "scan" ? styles.navItemActive : ""}`}
            href="/scan"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="scan" />
              Scan
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "seed" ? styles.navItemActive : ""}`}
            href="/seed"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="seed" />
              Seeding
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "runs" ? styles.navItemActive : ""}`}
            href="/runs"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="runs" />
              Runs
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "assets" ? styles.navItemActive : ""}`}
            href="/assets"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="assets" />
              Assets
            </span>
          </Link>
          <Link
            className={`${styles.navItem} ${active === "issues" ? styles.navItemActive : ""}`}
            href="/issues"
          >
            <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              <Icon name="changes" />
              Issues
            </span>
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
