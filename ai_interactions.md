# AI Interactions Log

Tool: Claude Code (agentic workflow), one session, plan-first.

## Agentic workflow
**Task given:** "Use my previous music recommender repo, plan and then carry out the Applied AI System assignment, and document it."

**Process:** read the original repo, wrote a plan (RAG + agent loop + guardrails + eval), got approval, wrote failing tests first, implemented modules, ran an evaluation harness, fixed what it found, captured real outputs into the README.

**Files generated:** `src/{retriever,agent,guardrails,logger,concierge}.py`, `data/knowledge/*.md`, 12 extra songs, `tests/test_{retriever,guardrails,agent}.py`, `eval/run_eval.py`, `diagrams/architecture.mmd`, README, model card, presentation outline.

**What needed human or follow-up verification:**
- First eval run failed 2 of 13 cases (metal override, the word "vibes"); both were real bugs in AI-written code, fixed in code rather than by loosening tests.
- A critic gap let a contradictory request pass as `ok`; found by reading output, fixed with an energy-mismatch rule.
- Grounding label cited the wrong document; found by reading sample output.
- Not done by the AI: creating the new GitHub repo, pushing, the Loom video, and writing the personal reflection (needs the owner).
