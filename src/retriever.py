"""TF-IDF retrieval over the markdown knowledge base in data/knowledge/.

Each doc: '# Title', 'keywords: ...', 'profile: genre=..; mood=..; energy=..; acoustic=..', then body text.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# Filler words that appear in almost every music request and carry no taste signal.
FILLER = {"vibe", "vibes", "music", "song", "songs", "playlist", "listen", "play", "want", "like", "something"}
STOP_WORDS = sorted(ENGLISH_STOP_WORDS | FILLER)


@dataclass
class Doc:
    doc_id: str
    title: str
    text: str
    profile: Dict


@dataclass
class Hit:
    doc_id: str
    title: str
    score: float
    profile: Dict


def _parse_profile(line: str) -> Dict:
    raw = dict(p.strip().split("=", 1) for p in line.split(";") if "=" in p)
    return {
        "genre": raw["genre"],
        "mood": raw["mood"],
        "energy": float(raw["energy"]),
        "likes_acoustic": raw.get("acoustic", "false").lower() == "true",
    }


def _load_doc(path: Path) -> Doc:
    title, keywords, profile, body = path.stem, "", None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.lower().startswith("keywords:"):
            keywords = line.split(":", 1)[1]
        elif line.lower().startswith("profile:"):
            profile = _parse_profile(line.split(":", 1)[1])
        else:
            body.append(line)
    if profile is None:
        raise ValueError(f"{path} has no 'profile:' line")
    return Doc(path.stem, title, f"{title} {keywords} {keywords} {' '.join(body)}", profile)


class Retriever:
    def __init__(self, kb_dir):
        paths = sorted(Path(kb_dir).glob("*.md"))
        if not paths:
            raise FileNotFoundError(f"No knowledge docs in {kb_dir}")
        self.docs: List[Doc] = [_load_doc(p) for p in paths]
        self._vec = TfidfVectorizer(stop_words=STOP_WORDS, sublinear_tf=True, ngram_range=(1, 2))
        self._matrix = self._vec.fit_transform(d.text for d in self.docs)

    def search(self, query: str, k: int = 3) -> List[Hit]:
        sims = cosine_similarity(self._vec.transform([query]), self._matrix)[0]
        order = sorted(range(len(self.docs)), key=lambda i: sims[i], reverse=True)[:k]
        return [Hit(self.docs[i].doc_id, self.docs[i].title, round(float(sims[i]), 3), self.docs[i].profile)
                for i in order]
