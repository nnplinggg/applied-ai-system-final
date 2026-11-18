"""Agentic loop: validate -> retrieve (RAG) -> plan profile -> recommend -> critique -> revise.

Retrieved knowledge docs decide the structured profile (genre/mood/energy/acoustic), so
retrieval changes what gets recommended, not just what gets printed.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.guardrails import LOW_CONFIDENCE, MIN_SIMILARITY, compute_confidence, validate_query
from src.logger import log_event
from src.recommender import DEFAULT_WEIGHTS, recommend_songs, score_song

MAX_ITERS = 3
MAX_PER_ARTIST = 2
MAX_ENERGY_GAP = 0.35  # top pick this far from target energy means the request is contradictory
MIN_TOP_RATIO = 0.65  # top song must reach this share of the max possible score
K = 5


@dataclass
class Rec:
    song: Dict
    score: float
    explanation: str


@dataclass
class Result:
    query: str
    status: str  # ok | low_confidence | needs_clarification | rejected
    message: str = ""
    profile: Dict = field(default_factory=dict)
    recs: List[Rec] = field(default_factory=list)
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    trace: List[Dict] = field(default_factory=list)


class Agent:
    def __init__(self, songs: List[Dict], retriever):
        self.songs = songs
        self.retriever = retriever
        self.genres = sorted({s["genre"] for s in songs}, key=len, reverse=True)
        self.moods = {s["mood"] for s in songs}

    # ---- helpers -------------------------------------------------------
    def _step(self, trace, step, **info):
        trace.append({"step": step, **info})
        log_event(step, **info)

    def _overrides(self, query: str) -> Dict:
        """Explicit words in the query beat retrieved defaults."""
        q, out = query.lower(), {}
        for g in self.genres:
            if re.search(rf"\b{re.escape(g)}\b", q):
                out["genre"] = g
                break
        for m in self.moods:
            if re.search(rf"\b{re.escape(m)}\b", q):
                out["mood"] = m
                break
        if re.search(r"\b(very |really |super )?high[- ]energy\b|\bupbeat energy\b", q):
            out["energy"] = 0.9
        elif re.search(r"\blow[- ]energy\b|\bmellow\b", q):
            out["energy"] = 0.25
        if re.search(r"\bnon[- ]acoustic\b|\belectronic\b", q):
            out["likes_acoustic"] = False
        elif re.search(r"\bacoustic\b", q):
            out["likes_acoustic"] = True
        return out

    def _prefs(self, p: Dict) -> Dict:
        return {k: v for k, v in p.items() if v is not None}

    def _rank(self, profile: Dict, weights: Dict):
        pool = recommend_songs(self._prefs(profile), self.songs, k=len(self.songs), weights=weights)
        picked, per_artist = [], {}
        for song, score, expl in pool:  # enforce artist diversity
            if per_artist.get(song["artist"], 0) >= MAX_PER_ARTIST:
                continue
            per_artist[song["artist"]] = per_artist.get(song["artist"], 0) + 1
            picked.append(Rec(song, score, expl))
            if len(picked) == K:
                break
        return picked

    # ---- main loop -----------------------------------------------------
    def run(self, query) -> Result:
        trace: List[Dict] = []
        v = validate_query(query)
        self._step(trace, "validate", ok=v.ok, reason=v.reason)
        if not v.ok:
            return Result(str(query), "rejected", v.reason, trace=trace)
        query = v.cleaned

        hits = self.retriever.search(query, k=3)
        best = hits[0].score if hits else 0.0
        self._step(trace, "retrieve", hits=[(h.doc_id, h.score) for h in hits])
        if best < MIN_SIMILARITY:
            msg = "I couldn't match that to any music vibe I know. Try describing a mood, activity or genre."
            self._step(trace, "plan", action="ask_user", reason="no relevant knowledge retrieved")
            return Result(query, "needs_clarification", msg, trace=trace)

        profile = dict(hits[0].profile)
        over = self._overrides(query)
        grounded = hits[0]
        if "genre" in over:  # let the knowledge base say what the requested genre sounds like
            doc = next((d for d in self.retriever.docs if d.profile["genre"] == over["genre"]), None)
            if doc:
                profile.update({k: v for k, v in doc.profile.items() if k not in over})
                grounded = doc
        profile.update(over)
        self._step(trace, "plan", profile=profile, overrides=over, grounded_in=grounded.doc_id)

        weights, alt_hits, recs, issues = dict(DEFAULT_WEIGHTS), list(hits[1:]), [], []
        for i in range(1, MAX_ITERS + 1):
            recs = self._rank(profile, weights)
            max_score = sum(weights.values())
            ratio = recs[0].score / max_score if recs else 0.0
            issues = []
            if profile["genre"] not in self.genres:
                issues.append("catalog_gap_genre")
            if profile["mood"] not in self.moods:
                issues.append("catalog_gap_mood")
            if ratio < MIN_TOP_RATIO:
                issues.append("low_match")
            if recs and "energy" in profile and abs(recs[0].song["energy"] - profile["energy"]) > MAX_ENERGY_GAP:
                issues.append("energy_mismatch")
            self._step(trace, "critique", iteration=i, top_ratio=round(ratio, 2), issues=issues)
            if not issues:
                break
            # revise: relax the unattainable part of the request, then fall back to the runner-up doc
            if "catalog_gap_genre" in issues:
                profile["genre"], weights["genre"] = None, 0.0
            elif "catalog_gap_mood" in issues:
                profile["mood"], weights["mood"] = None, 0.0
            elif "low_match" in issues and alt_hits and i < MAX_ITERS:
                nxt = alt_hits.pop(0)
                if nxt.score >= MIN_SIMILARITY:
                    profile = {**nxt.profile, **over}
                    self._step(trace, "revise", action="try_runner_up_doc", doc=nxt.doc_id)
                    continue
            self._step(trace, "revise", action="stop", reason="no further fix")
            break

        margin = (recs[0].score - recs[1].score) / sum(weights.values()) if len(recs) > 1 else 0.0
        conf = compute_confidence(recs[0].score / sum(weights.values()), margin, best)
        status, msg = "ok", ""
        if conf < LOW_CONFIDENCE or issues:
            status = "low_confidence"
            msg = "I'm not confident in this match. Please confirm or refine your request (e.g. mood, genre, energy)."
        self._step(trace, "decide", status=status, confidence=conf)
        for r in recs:  # attach grounding to explanations
            r.explanation += f"; grounded in '{grounded.title}'"
        return Result(query, status, msg, profile, recs, conf, [h.doc_id for h in hits if h.score >= MIN_SIMILARITY], trace)
