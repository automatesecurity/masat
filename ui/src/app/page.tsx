import { runScan, fetchRuns } from "@/lib/masatApi";

export const dynamic = "force-dynamic";

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
}) {
  const sp = (await searchParams) || {};
  const target = typeof sp.target === "string" ? sp.target : "";
  const scans = typeof sp.scans === "string" ? sp.scans : "";
  const smart = sp.smart === "0" ? false : true;

  let scanResult: Awaited<ReturnType<typeof runScan>> | null = null;
  let scanError: string | null = null;

  if (target) {
    try {
      scanResult = await runScan({
        target,
        scans: scans || undefined,
        smart,
        store: true,
      });
    } catch (e: unknown) {
      scanError = e instanceof Error ? e.message : String(e);
    }
  }

  const runs = await fetchRuns(20).catch(() => []);

  return (
    <main style={{ maxWidth: 980, margin: "40px auto", padding: "0 16px" }}>
      <h1>MASAT Portal (Prototype)</h1>
      <p style={{ color: "#444" }}>
        Enter a URL, domain, IP, or CIDR. This UI calls the MASAT FastAPI server.
      </p>

      <form method="GET" style={{ display: "grid", gap: 12, marginTop: 16 }}>
        <label>
          Target
          <input
            name="target"
            placeholder="https://example.com"
            defaultValue={target}
            style={{ width: "100%", padding: 10, marginTop: 6 }}
          />
        </label>

        <label>
          Scans (comma-separated, optional)
          <input
            name="scans"
            placeholder="web,tls,nuclei"
            defaultValue={scans}
            style={{ width: "100%", padding: 10, marginTop: 6 }}
          />
        </label>

        <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input type="checkbox" name="smart" value="1" defaultChecked={smart} />
          Smart mode (auto-select scans)
        </label>

        <button type="submit" style={{ padding: "10px 14px", width: 140 }}>
          Scan
        </button>
      </form>

      {scanError && (
        <div style={{ marginTop: 24, padding: 12, border: "1px solid #c33", color: "#c33" }}>
          <strong>Scan failed:</strong> {scanError}
        </div>
      )}

      {scanResult && (
        <section style={{ marginTop: 24 }}>
          <h2>Results</h2>
          <p>
            <strong>Target:</strong> {scanResult.target} | <strong>Run ID:</strong>{" "}
            {String(scanResult.runId)}
          </p>
          <p>
            <strong>Scans:</strong> {scanResult.scans?.join(", ")}
          </p>

          <h3>Findings</h3>
          <pre style={{ whiteSpace: "pre-wrap", background: "#f6f6f6", padding: 12 }}>
            {JSON.stringify(scanResult.findings, null, 2)}
          </pre>
        </section>
      )}

      <section style={{ marginTop: 28 }}>
        <h2>Recent runs</h2>
        <p style={{ color: "#666" }}>
          Stored by the API server in SQLite (default: ~/.masat/masat.db).
        </p>
        <ul>
          {runs.map((r) => (
            <li key={r.id}>
              #{r.id} — {r.target} — {new Date(r.ts * 1000).toLocaleString()} — [{r.scans.join(", ")}]
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
