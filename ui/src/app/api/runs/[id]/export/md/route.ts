type Finding = {
  category?: string;
  title?: string;
  severity?: number;
  details?: string;
  remediation?: string;
};

type RunDetail = {
  id: number;
  ts: number;
  target: string;
  scans: string[];
  findings: Finding[];
};

function apiBase() {
  return process.env.NEXT_PUBLIC_MASAT_API_BASE || "http://127.0.0.1:8000";
}

function sevLabel(sev: number): "High" | "Medium" | "Low" {
  if (sev >= 8) return "High";
  if (sev >= 4) return "Medium";
  return "Low";
}

function toMarkdown(run: RunDetail) {
  const findings = (run.findings || []).slice().sort((a, b) => (b.severity ?? 0) - (a.severity ?? 0));

  const lines: string[] = [];
  lines.push(`# MASAT Run #${run.id}`);
  lines.push("");
  lines.push(`- **Target:** ${run.target}`);
  lines.push(`- **Timestamp:** ${new Date(run.ts * 1000).toISOString()}`);
  lines.push(`- **Scans:** ${(run.scans || []).join(", ") || "(none)"}`);
  lines.push(`- **Findings:** ${findings.length}`);
  lines.push("");

  if (findings.length === 0) {
    lines.push("No findings.");
    lines.push("");
    return lines.join("\n");
  }

  lines.push("## Findings");
  lines.push("");

  findings.forEach((f, idx) => {
    const sev = sevLabel(f.severity ?? 0);
    const title = f.title || "(untitled)";
    const cat = f.category ? ` (${f.category})` : "";

    lines.push(`### ${idx + 1}. [${sev}] ${title}${cat}`);
    if (f.details) {
      lines.push("");
      lines.push(f.details);
    }
    if (f.remediation) {
      lines.push("");
      lines.push("**Remediation:**");
      lines.push("");
      lines.push(f.remediation);
    }
    lines.push("");
  });

  return lines.join("\n");
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

  const data = (await res.json()) as { run?: RunDetail };
  if (!data?.run) {
    return new Response("Malformed API response", { status: 502 });
  }

  const md = toMarkdown(data.run);

  return new Response(md, {
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      "content-disposition": `attachment; filename=masat-run-${runId}.md`,
    },
  });
}
