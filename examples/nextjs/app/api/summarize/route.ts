import { AI, SynthrError } from "synthr-sdk";
import { NextResponse } from "next/server";

// Runs on the SERVER only. The secret key is read from a non-public env var,
// so it never ships to the browser.
const ai = new AI({
  url: process.env.SYNTHR_URL ?? "http://localhost:8000",
  key: process.env.SYNTHR_SECRET_KEY!, // sk_proj_…
});

export async function POST(req: Request) {
  const { text } = await req.json();
  try {
    const { summary } = await ai.summarize(text, 20);
    return NextResponse.json({ summary });
  } catch (e) {
    const err = e as SynthrError;
    return NextResponse.json({ error: err.message, code: err.code }, { status: err.status ?? 500 });
  }
}
