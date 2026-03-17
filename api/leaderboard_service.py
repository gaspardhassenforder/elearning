from open_notebook.database.repository import ensure_record_id, repo_query

async def get_company_leaderboard(company_id: str) -> list[dict]:
    results = await repo_query(
        """
        SELECT username, (points ?? 0) AS points
        FROM user
        WHERE company_id = $company_id
          AND role = 'learner'
        ORDER BY points DESC
        """,
        {"company_id": ensure_record_id(company_id)},
    )
    return [
        {"rank": i + 1, "username": row["username"], "points": row.get("points", 0)}
        for i, row in enumerate(results or [])
    ]
