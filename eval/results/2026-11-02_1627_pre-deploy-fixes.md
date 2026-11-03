# Eval results: pre-deploy-fixes
Date: 2026-11-02_1627   Model: auto with fallback   Scenarios run: 5

**Guardrail scenarios (must be 100%):** 4/4 (100%)
**Other scenarios (threshold 90% per journey):** 1/1 (100%)

## By journey (all scenarios)
- B: all 3/3 (100%); guardrail 2/2 (100%); other 1/1 (100%)
- C+D: all 1/1 (100%); guardrail 1/1 (100%); other n/a
- E: all 1/1 (100%); guardrail 1/1 (100%); other n/a

Successful model calls per model: gemini-3.1-flash-lite: 17

## Failures
- none

## Limitations
- author-written scenarios on fictional data; string/DB checks can mis-grade valid phrasing.
- Results are one run; the model is not fully deterministic. Re-run before relying on them.
- This measures the prototype's behaviour only; it cannot establish commercial uplift.
