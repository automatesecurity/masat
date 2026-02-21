import { NextResponse } from "next/server";

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as
    | {
        assets?: string[];
        tags?: string[];
        owner?: string;
        environment?: string;
      }
    | null;

  const assets = Array.isArray(body?.assets) ? body?.assets : [];
  if (!assets.length) {
    return NextResponse.json({ error: "No assets provided" }, { status: 400 });
  }

  const res = await fetch(`${apiBase()}/assets/import`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      assets,
      tags: body?.tags ?? ["seeded"],
      owner: body?.owner ?? "",
      environment: body?.environment ?? "",
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return NextResponse.json({ error: `MASAT /assets/import failed: ${res.status} ${text}` }, { status: 502 });
  }

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data);
}
