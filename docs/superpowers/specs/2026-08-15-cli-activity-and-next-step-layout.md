# CLI Activity and Next-Step Layout

## Goal

Separate completed public work from a single actionable user choice and avoid
duplicating a clarification in the generated answer.

## Output

```text
Activity
✓ Classified requested outcome (1.90s)
✓ Refined outcome classification (6.83s)
✓ Matched workflows — PUMA, LIONESS-PUMA

Next step
? Choose network granularity
  Aggregate or sample-specific?

Reply: aggregate | sample-specific
```

`Activity` contains only completed public events. `Next step` contains one
action. When the CLI presents a clarification, the response generator receives
a flag and must not repeat that question or its workflow list. Public facts
only; no private model content. Non-clarification responses remain unchanged.

## Verification

Test activity/next-step spacing, one clarification occurrence, and unchanged
ordinary responses and tool cards.
