import { NextResponse } from "next/server";

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function POST(req: Request) {
  const body = (await req.json().catch(() => null)) as
    | {
        fingerprint?: string;
        status?: string;
        owner?: string;
      }
    | null;

  const fingerprint = String(body?.fingerprint || "").trim();
  if (!fingerprint) {
    return NextResponse.json({ error: "Missing fingerprint" }, { status: 400 });
  }

  const res = await fetch(`${apiBase()}/issues/update`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      fingerprint,
      status: body?.status ?? null,
      owner: body?.owner ?? null,
    }),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    return NextResponse.json({ error: `MASAT /issues/update failed: ${res.status} ${text}` }, { status: 502 });
  }

  const data = await res.json().catch(() => ({}));
  return NextResponse.json(data);
}
