# Music Concierge: an applied AI system built on my Music Recommender Simulation

## Original project

**Music Recommender Simulation** (Modules 1-3, [source](https://github.com/nnplinggg/musicrecommendersimulation)) was a content-based recommender. It stored songs as rows of attributes (genre, mood, energy, acousticness) and scored each song against a hand-built user profile with four weighted rules (mood +2, energy up to +2, genre +1, acousticness up to +1). It returned the top 5 songs with a plain-English reason for each score, and I stress-tested it with adversarial profiles.

## What this project does and why it matters

The original needed a structured profile such as `{genre: lofi, mood: focused, energy: 0.4}`. Real people say "quiet music for studying". **Music Concierge** takes free text and turns it into a recommendation the user can trust, using three AI components wired into the core logic:

| Feature | What it does | Where |
|---|---|---|
| **RAG** | Retrieves vibe documents from a local knowledge base (TF-IDF). The retrieved doc *sets* the profile (genre, mood, energy, acoustic) and is cited in every explanation. | `src/retriever.py`, `data/knowledge/` |
| **Agentic loop** | Plan, act, check, revise: build profile, score songs, run a critic, retry with a fix (up to 3 passes). | `src/agent.py` |
| **Reliability + guardrails** | Input validation, confidence score, human-in-the-loop prompts when confidence is low, JSON-lines logging, 19 unit tests and a 13-case evaluation harness. | `src/guardrails.py`, `src/logger.py`, `eval/`, `tests/` |

It matters because a recommender that always answers confidently is worse than one that says "I'm not sure, please confirm".

## Architecture overview

Source: [`diagrams/architecture.mmd`](diagrams/architecture.mmd) (Mermaid; paste into https://mermaid.live to view).

1. **Input guardrail** rejects empty, over-length (300 chars) and non-text input.
2. **Retriever** ranks 14 knowledge docs by TF-IDF cosine similarity. If the best similarity is below 0.08 the system asks the user to clarify instead of guessing.
3. **Planner** starts from the top doc's profile and applies explicit words in the query (a genre name, "high energy", "acoustic"). An explicit genre also pulls the mood and energy of that genre's doc.
4. **Scorer** is the original `recommend_songs` function, unchanged, followed by a cap of 2 songs per artist.
5. **Critic** flags: top score under 65% of the maximum, genre or mood missing from the catalog, or a top pick more than 0.35 away from the target energy (a contradictory request). The agent relaxes the unattainable part or tries the runner-up doc, and stops after 3 passes.
6. **Confidence** blends match quality (0.5), margin over the runner-up (0.2) and retrieval relevance (0.3). Below 0.55, or with any unresolved critic issue, the answer is marked `low_confidence` and the user is asked to confirm. This is the human-in-the-loop checkpoint.
7. Every step is appended to `logs/agent.log` as JSON.

## Setup

```bash
git clone <this repo> applied-ai-system-final && cd applied-ai-system-final
python3 -m venv .venv
source .venv/bin/activate            # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

pytest -q                            # 19 tests
python -m eval.run_eval              # 13-case reliability evaluation, writes eval/results.md
python -m src.concierge "quiet music for studying and reading"   # one query
python -m src.concierge              # interactive mode
```

No API key is needed. The system is fully offline and deterministic. Tested with Python 3.14 and scikit-learn 1.9.

## Sample interactions

Verbatim output, produced by the commands shown (full file: [`docs/sample_runs.txt`](docs/sample_runs.txt)).

### 1. Typical request: RAG sets the profile

```
$ python -m src.concierge "quiet music for studying and reading"
Status: ok   Confidence: 0.76
Retrieved: study_focus
Profile: genre=lofi, mood=focused, energy=0.4, likes_acoustic=True
  agent> step=critique, iteration=1, top_ratio=1.0, issues=[]
1. Focus Flow - LoRoom [lofi/focused] score 5.98
     mood match (+2.0); energy 0.40 vs target 0.40 (+2.00); genre match (+1.0); acousticness 0.78 vs target 0.80 (+0.98); grounded in 'Study and focus sessions'
2. Basement Static - LoRoom [lofi/focused] score 5.80
3. Library Rain - Paper Lanterns [lofi/chill] score 3.84
```

The user never said "lofi" or "focused". The retrieved document supplied both.

### 2. Explicit override: the knowledge base explains what "metal" sounds like

```
$ python -m src.concierge "workout music but I want metal"
Status: ok   Confidence: 0.81
Retrieved: workout_intense, aggressive_heavy
Profile: genre=metal, mood=aggressive, energy=0.97, likes_acoustic=False
1. Iron Cathedral - Black Tide [metal/aggressive] score 5.84
     ...grounded in 'Heavy and aggressive'
```

### 3. Guardrail: contradictory request goes back to the human

```
$ python -m src.concierge "sad heartbreak songs but very high energy"
Status: low_confidence   Confidence: 0.79
Profile: genre=folk, mood=sad, energy=0.9, likes_acoustic=True
  agent> step=critique, iteration=1, top_ratio=0.78, issues=['energy_mismatch']
  agent> step=revise, action=stop, reason=no further fix
1. Porch Lullaby - Wren & Willow [folk/sad] score 4.67
     mood match (+2.0); energy 0.30 vs target 0.90 (+0.80); ...
Note: I'm not confident in this match. Please confirm or refine your request (e.g. mood, genre, energy).
```

The numeric confidence (0.79) is high here, but the critic found a real contradiction (the saddest song is 0.6 below the requested energy), so the status overrides the number. See "Testing summary" for why.

### 4. Guardrails on bad input

```
$ python -m src.concierge "zxqv plmk wrtb"
Status: needs_clarification   Confidence: 0.00
Note: I couldn't match that to any music vibe I know. Try describing a mood, activity or genre.

$ python -m src.concierge ""
Status: rejected   Confidence: 0.00
Note: Input is empty. Describe the music you want.
```

A sample of the structured log is in [`docs/sample_log.jsonl`](docs/sample_log.jsonl).

## Reliability and guardrail results

`python -m eval.run_eval` (full table in [`eval/results.md`](eval/results.md)):

| Input | Checks | Status | Confidence | Top pick | Result |
|---|---|---|---|---|---|
| quiet music for studying and reading | typical request | ok | 0.76 | Focus Flow (lofi) | PASS |
| cozy rainy afternoon, calm and gentle | typical request | ok | 0.83 | Library Rain (lofi) | PASS |
| high intensity gym workout | typical request | ok | 0.92 | Gym Hero (pop) | PASS |
| friday night dance party | typical request | ok | 0.94 | Neon Pulse (edm) | PASS |
| romantic dinner date | typical request | ok | 0.95 | Velvet Hours (r&b) | PASS |
| workout music but I want metal | explicit genre override | ok | 0.81 | Iron Cathedral (metal) | PASS |
| road trip with country nostalgia | typical request | ok | 0.84 | Dust Road Anthem (country) | PASS |
| sad heartbreak songs but very high energy | contradictory request | low_confidence | 0.79 | Porch Lullaby (folk) | PASS |
| zxqv plmk wrtb | gibberish | needs_clarification | 0.00 | - | PASS |
| vibes | too vague | needs_clarification | 0.00 | - | PASS |
| (empty) | empty input | rejected | 0.00 | - | PASS |
| !!! 12345 ??? | non-text input | rejected | 0.00 | - | PASS |
| study study study ... | over-length input | rejected | 0.00 | - | PASS |

**13/13 passed; 19/19 pytest tests pass; mean confidence 0.85 on the 8 cases that returned songs.**

## Design decisions and trade-offs

- **Offline TF-IDF instead of an LLM or embeddings.** Anyone can clone and run it with no API key, results are deterministic, and tests are exact. The cost: it only understands words that appear in my 14 docs. A paraphrase like "music to nap to" may miss. An embedding model would fix that at the price of a download or API dependency.
- **Retrieval drives the profile, not the printout.** Removing the knowledge base changes which songs come back. That was the requirement for RAG being "integrated", and it made the system testable (`sources[0] == "study_focus"`).
- **Reused the original scorer unchanged.** The new layers sit around `recommend_songs`, so the Module 3 behaviour and tests still hold.
- **Critic uses simple, explainable rules** (score ratio, catalog gaps, energy gap) rather than a second model. Rules are auditable, but they only catch the failures I thought of.
- **Status can override confidence.** The numeric score is a blend and can hide a single hard contradiction, so any unresolved critic issue forces `low_confidence`.
- **Catalog grown from 18 to 30 songs** so the artist-diversity cap and genre overrides have something to choose between. It is still tiny.
- **Dropped the optional Claude-API query parser from the original plan.** It would break reproducibility and the offline guarantee for little gain in this scope.

## Testing summary

- **Automated:** 19 pytest tests (retriever, guardrails, agent, original recommender) plus the 13-case harness. All pass.
- **What the harness caught on its first run (11/13):**
  1. "workout music but I want metal" returned a *rock* song. The override replaced the genre but kept the workout doc's "intense" mood. Fix: an explicit genre also adopts that genre's mood and energy from the knowledge base.
  2. "vibes" retrieved the "Island vibes" doc and returned reggae with 0.75 confidence. Fix: generic filler words (vibes, music, songs, ...) are stop words. I fixed the code and did not change the expected outcomes. Both now have regression tests.
- **What surprised me:** the contradictory sad + high-energy request produced a *high* numeric confidence (0.76 at first) and status `ok`, because mood and genre matches outweighed the energy gap. I added the `energy_mismatch` critic rule and let issues override confidence.
- **Limits of the evidence:** the 13 cases were written by me, after reading the code, so a 100% pass rate shows the guardrails work on known cases, not that the system is correct in general.

## Reflection

The retrieval part was the easy part. The valuable work was deciding when the system should *not* answer: confidence numbers lie when one hard constraint is violated, and the only way I found that was by running adversarial inputs and reading the output instead of trusting a score. See [`model_card.md`](model_card.md) for limitations, misuse, and how I worked with AI.

## Portfolio

- Code: this repository
- Loom walkthrough: _add link here after recording_
- Presentation outline: [`docs/presentation_outline.md`](docs/presentation_outline.md)
- What this says about me as an AI engineer: _write 2-3 sentences in your own voice here_
