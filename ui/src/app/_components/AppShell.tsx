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
    <div className={styles.shellWrap}>
      {/* CSS-only sidebar collapse (no client JS). */}
      <input id="masat-nav-toggle" className={styles.navToggle} type="checkbox" aria-label="Toggle sidebar" />

      <div className={styles.shell}>
        <aside className={styles.sidebar}>
        <div className={styles.brandRow}>
          <div className={styles.brand}>
            <div className={styles.logo} />
            <div className={styles.brandText}>
              <div className={styles.brandName}>MASAT</div>
              <div className={styles.brandSub}>Attack surface signals</div>
            </div>
          </div>

          <label className={styles.collapseBtn} htmlFor="masat-nav-toggle" title="Collapse/expand sidebar" aria-label="Collapse/expand sidebar">
            <span className={styles.collapseGlyph} aria-hidden>
              ◀
            </span>
          </label>
        </div>

        <nav className={styles.nav} aria-label="Primary">
          <Link className={`${styles.navItem} ${active === "dashboard" ? styles.navItemActive : ""}`} href="/">
            <span className={styles.navItemInner}>
              <Icon name="dashboard" />
              <span className={styles.navLabel}>Dashboard</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "changes" ? styles.navItemActive : ""}`} href="/changes">
            <span className={styles.navItemInner}>
              <Icon name="changes" />
              <span className={styles.navLabel}>Changes</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "scan" ? styles.navItemActive : ""}`} href="/scan">
            <span className={styles.navItemInner}>
              <Icon name="scan" />
              <span className={styles.navLabel}>Assess</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "seed" ? styles.navItemActive : ""}`} href="/seed">
            <span className={styles.navItemInner}>
              <Icon name="seed" />
              <span className={styles.navLabel}>Seeding</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "runs" ? styles.navItemActive : ""}`} href="/runs">
            <span className={styles.navItemInner}>
              <Icon name="runs" />
              <span className={styles.navLabel}>Evidence</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "assets" ? styles.navItemActive : ""}`} href="/assets">
            <span className={styles.navItemInner}>
              <Icon name="assets" />
              <span className={styles.navLabel}>Assets</span>
            </span>
          </Link>
          <Link className={`${styles.navItem} ${active === "issues" ? styles.navItemActive : ""}`} href="/issues">
            <span className={styles.navItemInner}>
              <Icon name="changes" />
              <span className={styles.navLabel}>Issues</span>
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

          <div className={styles.pills}>
            {pills}
            <Link className={styles.actionLink} href="/settings">
              Settings
            </Link>
          </div>
        </div>

        <div className={styles.grid}>{children}</div>
        </main>
      </div>
    </div>
  );
}
