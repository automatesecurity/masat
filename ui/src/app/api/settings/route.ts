import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const form = await req.formData();
  const persona = String(form.get("persona") || "analyst");
  const owner = String(form.get("owner") || "");

  const res = NextResponse.redirect(new URL("/", req.url));

  res.cookies.set("masat_persona", persona, { path: "/", httpOnly: false });
  res.cookies.set("masat_owner", owner, { path: "/", httpOnly: false });

  return res;
}
