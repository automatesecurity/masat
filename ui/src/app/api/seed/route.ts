import { NextResponse } from "next/server";

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as
    | {
        domain?: string;
        use_ct?: boolean;
        use_common?: boolean;
        resolve?: boolean;
        max_hosts?: number;
      }
    | null;

  const domain = String(body?.domain || "").trim();
  if (!domain) {
    return NextResponse.json({ error: "Missing domain" }, { status: 400 });
  }

  const res = await fetch(`${apiBase()}/seed`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      domain,
      use_ct: body?.use_ct ?? true,
      use_common: body?.use_common ?? true,
      resolve: body?.resolve ?? true,
      max_hosts: body?.max_hosts ?? 500,
      store_assets: true,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return NextResponse.json({ error: `MASAT /seed failed: ${res.status} ${text}` }, { status: 502 });
  }

  const data = await res.json();
  return NextResponse.json(data);
}
