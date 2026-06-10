// Frontend usage (JS `fetch`) — identical to what a browser/React app does.
// Run with: node examples/frontend.mjs
// Uses the PUBLIC key + an allowed Origin header (browsers send Origin automatically).

const BASE = process.env.SYNTHR_URL ?? "http://localhost:8000";
const KEY = process.env.SYNTHR_PUBLIC_KEY ?? "pk_proj_demo_public";
const ORIGIN = "http://localhost:3000"; // must be in the key's allowed_origins

async function call(feature, payload) {
  const res = await fetch(`${BASE}/v1/${feature}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Project-Key": KEY, Origin: ORIGIN },
    body: JSON.stringify(payload),
  });
  const body = await res.json();
  if (!res.ok) throw new Error(`${feature}: ${body.error?.code} ${body.error?.message}`);
  return body;
}

const form = await call("fillForm", {
  fields: [
    { name: "brand", type: "string" },
    { name: "size", type: "number" },
  ],
  context: "Nike Air Max, size 10",
});
console.log("fillForm  ->", form.data.values, "| provider:", form.meta.provider);

const tr = await call("translate", { text: "Good morning", target_lang: "Japanese" });
console.log("translate ->", tr.data.translation);
