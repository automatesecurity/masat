import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { fetchAssets, type AssetRow } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

function uniq(items: string[]) {
  return Array.from(new Set(items)).sort();
}

function matches(asset: AssetRow, q: string) {
  const s = q.toLowerCase().trim();
  if (!s) return true;
  return (
    asset.value.toLowerCase().includes(s) ||
    asset.kind.toLowerCase().includes(s) ||
    (asset.owner || "").toLowerCase().includes(s) ||
    (asset.environment || "").toLowerCase().includes(s) ||
    (asset.tags || []).join(",").toLowerCase().includes(s)
  );
}

export default async function AssetsPage({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};
  const q = typeof sp.q === "string" ? sp.q : "";
  const view = typeof sp.view === "string" ? sp.view : "";

  const assets = await fetchAssets(500).catch(() => []);

  const allTags = uniq(assets.flatMap((a) => a.tags || []));
  const allEnvs = uniq(assets.map((a) => a.environment || "").filter(Boolean));

  // Very simple saved views (server-side presets via ?view=...)
  const viewFilter = (a: AssetRow) => {
    if (view === "prod") return (a.environment || "").toLowerCase() === "prod";
    if (view === "internet") return (a.tags || []).map((t) => t.toLowerCase()).includes("internet-facing");
    return true;
  };

  const filtered = assets.filter((a) => viewFilter(a)).filter((a) => matches(a, q));

  return (
    <AppShell
      active="assets"
      title="Assets"
      subtitle="Local asset inventory (EASM). Import via CLI, browse/filter here."
      pills={
        <>
          <span className={styles.pill}>Total: {assets.length}</span>
          <span className={styles.pill}>Filtered: {filtered.length}</span>
          <span className={styles.pill}>Tags: {allTags.length}</span>
          <span className={styles.pill}>Envs: {allEnvs.length}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Saved views</div>
          <div className={styles.meta}>Lightweight presets (we can add user-saved views next)</div>
        </div>

        <div className={styles.actions}>
          <a className={styles.actionLink} href="/assets">
            All assets
          </a>
          <a className={styles.actionLink} href="/assets?view=prod">
            Prod
          </a>
          <a className={styles.actionLink} href="/assets?view=internet">
            Internet-facing
          </a>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Search</div>
          <div className={styles.meta}>Filter by value, tag, owner, or environment</div>
        </div>

        <form className={styles.row} method="GET">
          <input className={styles.input} name="q" placeholder="Search..." defaultValue={q} />
          {view ? <input type="hidden" name="view" value={view} /> : null}
          <button className={styles.buttonSecondary} type="submit">
            Apply
          </button>
        </form>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Inventory</div>
          <div className={styles.meta}>Imported from `masat assets import`</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 90 }}>Kind</th>
                <th>Asset</th>
                <th style={{ width: 140 }}>Environment</th>
                <th style={{ width: 160 }}>Owner</th>
                <th>Tags</th>
                <th style={{ width: 140 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={`${a.kind}:${a.value}`}>
                  <td className={styles.meta}>{a.kind}</td>
                  <td>
                    <strong>{a.value}</strong>
                  </td>
                  <td className={styles.meta}>{a.environment || ""}</td>
                  <td className={styles.meta}>{a.owner || ""}</td>
                  <td className={styles.meta}>{(a.tags || []).join(", ")}</td>
                  <td>
                    <div className={styles.actions}>
                      <a className={styles.actionLink} href={`/scan?target=${encodeURIComponent(a.value)}`}>
                        Scan
                      </a>
                      <a className={styles.actionLink} href={`/seed?domain=${encodeURIComponent(a.value)}`}>
                        Seed
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className={styles.meta}>
                    No assets found. Import some with: <code>masat assets import assets.csv</code>
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
