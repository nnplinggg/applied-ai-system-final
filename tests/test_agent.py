import pytest

from src.agent import Agent
from src.recommender import load_songs
from src.retriever import Retriever


@pytest.fixture(scope="module")
def agent():
    return Agent(load_songs("data/songs.csv"), Retriever("data/knowledge"))


def test_study_query_recommends_lofi_and_uses_retrieval(agent):
    r = agent.run("quiet music for studying")
    assert r.status == "ok"
    assert r.recs[0].song["genre"] in {"lofi", "ambient"}
    assert r.sources and r.sources[0] == "study_focus"  # retrieval changed the profile
    assert r.confidence >= 0.5


def test_empty_input_is_rejected_not_crashed(agent):
    r = agent.run("")
    assert r.status == "rejected" and not r.recs


def test_gibberish_asks_for_clarification(agent):
    r = agent.run("zxqv plmk wrtb")
    assert r.status == "needs_clarification" and not r.recs


def test_explicit_genre_overrides_retrieved_genre(agent):
    r = agent.run("workout music but I want metal")
    assert r.profile["genre"] == "metal"


def test_artist_diversity_cap(agent):
    r = agent.run("chill lofi study focus beats")
    artists = [x.song["artist"] for x in r.recs]
    assert max(artists.count(a) for a in set(artists)) <= 2


def test_conflicting_request_is_flagged_low_confidence(agent):
    r = agent.run("sad heartbreak songs but very high energy")
    assert r.status == "low_confidence"
    assert "confirm" in r.message.lower()


def test_trace_records_steps(agent):
    r = agent.run("happy summer party")
    kinds = [t["step"] for t in r.trace]
    assert kinds[:3] == ["validate", "retrieve", "plan"] and "critique" in kinds


def test_explicit_genre_pulls_that_genres_mood_from_knowledge_base(agent):
    # regression: "metal" used to keep the workout doc's 'intense' mood and return a rock song
    assert agent.run("workout music but I want metal").recs[0].song["genre"] == "metal"


def test_generic_filler_words_do_not_retrieve(agent):
    # regression: the word 'vibes' used to match the 'island vibes' doc
    assert agent.run("vibes").status == "needs_clarification"
