import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel

from app import security
from app.database import get_pool

router = APIRouter()

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization.removeprefix("Bearer ")
    try:
        payload = security.decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    return int(payload["sub"])


class ArticleResult(BaseModel):
    id: int
    title: str
    url: str
    source_name: str
    published_at: datetime | None
    score: float


@router.get("", response_model=list[ArticleResult])
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: int = Depends(get_current_user),
):
    tokens = _TOKEN_PATTERN.findall(q.lower())
    if not tokens:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query contains no searchable terms")

    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                a.id,
                a.title,
                a.url,
                a.source_name,
                a.published_at,
                SUM(tp.tfidf_weight) AS score
            FROM term_postings tp
            JOIN terms t ON tp.term_id = t.id
            JOIN articles a ON tp.article_id = a.id
            WHERE t.term = ANY($1)
            GROUP BY a.id, a.title, a.url, a.source_name, a.published_at
            ORDER BY score DESC
            LIMIT $2
            """,
            tokens,
            limit,
        )

        await conn.execute(
            """
            INSERT INTO user_search_events (user_id, query_text, normalized_query)
            VALUES ($1, $2, $3)
            """,
            user_id,
            q,
            " ".join(tokens),
        )

    return [ArticleResult(**dict(row)) for row in rows]
