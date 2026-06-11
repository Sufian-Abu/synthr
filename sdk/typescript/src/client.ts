import { AIOptions, FillFormResult, FormField, SynthrError } from "./types.js";

/** Client for the Synthr gateway. Same call works in the browser or Node 18+. */
export class AI {
  private url: string;
  private key: string;
  private userId?: string;
  private fetchImpl: typeof fetch;

  constructor(opts: AIOptions) {
    this.url = (opts.url ?? "http://localhost:8000").replace(/\/$/, "");
    this.key = opts.key;
    this.userId = opts.userId;
    // Bind the global fetch to globalThis — a bare `fetch` reference called as a method
    // throws "Illegal invocation" in browsers (and undici/Node). A user-supplied fetch is
    // used as-is (their responsibility to bind).
    this.fetchImpl = opts.fetch ?? globalThis.fetch.bind(globalThis);
  }

  private async call<T = unknown>(feature: string, body: unknown): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "X-Project-Key": this.key,
    };
    if (this.userId) headers["X-User-Id"] = this.userId;

    const res = await this.fetchImpl(`${this.url}/v1/${feature}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const json = (await res.json().catch(() => ({}))) as {
      data?: T;
      error?: { code?: string; message?: string; retry_after_seconds?: number };
    };

    if (!res.ok) {
      const e = json.error ?? {};
      throw new SynthrError(e.code ?? "http_error", e.message ?? res.statusText, res.status, e.retry_after_seconds);
    }
    return json.data as T;
  }

  fillForm(fields: FormField[], context: unknown, locale?: string): Promise<FillFormResult> {
    return this.call<FillFormResult>("fillForm", { fields, context, ...(locale ? { locale } : {}) });
  }

  summarize(text: string, maxWords?: number): Promise<{ summary: string }> {
    return this.call("summarize", { text, ...(maxWords != null ? { max_words: maxWords } : {}) });
  }

  translate(text: string, targetLang: string): Promise<{ translation: string }> {
    return this.call("translate", { text, target_lang: targetLang });
  }

  image(prompt: string, size = "1024x1024", n = 1): Promise<{ images: Array<{ b64?: string; url?: string; mime?: string }> }> {
    return this.call("image", { prompt, size, n });
  }

  removeBackground(opts: { image?: string; imageUrl?: string }): Promise<{ image: { b64: string; mime: string } }> {
    return this.call("removeBackground", { image: opts.image, image_url: opts.imageUrl });
  }

  generate(prompt: string, maxWords?: number): Promise<{ text: string }> {
    return this.call("generate", { prompt, ...(maxWords != null ? { max_words: maxWords } : {}) });
  }

  rewrite(text: string, instruction?: string): Promise<{ text: string }> {
    return this.call("rewrite", { text, ...(instruction ? { instruction } : {}) });
  }

  seo(content: string): Promise<{ title: string; description: string; keywords: string[] }> {
    return this.call("seo", { content });
  }

  classify(text: string, labels: string[]): Promise<{ label: string | null; confidence: number | null }> {
    return this.call("classify", { text, labels });
  }

  extract<T = unknown>(text: string, opts: { schema?: Record<string, string>; fields?: unknown[] }): Promise<T> {
    return this.call<T>("extract", { text, schema: opts.schema, fields: opts.fields });
  }

  moderate(text: string): Promise<{ flagged: boolean; categories: string[]; reason: string | null }> {
    return this.call("moderate", { text });
  }

  embed(input: string | string[]): Promise<{ model: string; dimensions: number; vectors: number[][] }> {
    return this.call("embed", { input });
  }

  /** Escape hatch for any feature, including custom ones. */
  run<T = unknown>(feature: string, payload: unknown): Promise<T> {
    return this.call<T>(feature, payload);
  }
}
