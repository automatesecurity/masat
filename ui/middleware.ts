import { NextResponse, type NextRequest } from "next/server";

function withParams(url: URL, params: Record<string, string>) {
  for (const [k, v] of Object.entries(params)) {
    if (!url.searchParams.get(k)) url.searchParams.set(k, v);
  }
  return url;
}

export function middleware(req: NextRequest) {
  const persona = req.cookies.get("masat_persona")?.value || "analyst";
  const owner = req.cookies.get("masat_owner")?.value || "";

  const url = req.nextUrl.clone();
  const path = url.pathname;

  // Persona-driven defaults (non-destructive): only apply when user hasn't set their own filters.
  if (persona === "owner" && owner) {
    if (path === "/issues") {
      if (!url.searchParams.get("owner")) {
        return NextResponse.redirect(withParams(url, { owner }));
      }
    }

    if (path === "/assets") {
      // Assets page currently supports search via q; set q=owner as a weak default, or better: add owner filter later.
      // We'll keep it minimal and not override; leave for a follow-up.
    }

    if (path === "/") {
      // Default to owned-only view for an asset owner.
      if (!url.searchParams.get("owned")) {
        return NextResponse.redirect(withParams(url, { owned: "1" }));
      }
    }
  }

  if (persona === "ciso") {
    // Ensure dashboard is the landing page (it already is /)
    return NextResponse.next();
  }

  // Analyst: no defaults.
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/issues", "/assets"],
};
