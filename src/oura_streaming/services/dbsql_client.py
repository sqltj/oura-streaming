"""Minimal Databricks SQL Statement Execution client (async, httpx).

Uses /api/2.0/sql/statements with X-Databricks-SQL-HTTP-Path header to route
to a SQL Warehouse. Avoids extra dependencies, works in Databricks Apps.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class DBSQLConfig:
    host: str
    http_path: str
    token: str


class DBSQLClient:
    def __init__(self, cfg: DBSQLConfig, timeout: float = 30.0):
        self.cfg = cfg
        self.base_url = f"https://{cfg.host}"
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.cfg.token}",
            "X-Databricks-SQL-HTTP-Path": self.cfg.http_path,
            "Content-Type": "application/json",
        }

    async def execute(self, sql: str) -> Optional[List[List[Any]]]:
        """Execute SQL. Returns rows for SELECT (INLINE), else None."""
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            resp = await client.post(
                "/api/2.0/sql/statements",
                headers=self._headers(),
                json={
                    "statement": sql,
                    "disposition": "INLINE",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            statement_id = data.get("statement_id")
            # If already succeeded inline, return
            status = data.get("status", {}).get("state")
            if status in {"SUCCEEDED", "FAILED", "CANCELED"}:
                if status == "SUCCEEDED":
                    return self._extract_rows(data)
                raise RuntimeError(f"DBSQL error: {data}")

            # Poll until done
            while True:
                await asyncio.sleep(0.4)
                poll = await client.get(
                    f"/api/2.0/sql/statements/{statement_id}", headers=self._headers()
                )
                poll.raise_for_status()
                pdata = poll.json()
                pstate = pdata.get("status", {}).get("state")
                if pstate == "SUCCEEDED":
                    return self._extract_rows(pdata)
                if pstate in {"FAILED", "CANCELED"}:
                    raise RuntimeError(f"DBSQL error: {pdata}")

    def _extract_rows(self, payload: Dict[str, Any]) -> Optional[List[List[Any]]]:
        # Inline SELECT results live in result.data_array
        result = payload.get("result")
        if not result:
            return None
        return result.get("data_array")

