# synthr-sdk (Python)

Thin client for the [Synthr gateway](../../). Call features — never raw HTTP.

```bash
pip install synthr-sdk
```

```python
from synthr import AI

ai = AI(key="sk_proj_...")            # url defaults to http://localhost:8000 (or $SYNTHR_URL)

ai.fill_form(
    fields=[{"name": "brand", "type": "string"}, {"name": "size", "type": "number"}],
    context="Nike Air Max, size 10",
)                                     # -> {"values": {...}, "unfilled": [...]}

ai.summarize(text="...", max_words=20)
ai.translate(text="Good morning", target_lang="Spanish")
ai.image(prompt="a red shoe")         # backend-only by default
ai.remove_background(image_url="https://...")
ai.run("custom_feature", {"foo": "bar"})   # escape hatch
```

Async is identical with `AsyncAI` and `await`. Errors raise `SynthrError` (`.code`, `.message`,
`.status`, `.retry_after`). Config: `AI(key=..., url=..., user_id=...)` or `$SYNTHR_KEY` / `$SYNTHR_URL`.
