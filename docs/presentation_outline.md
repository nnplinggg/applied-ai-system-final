# 5-7 minute presentation outline

1. **Hook (0:30)** - "My Module 3 recommender needed a stats-style profile. Real people say 'rainy study vibes'." 
2. **Original project (0:45)** - Music Recommender Simulation: content-based scorer, 4 weighted features, 18 songs.
3. **What I added (1:00)** - Show `diagrams/architecture.mmd`: guardrail -> RAG retriever -> planner -> scorer -> critic loop -> confidence -> human check.
4. **Live demo (2:00)** - Run 3 commands from `docs/sample_runs.txt`: study (ok), metal override (RAG changes mood), contradictory sad+high-energy (low confidence, asks the human). Then gibberish.
5. **Reliability (1:00)** - `python -m eval.run_eval` (13/13) + `pytest` (19). Tell the story of the two failures the harness caught first (metal override, "vibes").
6. **Limits and ethics (0:45)** - 30 songs, 14 hand-written docs, western genre bias, keyword retrieval; see model_card.md.
7. **Takeaway (0:30)** - Reliability work (critic, confidence, evals) mattered more than the retrieval itself.

Key terms to say out loud: agent, guardrail, human-in-the-loop, orchestration, RAG, reliability testing, verification.
