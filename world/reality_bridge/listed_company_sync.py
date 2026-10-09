from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"


@dataclass(frozen=True)
class ListedCompanyRecord:
    cik: str
    legal_name: str
    ticker: str
    exchange: str
    country: str = "US"


class ListedCompanySync:
    """Importa empresas cotadas a partir de fontes oficiais, sem inventar empresas.

    A primeira fonte é o ficheiro oficial SEC CIK/ticker/exchange. O desenho permite
    acrescentar adaptadores para outras bolsas sem alterar o modelo canónico.
    """

    ENGINE_NAME = "ATHENA WORLD - LISTED COMPANY SYNC"
    ENGINE_VERSION = "V01"

    EXCLUDED_EXCHANGES = {"OTC", "OTCBB", "OTCQB", "OTCQX", "PINK"}
    FUND_PATTERNS = (
        r"\bETF\b", r"\bETN\b", r"\bTRUST\b", r"\bFUND\b",
        r"\bINDEX FUND\b", r"\bMUTUAL FUND\b", r"\bSPDR\b",
        r"\bISHARES\b", r"\bVANGUARD\b", r"\bINVESCO\b",
    )

    def fetch_sec(self, user_agent: str) -> List[ListedCompanyRecord]:
        if not user_agent or "@" not in user_agent:
            raise ValueError("A SEC exige um User-Agent identificável, idealmente com email.")
        request = urllib.request.Request(
            SEC_TICKERS_URL,
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return self.parse_sec_payload(payload)

    @classmethod
    def parse_sec_payload(cls, payload: Dict[str, Any]) -> List[ListedCompanyRecord]:
        rows = payload.get("data", [])
        records: List[ListedCompanyRecord] = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) < 4:
                continue
            cik, name, ticker, exchange = row[:4]
            exchange = str(exchange or "").strip().upper()
            ticker = str(ticker or "").strip().upper()
            name = str(name or "").strip()
            if not name or not ticker or exchange in cls.EXCLUDED_EXCHANGES:
                continue
            if any(re.search(pattern, name.upper()) for pattern in cls.FUND_PATTERNS):
                continue
            records.append(
                ListedCompanyRecord(
                    cik=str(cik).zfill(10),
                    legal_name=name,
                    ticker=ticker,
                    exchange=exchange,
                )
            )
        return records

    def sync_to_universe(
        self,
        universe,
        records: Iterable[ListedCompanyRecord],
        max_new: Optional[int] = None,
    ) -> Dict[str, int]:
        added = 0
        skipped = 0
        existing_ciks = {
            getattr(company, "source_cik", None)
            for company in universe.get_all_companies()
        }
        for record in records:
            if max_new is not None and added >= max_new:
                break
            if record.cik in existing_ciks:
                skipped += 1
                continue
            if universe.get_company_by_ticker(record.ticker, record.exchange):
                skipped += 1
                continue
            company = universe.create_company(
                legal_name=record.legal_name,
                country=record.country,
                sector="UNKNOWN",
                industry="UNKNOWN",
                real_company_id=f"REAL-SEC-{record.cik}",
                source_cik=record.cik,
            )
            company.source_cik = record.cik
            listing = universe.add_listing(
                real_company_id=company.real_company_id,
                exchange=record.exchange,
                ticker=record.ticker,
                country=record.country,
                currency="USD",
                primary=True,
            )
            # Persist the source identity without breaking the canonical model.
            universe.save()
            existing_ciks.add(record.cik)
            added += 1
        return {"added": added, "skipped": skipped}
