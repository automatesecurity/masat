"use client";

import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import { useMemo, useState } from "react";

type SeedAsset = { hostname: string; ips: string[]; source: string };

type SeedResponse = {
  domain: string;
  assets: SeedAsset[];
  stored: number;
};

function normalizeDomain(input: string) {
  const raw = input.trim();
  if (!raw) return "";

  // Accept: domain.com, http(s)://domain.com, domain.com/path
  try {
    if (raw.startsWith("http://") || raw.startsWith("https://")) {
      return new URL(raw).hostname;
    }

    // URL() requires a scheme; use https as a dummy.
    const u = new URL(`https://${raw}`);
    return u.hostname;
  } catch {
    return raw.replace(/\s+/g, "");
  }
}

export default function SeedPage() {
  const [domainInput, setDomainInput] = useState("");
  const [useCt, setUseCt] = useState(true);
  const [useCommon, setUseCommon] = useState(true);
  const [resolve, setResolve] = useState(true);
  const [maxHosts, setMaxHosts] = useState(200);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SeedResponse | null>(null);

  const domain = useMemo(() => normalizeDomain(domainInput), [domainInput]);

  async function runSeed() {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch("/api/seed", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          domain,
          use_ct: useCt,
          use_common: useCommon,
          resolve,
          max_hosts: maxHosts,
        }),
      });

      const data: unknown = await res.json().catch(() => null);
      if (!res.ok) {
        const msg =
          typeof data === "object" && data && "error" in data
            ? String((data as { error?: unknown }).error)
            : `Seed failed: ${res.status}`;
        setError(msg);
        return;
      }

      setResult(data as SeedResponse);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell
      active="seed"
      title="Seeding"
      subtitle="Start with a root domain and automatically discover candidate assets for monitoring."
      pills={
        result ? (
          <>
            <span className={styles.pill}>Discovered: {result.assets.length}</span>
            <span className={styles.pill}>Stored: {result.stored}</span>
          </>
        ) : null
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Seed wizard</div>
          <div className={styles.meta}>Domain → discover → store assets</div>
        </div>

        <div className={styles.form}>
          <label className={styles.label}>
            Domain
            <span className={styles.hint}>Accepts domain.com or https://domain.com</span>
            <input
              className={styles.input}
              placeholder="example.com"
              value={domainInput}
              onChange={(e) => setDomainInput(e.target.value)}
            />
          </label>

          <div className={styles.row}>
            <label className={styles.checkbox}>
              <input type="checkbox" checked={useCt} onChange={(e) => setUseCt(e.target.checked)} />
              Certificate mining (CT)
            </label>
            <label className={styles.checkbox}>
              <input type="checkbox" checked={useCommon} onChange={(e) => setUseCommon(e.target.checked)} />
              Common subdomains
            </label>
            <label className={styles.checkbox}>
              <input type="checkbox" checked={resolve} onChange={(e) => setResolve(e.target.checked)} />
              Resolve DNS
            </label>
          </div>

          <label className={styles.label}>
            Max hosts
            <span className={styles.hint}>Safety limit for discovered hostnames</span>
            <input
              className={styles.input}
              type="number"
              min={10}
              max={2000}
              value={maxHosts}
              onChange={(e) => setMaxHosts(Number(e.target.value || 0))}
            />
          </label>

          <div className={styles.row}>
            <button className={styles.button} disabled={!domain || loading} onClick={runSeed} type="button">
              {loading ? "Seeding…" : "Discover assets"}
            </button>
            <div className={styles.meta}>Normalized: <code>{domain || "—"}</code></div>
          </div>

          {error ? <div className={`${styles.meta} ${styles.error}`}>{error}</div> : null}
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Discovered assets</div>
          <div className={styles.meta}>Stored into the local assets inventory on success.</div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Hostname</th>
                <th style={{ width: 160 }}>Source</th>
                <th>IPs</th>
              </tr>
            </thead>
            <tbody>
              {result?.assets?.map((a) => (
                <tr key={`${a.hostname}:${a.source}`}>
                  <td>
                    <strong>{a.hostname}</strong>
                  </td>
                  <td className={styles.meta}>{a.source}</td>
                  <td className={styles.meta}>{a.ips?.length ? a.ips.join(", ") : "—"}</td>
                </tr>
              ))}
              {!result ? (
                <tr>
                  <td colSpan={3} className={styles.meta}>
                    Run seeding to see discovered assets.
                  </td>
                </tr>
              ) : null}
              {result && result.assets.length === 0 ? (
                <tr>
                  <td colSpan={3} className={styles.meta}>
                    No assets discovered. Try enabling CT or common subdomains.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Next</div>
          <div className={styles.meta}>After seeding, go to Assets to review and Scan to run stored scans.</div>
        </div>
        <div className={styles.actions}>
          <a className={styles.actionLink} href="/assets">
            Review assets
          </a>
          <a className={styles.actionLink} href="/scan">
            Run a scan
          </a>
        </div>
      </section>
    </AppShell>
  );
}
