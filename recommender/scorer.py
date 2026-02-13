from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import FrozenSet, List, Optional

from plex.index import MovieRecord

WEIGHTS = {
    "genre": 0.40,
    "director": 0.25,
    "actor": 0.20,
    "decade": 0.15,
}


@dataclass
class ScoreBreakdown:
    genre: float = 0.0
    director: float = 0.0
    actor: float = 0.0
    decade: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.genre * WEIGHTS["genre"]
            + self.director * WEIGHTS["director"]
            + self.actor * WEIGHTS["actor"]
            + self.decade * WEIGHTS["decade"]
        )

    def explanations(self) -> List[str]:
        parts: List[str] = []
        if self.genre > 0:
            parts.append(f"Genre match: {self.genre:.0%}")
        if self.director > 0:
            parts.append("Shared director")
        if self.actor > 0:
            parts.append(f"Cast overlap: {self.actor:.0%}")
        if self.decade > 0:
            parts.append(f"Era similarity: {self.decade:.0%}")
        return parts


def score_genre(
    candidate_genres: FrozenSet[str], seed_genres: FrozenSet[str]
) -> float:
    if not seed_genres:
        return 0.0
    intersection = len(candidate_genres & seed_genres)
    return intersection / len(seed_genres)


def score_director(
    candidate_directors: FrozenSet[str], seed_directors: FrozenSet[str]
) -> float:
    if not seed_directors:
        return 0.0
    return 1.0 if candidate_directors & seed_directors else 0.0


def score_actor(
    candidate_actors: FrozenSet[str], seed_actors: FrozenSet[str]
) -> float:
    if not seed_actors or not candidate_actors:
        return 0.0
    intersection = len(candidate_actors & seed_actors)
    min_size = min(len(candidate_actors), len(seed_actors))
    return intersection / min_size


def score_decade(
    candidate_decade: Optional[int], seed_decade: Optional[int]
) -> float:
    if candidate_decade is None or seed_decade is None:
        return 0.0
    diff = abs(candidate_decade - seed_decade) // 10  # number of decades apart
    if diff >= 3:
        return 0.0
    return 1.0 - diff / 3.0


def build_seed_profile(seeds: List[MovieRecord]):
    """Merge seed fields into union sets and median decade."""
    genres: FrozenSet[str] = frozenset().union(*(s.genres for s in seeds))
    directors: FrozenSet[str] = frozenset().union(*(s.directors for s in seeds))
    actors: FrozenSet[str] = frozenset().union(*(s.actors for s in seeds))
    decades = [s.decade for s in seeds if s.decade is not None]
    seed_decade: Optional[int] = int(median(decades)) if decades else None
    return genres, directors, actors, seed_decade


def score_movie(
    candidate: MovieRecord,
    seed_genres: FrozenSet[str],
    seed_directors: FrozenSet[str],
    seed_actors: FrozenSet[str],
    seed_decade: Optional[int],
) -> ScoreBreakdown:
    return ScoreBreakdown(
        genre=score_genre(candidate.genres, seed_genres),
        director=score_director(candidate.directors, seed_directors),
        actor=score_actor(candidate.actors, seed_actors),
        decade=score_decade(candidate.decade, seed_decade),
    )
