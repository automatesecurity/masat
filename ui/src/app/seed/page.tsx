"use client";

import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type SeedAsset = { hostname: string; ips: string[]; source: string };

type SeedResponse = {
  domain: string;
  assets: SeedAsset[];
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
  const [useLiveTls, setUseLiveTls] = useState(false);
  const [resolve, setResolve] = useState(true);
  const [maxHosts, setMaxHosts] = useState(200);

  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SeedResponse | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [importedCount, setImportedCount] = useState<number | null>(null);

  useEffect(() => {
    if (domainInput) return;
    try {
      const params = new URLSearchParams(window.location.search);
      const d = params.get("domain");
      if (d) setDomainInput(d);
    } catch {
      // ignore
    }
  }, [domainInput]);

  const domain = useMemo(() => normalizeDomain(domainInput), [domainInput]);

  const selectedHostnames = useMemo(
    () => Object.entries(selected).filter(([, v]) => v).map(([k]) => k),
    [selected],
  );

  async function runSeed() {
    setError(null);
    setImportedCount(null);
    setResult(null);
    setSelected({});
    setLoading(true);
    try {
      const res = await fetch("/api/seed", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          domain,
          use_ct: useCt,
          use_common: useCommon,
          use_live_tls: useLiveTls,
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

      const r = data as SeedResponse;
      setResult(r);
      const initial: Record<string, boolean> = {};
      for (const a of r.assets || []) initial[a.hostname] = true;
      setSelected(initial);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  async function importSelected() {
    setError(null);
    setImportedCount(null);
    setImporting(true);
    try {
      const res = await fetch("/api/assets/import", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          assets: selectedHostnames,
          tags: ["seeded"],
        }),
      });

      const data: unknown = await res.json().catch(() => null);
      if (!res.ok) {
        const msg =
          typeof data === "object" && data && "error" in data
            ? String((data as { error?: unknown }).error)
            : `Import failed: ${res.status}`;
        setError(msg);
        return;
      }

      const stored =
        typeof data === "object" && data && "stored" in data ? Number((data as { stored?: unknown }).stored) : null;
      setImportedCount(Number.isFinite(stored) ? stored : selectedHostnames.length);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
    } finally {
      setImporting(false);
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
            <span className={styles.pill}>Selected: {selectedHostnames.length}</span>
            {importedCount !== null ? <span className={styles.pill}>Imported: {importedCount}</span> : null}
          </>
        ) : null
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Seed wizard</div>
          <div className={styles.meta}>Domain → discover → select → import → scan</div>
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
              <input type="checkbox" checked={useLiveTls} onChange={(e) => setUseLiveTls(e.target.checked)} />
              Live TLS cert mining (SAN)
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
              {loading ? "Discovering…" : "Discover assets"}
            </button>
            <div className={styles.meta}>
              Normalized: <code>{domain || "—"}</code>
            </div>
          </div>

          {error ? <div className={`${styles.meta} ${styles.error}`}>{error}</div> : null}
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Discovered assets</div>
          <div className={styles.meta}>Select what you want to import into Assets.</div>
        </div>

        <div className={styles.actions}>
          <button
            type="button"
            className={styles.buttonSecondary}
            disabled={!result || importing || selectedHostnames.length === 0}
            onClick={importSelected}
          >
            {importing ? "Importing…" : `Import selected (${selectedHostnames.length})`}
          </button>
          <a className={styles.actionLink} href={selectedHostnames.length ? `/scan?target=${encodeURIComponent(selectedHostnames[0])}` : "/scan"}>
            Scan a selected asset
          </a>
          <a className={styles.actionLink} href="/assets">
            View asset inventory
          </a>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 44 }} />
                <th>Hostname</th>
                <th style={{ width: 160 }}>Source</th>
                <th>IPs</th>
              </tr>
            </thead>
            <tbody>
              {result?.assets?.map((a) => (
                <tr key={`${a.hostname}:${a.source}`}>
                  <td className={styles.meta}>
                    <input
                      type="checkbox"
                      checked={selected[a.hostname] ?? false}
                      onChange={(e) => setSelected((s) => ({ ...s, [a.hostname]: e.target.checked }))}
                    />
                  </td>
                  <td>
                    <strong>{a.hostname}</strong>
                  </td>
                  <td className={styles.meta}>{a.source}</td>
                  <td className={styles.meta}>{a.ips?.length ? a.ips.join(", ") : "—"}</td>
                </tr>
              ))}
              {!result ? (
                <tr>
                  <td colSpan={4} className={styles.meta}>
                    Run seeding to see discovered assets.
                  </td>
                </tr>
              ) : null}
              {result && result.assets.length === 0 ? (
                <tr>
                  <td colSpan={4} className={styles.meta}>
                    No assets discovered. Try enabling CT, common subdomains, or live TLS mining.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Close the loop</div>
          <div className={styles.meta}>Seed → Assets → Scan → Runs → Changes</div>
        </div>
        <div className={styles.actions}>
          <a className={styles.actionLink} href="/assets">
            Review imported assets
          </a>
          <a className={styles.actionLink} href="/scan">
            Create a stored scan
          </a>
          <Link className={styles.actionLink} href="/runs">
            Browse runs
          </Link>
        </div>
      </section>
    </AppShell>
  );
}
