"""CLI: python -m src.concierge "chill rainy-day study music"   (no args = interactive)."""
import sys

from src.agent import Agent
from src.recommender import load_songs
from src.retriever import Retriever


def build_agent() -> Agent:
    return Agent(load_songs("data/songs.csv"), Retriever("data/knowledge"))


def render(r) -> str:
    lines = [f'Query: "{r.query}"', f"Status: {r.status}   Confidence: {r.confidence:.2f}"]
    if r.sources:
        lines.append(f"Retrieved: {', '.join(r.sources)}")
    if r.profile:
        lines.append("Profile: " + ", ".join(f"{k}={v}" for k, v in r.profile.items()))
    for t in r.trace:
        if t["step"] in {"critique", "revise"}:
            lines.append("  agent> " + ", ".join(f"{k}={v}" for k, v in t.items()))
    for i, rec in enumerate(r.recs, 1):
        s = rec.song
        lines.append(f"{i}. {s['title']} - {s['artist']} [{s['genre']}/{s['mood']}] score {rec.score:.2f}")
        lines.append(f"     {rec.explanation}")
    if r.message:
        lines.append(f"Note: {r.message}")
    return "\n".join(lines)


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    agent = build_agent()
    if argv:
        print(render(agent.run(" ".join(argv))))
        return
    while True:
        q = input("What do you want to hear? (blank to quit) > ")
        if not q.strip():
            break
        print(render(agent.run(q)) + "\n")


if __name__ == "__main__":
    main()
