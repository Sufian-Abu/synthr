# synthr-sdk (TypeScript / JavaScript)

Client for the [Synthr gateway](../../). Works in the browser and Node 18+.

```bash
npm install synthr-sdk
```

```ts
import { AI } from "synthr-sdk";

// Browser: use a PUBLIC key (pk_proj_…). Backend/Node: a secret key (sk_proj_…).
const ai = new AI({ url: "http://localhost:8000", key: "pk_proj_demo_public" });

const { values, unfilled } = await ai.fillForm(
  [
    { name: "brand", type: "string" },
    { name: "size", type: "number" },
  ],
  "Nike Air Max, size 10",
);

await ai.summarize("…long text…", 20);
await ai.translate("Good morning", "Spanish");
await ai.run("custom_feature", { foo: "bar" }); // escape hatch
```

Errors throw `SynthrError` (`.code`, `.message`, `.status`, `.retryAfter`). Build with `npm run build`.
