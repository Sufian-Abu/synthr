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
    this.fetchImpl = opts.fetch ?? fetch;
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

  /** Escape hatch for any feature, including custom ones. */
  run<T = unknown>(feature: string, payload: unknown): Promise<T> {
    return this.call<T>(feature, payload);
  }
}
