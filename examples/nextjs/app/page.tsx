"use client";

import { CSSProperties, useState } from "react";

// ── shared call + styles ────────────────────────────────────────────────
async function run(feature: string, payload: unknown): Promise<any> {
  const res = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feature, payload }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json?.error?.message || json?.error || `HTTP ${res.status}`);
  return json.data;
}

const card: CSSProperties = { border: "1px solid #e4e4e7", borderRadius: 12, padding: 18, background: "#fff" };
const input: CSSProperties = { width: "100%", padding: 9, fontSize: 14, border: "1px solid #d4d4d8", borderRadius: 8, boxSizing: "border-box", fontFamily: "inherit" };
const ta: CSSProperties = { ...input, minHeight: 64, resize: "vertical" };
const btn: CSSProperties = { marginTop: 10, padding: "9px 16px", border: 0, borderRadius: 8, background: "#0f6e56", color: "#fff", fontWeight: 600, cursor: "pointer" };
const out: CSSProperties = { marginTop: 12, background: "#f4f4f5", padding: 12, borderRadius: 8, whiteSpace: "pre-wrap", fontSize: 14, lineHeight: 1.5 };
const errStyle: CSSProperties = { ...out, background: "#fde8e8", color: "#9b1c1c" };
const h3: CSSProperties = { margin: "0 0 2px", fontSize: 16 };
const sub: CSSProperties = { margin: "0 0 12px", color: "#71717a", fontSize: 13 };

function Result({ busy, error, children }: { busy: boolean; error: string; children?: React.ReactNode }) {
  if (busy) return <div style={out}>…</div>;
  if (error) return <div style={errStyle}>{error}</div>;
  return <>{children}</>;
}

function useRunner() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const call = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };
  return { busy, error, call };
}

// ── Form autofill (the hero — words in, a filled form out) ───────────────
const FIELDS = [
  { name: "brand", type: "string", label: "Brand" },
  { name: "size", type: "number", label: "Size" },
  { name: "color", type: "string", label: "Color" },
  { name: "inStock", type: "boolean", label: "In stock" },
];

function Autofill() {
  const [text, setText] = useState("The new Nike Air Max in red, size 10 — in stock now.");
  const [values, setValues] = useState<Record<string, unknown> | null>(null);
  const [unfilled, setUnfilled] = useState<string[]>([]);
  const { busy, error, call } = useRunner();

  const go = () =>
    call(async () => {
      const data = await run("fillForm", {
        fields: FIELDS.map(({ name, type }) => ({ name, type })),
        context: text,
      });
      setValues(data.values);
      setUnfilled(data.unfilled || []);
    });

  return (
    <div style={{ ...card, gridColumn: "1 / -1" }}>
      <h3 style={h3}>📝 Form autofill</h3>
      <p style={sub}>Describe something in plain words — Synthr fills the structured form. No prompt, no parsing on your side.</p>
      <textarea style={ta} value={text} onChange={(e) => setText(e.target.value)} />
      <button style={btn} onClick={go} disabled={busy}>Autofill the form →</button>
      <Result busy={busy} error={error}>
        {values && (
          <div style={{ marginTop: 14, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
            {FIELDS.map((f) => (
              <label key={f.name} style={{ fontSize: 12, color: "#52525b" }}>
                {f.label}
                <input
                  style={{ ...input, marginTop: 4, background: values[f.name] == null ? "#fafafa" : "#ecfdf5" }}
                  readOnly
                  value={values[f.name] == null ? "" : String(values[f.name])}
                  placeholder="—"
                />
              </label>
            ))}
          </div>
        )}
        {values && unfilled.length > 0 && (
          <p style={{ ...sub, marginTop: 10 }}>Not found in the text (left empty, never guessed): {unfilled.join(", ")}</p>
        )}
      </Result>
    </div>
  );
}

// ── generic single-output text feature ──────────────────────────────────
function TextFeature(props: {
  icon: string;
  title: string;
  desc: string;
  feature: string;
  inKey: string;
  outKey: string;
  initial: string;
  second?: { key: string; label: string; initial: string };
}) {
  const [val, setVal] = useState(props.initial);
  const [second, setSecond] = useState(props.second?.initial ?? "");
  const [result, setResult] = useState("");
  const { busy, error, call } = useRunner();

  const go = () =>
    call(async () => {
      const payload: Record<string, unknown> = { [props.inKey]: val };
      if (props.second) payload[props.second.key] = second;
      const data = await run(props.feature, payload);
      setResult(String(data[props.outKey] ?? ""));
    });

  return (
    <div style={card}>
      <h3 style={h3}>{props.icon} {props.title}</h3>
      <p style={sub}>{props.desc}</p>
      <textarea style={ta} value={val} onChange={(e) => setVal(e.target.value)} />
      {props.second && (
        <input
          style={{ ...input, marginTop: 8 }}
          value={second}
          onChange={(e) => setSecond(e.target.value)}
          placeholder={props.second.label}
        />
      )}
      <button style={btn} onClick={go} disabled={busy}>Run</button>
      <Result busy={busy} error={error}>{result && <div style={out}>{result}</div>}</Result>
    </div>
  );
}

// ── SEO (structured output) ──────────────────────────────────────────────
function Seo() {
  const [content, setContent] = useState("Synthr is a self-hosted gateway that gives every project ready-made AI features behind one SDK.");
  const [r, setR] = useState<{ title?: string; description?: string; keywords?: string[] } | null>(null);
  const { busy, error, call } = useRunner();
  const go = () => call(async () => setR(await run("seo", { content })));
  return (
    <div style={card}>
      <h3 style={h3}>🔎 SEO metadata</h3>
      <p style={sub}>Content in → title, meta description, and keywords out.</p>
      <textarea style={ta} value={content} onChange={(e) => setContent(e.target.value)} />
      <button style={btn} onClick={go} disabled={busy}>Run</button>
      <Result busy={busy} error={error}>
        {r && (
          <div style={out}>
            <div><b>Title:</b> {r.title}</div>
            <div><b>Description:</b> {r.description}</div>
            <div><b>Keywords:</b> {(r.keywords || []).join(", ")}</div>
          </div>
        )}
      </Result>
    </div>
  );
}

// ── Image generation ─────────────────────────────────────────────────────
function ImageGen() {
  const [prompt, setPrompt] = useState("a minimalist red running shoe on a white background");
  const [b64, setB64] = useState("");
  const [mime, setMime] = useState("image/png");
  const { busy, error, call } = useRunner();
  const go = () =>
    call(async () => {
      const data = await run("image", { prompt });
      setB64(data.images?.[0]?.b64 ?? "");
      setMime(data.images?.[0]?.mime ?? "image/png");
    });
  return (
    <div style={card}>
      <h3 style={h3}>🖼️ Image generation</h3>
      <p style={sub}>Prompt → image. Free via Hugging Face — set <code>HF_TOKEN</code> on the gateway (first call may warm up the model).</p>
      <textarea style={ta} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
      <button style={btn} onClick={go} disabled={busy}>Generate</button>
      <Result busy={busy} error={error}>
        {b64 && <img alt="generated" src={`data:${mime};base64,${b64}`} style={{ marginTop: 12, maxWidth: "100%", borderRadius: 8 }} />}
      </Result>
    </div>
  );
}

// ── Background removal (local, free) ─────────────────────────────────────
const checker: CSSProperties = {
  backgroundImage:
    "linear-gradient(45deg,#ddd 25%,transparent 25%),linear-gradient(-45deg,#ddd 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#ddd 75%),linear-gradient(-45deg,transparent 75%,#ddd 75%)",
  backgroundSize: "16px 16px",
  backgroundPosition: "0 0,0 8px,8px -8px,-8px 0",
};

function BgRemove() {
  const [src, setSrc] = useState("");
  const [b64, setB64] = useState("");
  const [result, setResult] = useState("");
  const { busy, error, call } = useRunner();

  function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = String(reader.result);
      setSrc(dataUrl);
      setB64(dataUrl.split(",")[1] ?? "");
      setResult("");
    };
    reader.readAsDataURL(f);
  }

  const go = () =>
    call(async () => {
      const data = await run("removeBackground", { image: b64 });
      setResult(data.image?.b64 ?? "");
    });

  return (
    <div style={card}>
      <h3 style={h3}>🪄 Background removal</h3>
      <p style={sub}>Local & free (rembg) — upload an image, get a transparent PNG back. First run downloads the model.</p>
      <input type="file" accept="image/*" onChange={onFile} style={{ fontSize: 13 }} />
      <button style={btn} onClick={go} disabled={busy || !b64}>Remove background</button>
      <Result busy={busy} error={error}>
        <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
          {src && <img alt="input" src={src} style={{ maxWidth: 150, borderRadius: 8 }} />}
          {result && <img alt="output" src={`data:image/png;base64,${result}`} style={{ maxWidth: 150, borderRadius: 8, ...checker }} />}
        </div>
      </Result>
    </div>
  );
}

export default function Home() {
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", maxWidth: 920, margin: "2.5rem auto", padding: "0 1rem", color: "#18181b" }}>
      <h1 style={{ marginBottom: 4 }}>Synthr Playground</h1>
      <p style={{ color: "#52525b", marginTop: 0 }}>
        Ready-made AI features, called by name. Every result below is <b>one API call</b> — this app writes no prompts,
        holds no provider keys, and does no parsing. Powered by your gateway on <code>:8000</code>.
      </p>

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(2, 1fr)", marginTop: 20 }}>
        <Autofill />
        <TextFeature icon="✂️" title="Summarize" desc="Long text → a short summary." feature="summarize" inKey="text" outKey="summary" initial="Synthr is a self-hosted AI gateway. Stand it up once and every project calls ready-made features behind one SDK, with auth, caching, rate limits, guardrails, fallback, and cost tracking built in." />
        <TextFeature icon="🌍" title="Translate" desc="Any text → any language." feature="translate" inKey="text" outKey="translation" initial="Good morning, how are you?" second={{ key: "target_lang", label: "Target language (e.g. Spanish)", initial: "Spanish" }} />
        <TextFeature icon="🪄" title="Rewrite" desc="Transform tone, grammar, or style." feature="rewrite" inKey="text" outKey="text" initial="we was hoping you can maybe help us out" second={{ key: "instruction", label: "Instruction", initial: "Make it formal and concise." }} />
        <TextFeature icon="💡" title="Generate" desc="Freeform prompt → text." feature="generate" inKey="prompt" outKey="text" initial="Write a one-line tagline for a self-hosted AI gateway." />
        <Seo />
        <TextFeature icon="💬" title="Chat (OpenAI-compatible)" desc="Raw chat via /v1/chat/completions." feature="chat" inKey="prompt" outKey="text" initial="In one sentence, what is an AI gateway?" />
        <ImageGen />
        <BgRemove />
      </div>
    </main>
  );
}
