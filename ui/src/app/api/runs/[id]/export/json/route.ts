function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const runId = Number(id);
  if (!Number.isFinite(runId)) {
    return new Response("Invalid run id", { status: 400 });
  }

  const res = await fetch(`${apiBase()}/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) {
    return new Response(await res.text().catch(() => "Not found"), { status: res.status });
  }

  const data = await res.json();

  return new Response(JSON.stringify(data, null, 2), {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "content-disposition": `attachment; filename=masat-run-${runId}.json`,
    },
  });
}
