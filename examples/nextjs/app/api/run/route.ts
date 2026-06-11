import { NextResponse } from "next/server";

// One server-side proxy for every feature. The SECRET key stays on the server;
// the browser only ever talks to this route. (The dual-key model — calling the
// gateway directly from the browser with a public key — is shown in the README.)
const BASE = process.env.SYNTHR_URL ?? "http://localhost:8000";
const KEY = process.env.SYNTHR_SECRET_KEY!;

export async function POST(req: Request) {
  const { feature, payload } = await req.json();

  // `chat` is the OpenAI-compatible endpoint — call it and normalize to { data: { text } }.
  if (feature === "chat") {
    const r = await fetch(`${BASE}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${KEY}` },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: [{ role: "user", content: payload.prompt }],
      }),
    });
    const j = await r.json();
    if (!r.ok) return NextResponse.json(j, { status: r.status });
    return NextResponse.json({ data: { text: j.choices?.[0]?.message?.content ?? "" } });
  }

  const r = await fetch(`${BASE}/v1/${feature}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Project-Key": KEY },
    body: JSON.stringify(payload),
  });
  return NextResponse.json(await r.json(), { status: r.status });
}
