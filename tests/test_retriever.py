from pathlib import Path

from src.recommender import load_songs
from src.retriever import Retriever

KB = Path("data/knowledge")


def test_retrieves_study_doc_for_study_query():
    hits = Retriever(KB).search("quiet music for studying and reading", k=2)
    assert hits and hits[0].doc_id == "study_focus"
    assert hits[0].score > 0


def test_gibberish_scores_zero():
    hits = Retriever(KB).search("zxqv plmk wrtb", k=2)
    assert not hits or hits[0].score == 0


def test_every_doc_profile_uses_values_that_exist_in_catalog():
    songs = load_songs("data/songs.csv")
    genres = {s["genre"] for s in songs}
    moods = {s["mood"] for s in songs}
    for doc in Retriever(KB).docs:
        assert doc.profile["genre"] in genres, doc.doc_id
        assert doc.profile["mood"] in moods, doc.doc_id
        assert 0.0 <= doc.profile["energy"] <= 1.0
