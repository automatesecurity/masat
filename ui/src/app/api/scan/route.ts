import { redirect } from "next/navigation";

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

export async function POST(req: Request) {
  const form = await req.formData();
  const target = String(form.get("target") || "").trim();
  const scans = String(form.get("scans") || "").trim();
  const smart = form.get("smart") === "1";

  if (!target) {
    redirect(`/?error=${encodeURIComponent("Missing target")}`);
  }

  try {
    const res = await fetch(`${apiBase()}/scan`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        target,
        scans: scans ? scans : null,
        smart,
        store: true,
      }),
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      redirect(`/?error=${encodeURIComponent(`MASAT /scan failed: ${res.status} ${text}`)}`);
    }

    const data: unknown = await res.json();
    const runId = (data as { runId?: number | null } | null)?.runId ?? null;

    if (typeof runId === "number") {
      redirect(`/runs/${runId}`);
    }

    redirect(`/?error=${encodeURIComponent("Scan completed but was not stored (runId missing).")}`);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    redirect(`/?error=${encodeURIComponent(msg)}`);
  }
}
