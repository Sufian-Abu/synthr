export interface AIOptions {
  /** Gateway base URL. Defaults to http://localhost:8000 */
  url?: string;
  /** Project key: sk_proj_… (backend) or pk_proj_… (browser). */
  key: string;
  /** Optional stable user id for per-user rate limits. */
  userId?: string;
  /** Override fetch (for tests / non-browser runtimes). */
  fetch?: typeof fetch;
}

export interface FormField {
  name: string;
  type?: "string" | "number" | "integer" | "boolean";
  description?: string;
  options?: unknown[];
}

export interface FillFormResult {
  values: Record<string, unknown>;
  unfilled: string[];
}

export class SynthrError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public retryAfter?: number,
  ) {
    super(`${code}: ${message}`);
    this.name = "SynthrError";
  }
}
