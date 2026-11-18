# Model Card: Music Concierge

**Scope:** a retrieval-grounded, rule-based recommender over a 30-song catalog. It contains no trained model and no LLM. "AI" here means retrieval (TF-IDF), an agentic critic loop, and confidence-based guardrails. Original Module 3 scorer: see the README.

## Intended use
Turn a short free-text request into 5 songs plus an explanation, and say when it is unsure. Educational demo, not a production recommender.

## Limitations and biases
- **Tiny, hand-made data.** 30 songs and 14 knowledge docs, all written by me. Genres skew toward Western popular music (pop, rock, hip hop, EDM, country). Folk, classical and reggae have 1-3 songs each, so users who want them get thin results.
- **Vocabulary-bound retrieval.** TF-IDF matches words, not meaning. "Music to nap to" may miss "sleep". The system then asks for clarification rather than guessing, which is safe but sometimes annoying. English only.
- **Stereotyped vibes.** My docs map "sad" to folk, "romantic" to R&B, "hype" to hip hop, "party" to EDM. These are my assumptions and reinforce genre-mood clichés. A listener who finds metal relaxing is not served unless they say "metal".
- **One profile dimension at a time.** There is no listening history, no lyrics, no language or culture signal, and no popularity data. Artist diversity is a flat cap of 2.
- **Confidence is heuristic.** The 0-1 score is a hand-weighted blend, not a calibrated probability. A high number does not guarantee a good match (see Surprises).
- **Evaluation bias.** I wrote the 13 test cases after reading the code. Passing them is not evidence of general accuracy, and no real users have rated the output.

## Misuse and prevention
- **Prompt injection / abuse:** there is no LLM to hijack, so injected instructions are only treated as search words. Input is capped at 300 characters and must be mostly letters.
- **Manipulation:** if this were extended with real artists, anyone who controls the knowledge docs or keywords could push specific songs. Prevention: keep the knowledge base in version control with review, and log the retrieved doc for every recommendation (already done: `grounded_in` in the log).
- **Overtrust:** the biggest realistic risk is users believing a confident-looking list. Mitigation: explanations show the exact scoring arithmetic, and low-confidence results are labelled and ask the user to confirm.
- **Privacy:** queries are logged locally in `logs/agent.log` (git-ignored). A deployed version would need retention limits and no user identifiers.

## What surprised me while testing reliability
1. A contradictory request ("sad heartbreak songs but very high energy") scored *higher* confidence than some normal queries, because mood and genre matches carried the total. I had to add an explicit energy-gap rule and make critic issues override the number.
2. A single filler word ("vibes") was enough to retrieve a confident, wrong document.
3. Overriding only the genre ("I want metal") silently kept the previous document's mood, so the top result was rock. The bug was invisible without reading the explanation line.

## Collaboration with AI
I built this with Claude Code, starting from a written plan I approved before any code was written. The AI wrote the plan, tests-first, the modules, the eval harness and the first drafts of the docs. I set the goals, approved the plan and own the final review.

- **Accepted (kept):** the AI proposed making retrieved documents *set* the profile, so removing the knowledge base changes the results, instead of printing a retrieved snippet next to a normal answer. That was kept because it satisfies the "integrated feature" requirement and makes the behaviour testable. The AI's fix for the metal bug was also kept: an explicit genre now pulls mood and energy from that genre's document.
- **Changed / not built as written:** the approved plan included an optional Claude-API query parser next to the offline one. The AI dropped it during the build because it would make results depend on a key and network and make tests non-deterministic, while the offline parser already covers every demo case. Also, when two eval cases failed on the first run, the AI fixed the code and left the expected outcomes unchanged instead of loosening them.
- **Where the AI needed checking:** it initially labelled the metal result "grounded in 'Workout and gym'" even though the profile came from the metal document. Reading the sample output caught it and it was fixed so that explanations cite the document that actually produced the profile.

<!-- TODO(owner): this section was drafted by the AI from what happened in the build session. Re-read it and rewrite the accepted/rejected examples in your own words, and correct anything that does not match your recollection. -->
