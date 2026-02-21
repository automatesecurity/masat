import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { cookies } from "next/headers";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const c = await cookies();
  const persona = c.get("masat_persona")?.value || "analyst";
  const owner = c.get("masat_owner")?.value || "";

  return (
    <AppShell
      active="dashboard"
      title="Settings"
      subtitle="Personalization for demo personas. (No auth yet; stored as cookies in the browser.)"
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Persona</div>
          <div className={styles.meta}>Controls default views and filters.</div>
        </div>

        <form className={styles.form} method="POST" action="/api/settings">
          <label className={styles.label}>
            Persona
            <span className={styles.hint}>Analyst prioritizes issues; Owner focuses on their assets; CISO focuses on score & trend.</span>
            <select className={styles.select} name="persona" defaultValue={persona}>
              <option value="analyst">Risk analyst</option>
              <option value="owner">Asset owner</option>
              <option value="ciso">CISO / Executive</option>
            </select>
          </label>

          <label className={styles.label}>
            Owner / Team
            <span className={styles.hint}>Used to default “my issues” / “my assets” filters when persona = Asset owner.</span>
            <input className={styles.input} name="owner" placeholder="Platform Security" defaultValue={owner} />
          </label>

          <div className={styles.row}>
            <button className={styles.button} type="submit">
              Save
            </button>
          </div>
        </form>
      </section>
    </AppShell>
  );
}
