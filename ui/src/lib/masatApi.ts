export type Scan = { id: string; description?: string };
export type RunRow = { id: number; ts: number; target: string; scans: string[] };

export type AssetRow = {
  kind: string;
  value: string;
  tags: string[];
  owner: string;
  environment: string;
  ts: number;
};

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

export type DashboardMetrics = {
  ts: number;
  total_assets: number;
  assets_by_env: Record<string, number>;
  total_runs: number;
  runs_24h: number;
  runs_7d: number;
  latest_run_ts: number | null;
  targets_seen: number;
  assets_scanned_30d: number;
  coverage_30d_pct: number;
  findings_by_sev: Record<string, number>;
  open_ports_total: number;
  score: number;
  grade: string;
  score_categories: Record<string, number>;
  score_weights: Record<string, number>;
};

export type DashboardSnapshot = {
  ts: number;
  score: number;
  score_categories: Record<string, number>;
  open_ports_total: number;
  findings_by_sev: Record<string, number>;
  coverage_30d_pct: number;
};

export type DashboardResponse = {
  metrics: DashboardMetrics;
  trend: {
    asof7d: DashboardSnapshot | null;
    asof30d: DashboardSnapshot | null;
    asof90d: DashboardSnapshot | null;
  };
  narrative: string[];
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

export type Page<T> = { items: T[]; total: number; limit: number; offset: number };

export async function fetchRunsPage(params?: { limit?: number; offset?: number }): Promise<Page<RunRow>> {
  const limit = params?.limit ?? 30;
  const offset = params?.offset ?? 0;

  const res = await fetch(`${baseUrl()}/runs?limit=${limit}&offset=${offset}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /runs failed: ${res.status}`);
  const data = await res.json();
  return {
    items: data.runs || [],
    total: Number(data.total || 0),
    limit: Number(data.limit || limit),
    offset: Number(data.offset || offset),
  };
}

export async function fetchAssetsPage(params?: { limit?: number; offset?: number }): Promise<Page<AssetRow>> {
  const limit = params?.limit ?? 30;
  const offset = params?.offset ?? 0;

  const res = await fetch(`${baseUrl()}/assets?limit=${limit}&offset=${offset}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /assets failed: ${res.status}`);
  const data = await res.json();
  return {
    items: data.assets || [],
    total: Number(data.total || 0),
    limit: Number(data.limit || limit),
    offset: Number(data.offset || offset),
  };
}

// Back-compat helpers
export async function fetchRuns(limit = 20): Promise<RunRow[]> {
  return (await fetchRunsPage({ limit, offset: 0 })).items;
}

export async function fetchAssets(limit = 200): Promise<AssetRow[]> {
  return (await fetchAssetsPage({ limit, offset: 0 })).items;
}

export async function fetchRun(id: number): Promise<RunDetail> {
  const res = await fetch(`${baseUrl()}/runs/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /runs/${id} failed: ${res.status}`);
  const data = await res.json();
  return data.run as RunDetail;
}

export async function fetchDashboard(): Promise<DashboardResponse> {
  const res = await fetch(`${baseUrl()}/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /dashboard failed: ${res.status}`);
  return (await res.json()) as DashboardResponse;
}

export type AssetDetail = {
  asset: AssetRow | null;
  latestRun: RunRow | null;
  runDetail: RunDetail | null;
  openPorts: { port: string; service: string; version: string }[];
};

export type ExposedPort = { port: string; assets: number };

export async function fetchAssetDetail(value: string): Promise<AssetDetail> {
  const res = await fetch(`${baseUrl()}/asset?value=${encodeURIComponent(value)}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /asset failed: ${res.status}`);
  return (await res.json()) as AssetDetail;
}

export async function fetchTopExposedPorts(limit = 10): Promise<ExposedPort[]> {
  const res = await fetch(`${baseUrl()}/exposure/ports?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`MASAT /exposure/ports failed: ${res.status}`);
  const data = await res.json();
  return (data.ports || []) as ExposedPort[];
}

export async function fetchAssetsExposedPage(params: {
  port: string;
  limit?: number;
  offset?: number;
}): Promise<Page<AssetRow>> {
  const limit = params.limit ?? 30;
  const offset = params.offset ?? 0;

  const res = await fetch(
    `${baseUrl()}/assets/exposed?port=${encodeURIComponent(params.port)}&limit=${limit}&offset=${offset}`,
    { cache: "no-store" },
  );
  if (!res.ok) throw new Error(`MASAT /assets/exposed failed: ${res.status}`);
  const data = await res.json();
  return {
    items: data.assets || [],
    total: Number(data.total || 0),
    limit: Number(data.limit || limit),
    offset: Number(data.offset || offset),
  };
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
