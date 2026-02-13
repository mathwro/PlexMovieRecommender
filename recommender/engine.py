from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from plex.index import MovieIndex, MovieRecord
from recommender.scorer import (
    ScoreBreakdown,
    build_seed_profile,
    score_movie,
)


@dataclass
class Recommendation:
    movie: MovieRecord
    score: float
    breakdown: ScoreBreakdown
    explanation: List[str]


class Recommender:
    def __init__(self, index: MovieIndex):
        self.index = index

    def _fallback_top_rated(self, n: int, pool: Optional[List[str]] = None) -> List[Recommendation]:
        """Return top-rated unwatched movies when no history is available."""
        keys = pool if pool is not None else list(self.index.records.keys())
        candidates = [
            self.index.records[k]
            for k in keys
            if k in self.index.records and not self.index.records[k].watched
        ]
        candidates.sort(
            key=lambda m: m.audience_rating or m.rating or 0.0,
            reverse=True,
        )
        return [
            Recommendation(
                movie=m,
                score=m.audience_rating or m.rating or 0.0,
                breakdown=ScoreBreakdown(),
                explanation=["Top rated in library"],
            )
            for m in candidates[:n]
        ]

    def _rank(
        self,
        pool_keys: List[str],
        seed_genres,
        seed_directors,
        seed_actors,
        seed_decade,
        n: int,
    ) -> List[Recommendation]:
        results: List[Recommendation] = []
        for key in pool_keys:
            record = self.index.records.get(key)
            if record is None or record.watched:
                continue
            bd = score_movie(record, seed_genres, seed_directors, seed_actors, seed_decade)
            results.append(
                Recommendation(
                    movie=record,
                    score=bd.total,
                    breakdown=bd,
                    explanation=bd.explanations() or ["Library pick"],
                )
            )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:n]

    def recommend_from_history(self, n: int = 10, seed_count: int = 5) -> List[Recommendation]:
        # Seeds = last seed_count watched movies that exist in the index
        seed_keys = [
            k for k in self.index.watched_order if k in self.index.records
        ][:seed_count]

        if not seed_keys:
            return self._fallback_top_rated(n)

        seeds = [self.index.records[k] for k in seed_keys]
        seed_genres, seed_directors, seed_actors, seed_decade = build_seed_profile(seeds)

        pool = [k for k in self.index.records if k not in set(self.index.watched_order)]
        recs = self._rank(pool, seed_genres, seed_directors, seed_actors, seed_decade, n)

        if not recs:
            return self._fallback_top_rated(n)
        return recs

    def recommend_by_genre(self, genre: str, n: int = 10) -> List[Recommendation]:
        genre_lower = genre.lower()
        pool_keys = self.index.genre_index.get(genre_lower, [])

        if not pool_keys:
            # Try partial match
            for g, keys in self.index.genre_index.items():
                if genre_lower in g:
                    pool_keys = keys
                    break

        if not pool_keys:
            return []

        # Build seed profile from watched movies in this genre
        watched_in_genre = [
            self.index.records[k]
            for k in pool_keys
            if k in self.index.records and self.index.records[k].watched
        ]

        if watched_in_genre:
            seed_genres, seed_directors, seed_actors, seed_decade = build_seed_profile(
                watched_in_genre[:5]
            )
            recs = self._rank(
                pool_keys, seed_genres, seed_directors, seed_actors, seed_decade, n
            )
        else:
            recs = self._fallback_top_rated(n, pool=pool_keys)

        return recs
