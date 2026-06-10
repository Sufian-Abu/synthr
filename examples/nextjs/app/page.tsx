"use client";

import { useState } from "react";
import { AI } from "synthr-sdk";

// Browser-safe: a PUBLIC key (pk_proj_…), locked to this origin and to
// frontend_safe features in synthr.config.yaml. Safe to ship in client JS.
const browserAI = new AI({
  url: process.env.NEXT_PUBLIC_SYNTHR_URL ?? "http://localhost:8000",
  key: process.env.NEXT_PUBLIC_SYNTHR_PUBLIC_KEY!,
});

export default function Home() {
  const [out, setOut] = useState("Click a button →");

  // (1) Backend feature through our own server route — the SECRET key stays server-side.
  async function summarizeViaServer() {
    setOut("…");
    const res = await fetch("/api/summarize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: "Synthr is a self-hosted gateway for ready-made AI features." }),
    });
    setOut(JSON.stringify(await res.json(), null, 2));
  }

  // (2) frontend_safe feature called DIRECTLY from the browser with the PUBLIC key.
  async function fillFormFromBrowser() {
    setOut("…");
    try {
      const result = await browserAI.fillForm(
        [
          { name: "brand", type: "string" },
          { name: "size", type: "number" },
        ],
        "Nike Air Max, size 10",
      );
      setOut(JSON.stringify(result, null, 2));
    } catch (e) {
      setOut(String(e));
    }
  }

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 640, margin: "3rem auto", padding: "0 1rem" }}>
      <h1>Next.js + Synthr</h1>
      <p>Two paths to the same gateway — secret key on the server, public key in the browser.</p>
      <div style={{ display: "flex", gap: 12, margin: "1.5rem 0" }}>
        <button onClick={summarizeViaServer}>Summarize (via server, secret key)</button>
        <button onClick={fillFormFromBrowser}>Fill form (browser, public key)</button>
      </div>
      <pre style={{ background: "#f4f4f5", padding: 16, borderRadius: 8, whiteSpace: "pre-wrap" }}>{out}</pre>
    </main>
  );
}
