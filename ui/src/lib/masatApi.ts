export type Scan = { id: string; description?: string };
export type RunRow = { id: number; ts: number; target: string; scans: string[] };

export type RunDetail = RunRow & {
  // API shape from GET /runs/{id}
  results: unknown;
  findings: Finding[];
};

export type Finding = {
  category: string;
  title: string;
  severity: number;
  remediation: string;
  details: string;
};

export type ScanResponse = {
  runId: number | null;
  target: string;
  scans: string[];
  // API returns a nested dict; keep it as unknown for safety.
  results: unknown;
  findings: Finding[];
};

function baseUrl() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function fetchScans(): Promise<Scan[]> {
  const res = await fetch(`${baseUrl()}/scans`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /scans failed: ${res.status}`);
  const data = await res.json();
  return data.scans || [];
}

export async function fetchRuns(limit = 20): Promise<RunRow[]> {
  const res = await fetch(`${baseUrl()}/runs?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /runs failed: ${res.status}`);
  const data = await res.json();
  return data.runs || [];
}

export async function fetchRun(id: number): Promise<RunDetail> {
  const res = await fetch(`${baseUrl()}/runs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /runs/${id} failed: ${res.status}`);
  const data = await res.json();
  return data.run as RunDetail;
}

export async function runScan(params: {
  target: string;
  scans?: string;
  smart?: boolean;
  store?: boolean;
}): Promise<ScanResponse> {
  const res = await fetch(`${baseUrl()}/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      target: params.target,
      scans: params.scans ?? null,
      smart: params.smart ?? true,
      store: params.store ?? true,
    }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`MASAT /scan failed: ${res.status} ${text}`);
  }
  return await res.json();
}
