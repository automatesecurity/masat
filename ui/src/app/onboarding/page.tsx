"use client";

import AppShell from "@/app/_components/AppShell";
import styles from "@/app/_components/appShell.module.css";
import Link from "next/link";
import { useMemo, useState } from "react";

type SeedAsset = { hostname: string; ips: string[]; source: string };

type SeedResponse = {
  domain: string;
  assets: SeedAsset[];
};

type Step = 1 | 2 | 3 | 4;

function normalizeSeedTarget(input: string) {
  const raw = input.trim();
  if (!raw) return "";

  // Accept domain.com, IP, http(s)://domain.com
  try {
    if (raw.startsWith("http://") || raw.startsWith("https://")) return new URL(raw).hostname;
    const u = new URL(`https://${raw}`);
    return u.hostname;
  } catch {
    return raw.replace(/\s+/g, "");
  }
}

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>(1);

  // Step 1
  const [seedInput, setSeedInput] = useState("");
  const [owner, setOwner] = useState("");
  const [environment, setEnvironment] = useState("prod");

  // Step 2
  const [useCt, setUseCt] = useState(true);
  const [useCommon, setUseCommon] = useState(true);
  const [useLiveTls, setUseLiveTls] = useState(false);
  const [resolve, setResolve] = useState(true);
  const [maxHosts, setMaxHosts] = useState(200);

  const [discovering, setDiscovering] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [seedResult, setSeedResult] = useState<SeedResponse | null>(null);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [importedCount, setImportedCount] = useState<number | null>(null);

  const seedTarget = useMemo(() => normalizeSeedTarget(seedInput), [seedInput]);

  const selectedHostnames = useMemo(
    () => Object.entries(selected).filter(([, v]) => v).map(([k]) => k),
    [selected],
  );

  async function discover() {
    setError(null);
    setImportedCount(null);
    setSeedResult(null);
    setSelected({});
    setDiscovering(true);

    try {
      const res = await fetch("/api/seed", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          domain: seedTarget,
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
            : `Discovery failed: ${res.status}`;
        setError(msg);
        return;
      }

      const r = data as SeedResponse;
      setSeedResult(r);

      const initial: Record<string, boolean> = {};
      for (const a of r.assets || []) initial[a.hostname] = true;
      setSelected(initial);

      setStep(3);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setDiscovering(false);
    }
  }

  async function importInScope() {
    setError(null);
    setImportedCount(null);
    setImporting(true);

    try {
      if (!selectedHostnames.length) {
        setError("Select at least one in-scope asset to continue.");
        return;
      }

      const res = await fetch("/api/assets/import", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          assets: selectedHostnames,
          tags: ["owned", "in-scope", "seeded"],
          owner,
          environment,
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
      setStep(4);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setImporting(false);
    }
  }

  function stepLabel(s: Step) {
    if (s === 1) return "Seed target";
    if (s === 2) return "Discovery";
    if (s === 3) return "Confirm in-scope assets";
    return "Start monitoring";
  }

  return (
    <AppShell
      active="dashboard"
      title="Onboarding"
      subtitle="Guided setup: seed → discover → confirm owned/in-scope assets → begin monitoring."
      pills={
        <>
          <span className={styles.pill}>Step {step} / 4</span>
          <span className={styles.pill}>{stepLabel(step)}</span>
        </>
      }
    >
      <section className={styles.card}>
        <div className={styles.cardHeader}>
          <div className={styles.sectionTitle}>Setup wizard</div>
          <div className={styles.meta}>You must explicitly add at least one in-scope asset to continue.</div>
        </div>

        {error ? <div className={`${styles.meta} ${styles.error}`}>{error}</div> : null}

        {/* Step 1 */}
        <div className={styles.form} style={{ marginTop: 10 }}>
          <label className={styles.label}>
            Seed (domain or IP)
            <span className={styles.hint}>Accepts example.com, https://example.com, or an IP</span>
            <input
              className={styles.input}
              placeholder="example.com"
              value={seedInput}
              onChange={(e) => setSeedInput(e.target.value)}
            />
          </label>

          <div className={styles.row}>
            <label className={styles.label} style={{ minWidth: 260, flex: 1 }}>
              Owner
              <span className={styles.hint}>Optional, but recommended for enterprise workflows</span>
              <input className={styles.input} placeholder="Team / Business unit" value={owner} onChange={(e) => setOwner(e.target.value)} />
            </label>

            <label className={styles.label} style={{ minWidth: 220 }}>
              Environment
              <span className={styles.hint}>Used for reporting & filtering</span>
              <select className={styles.select} value={environment} onChange={(e) => setEnvironment(e.target.value)}>
                <option value="prod">prod</option>
                <option value="staging">staging</option>
                <option value="dev">dev</option>
                <option value="unspecified">unspecified</option>
              </select>
            </label>
          </div>

          <div className={styles.actions}>
            <button
              className={styles.buttonSecondary}
              type="button"
              onClick={() => {
                setStep(2);
                setError(null);
              }}
              disabled={!seedTarget}
            >
              Next
            </button>
            <div className={styles.meta}>
              Normalized: <code>{seedTarget || "—"}</code>
            </div>
          </div>
        </div>
      </section>

      {/* Step 2 */}
      {step >= 2 ? (
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.sectionTitle}>Discovery</div>
            <div className={styles.meta}>Start with passive sources; expand iteratively.</div>
          </div>

          <div className={styles.form}>
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
              <span className={styles.hint}>Safety cap during onboarding</span>
              <input
                className={styles.input}
                type="number"
                min={10}
                max={2000}
                value={maxHosts}
                onChange={(e) => setMaxHosts(Number(e.target.value || 0))}
              />
            </label>

            <div className={styles.actions}>
              <button className={styles.button} type="button" onClick={discover} disabled={!seedTarget || discovering}>
                {discovering ? "Discovering…" : "Run discovery"}
              </button>
              <button className={styles.buttonSecondary} type="button" onClick={() => setStep(1)} disabled={discovering}>
                Back
              </button>
            </div>
          </div>
        </section>
      ) : null}

      {/* Step 3 */}
      {step >= 3 ? (
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.sectionTitle}>Confirm in-scope assets</div>
            <div className={styles.meta}>Deselect anything you don’t own or don’t want to monitor.</div>
          </div>

          <div className={styles.actions}>
            <button
              className={styles.button}
              type="button"
              onClick={importInScope}
              disabled={!seedResult || importing || selectedHostnames.length === 0}
            >
              {importing ? "Importing…" : `Add ${selectedHostnames.length} in-scope assets`}
            </button>
            <button
              className={styles.buttonSecondary}
              type="button"
              onClick={() => setStep(2)}
              disabled={importing}
            >
              Back
            </button>
            <Link className={styles.actionLink} href="/assets">
              View inventory
            </Link>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th style={{ width: 44 }} />
                  <th>Hostname</th>
                  <th style={{ width: 140 }}>Source</th>
                  <th>IPs</th>
                </tr>
              </thead>
              <tbody>
                {seedResult?.assets?.map((a) => (
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
                {!seedResult ? (
                  <tr>
                    <td colSpan={4} className={styles.meta}>
                      Run discovery to see candidate assets.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {/* Step 4 */}
      {step >= 4 ? (
        <section className={styles.card}>
          <div className={styles.cardHeader}>
            <div className={styles.sectionTitle}>Onboarding complete</div>
            <div className={styles.meta}>Next: run your first stored scans and start tracking drift.</div>
          </div>

          <div className={styles.actions}>
            <span className={styles.pill}>Imported: {importedCount ?? selectedHostnames.length}</span>
            <Link className={styles.actionLink} href="/assets">
              Review assets
            </Link>
            <Link
              className={styles.actionLink}
              href={selectedHostnames[0] ? `/scan?target=${encodeURIComponent(selectedHostnames[0])}` : "/scan"}
            >
              Run first scan
            </Link>
            <Link className={styles.actionLink} href="/changes">
              View drift
            </Link>
          </div>
        </section>
      ) : null}
    </AppShell>
  );
}
