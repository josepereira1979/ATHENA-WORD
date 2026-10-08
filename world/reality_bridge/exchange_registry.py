from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class ExchangeProfile:
    code: str
    name: str
    country: str
    region: str
    group: str


EXCHANGES: Dict[str, ExchangeProfile] = {
    "NASDAQ": ExchangeProfile("NASDAQ", "Nasdaq Stock Market", "US", "AMERICAS", "USA"),
    "NYSE": ExchangeProfile("NYSE", "New York Stock Exchange", "US", "AMERICAS", "USA"),
    "LSE": ExchangeProfile("LSE", "London Stock Exchange", "GB", "EUROPE", "UK"),
    "EURONEXT": ExchangeProfile("EURONEXT", "Euronext", "EU", "EUROPE", "EUROPE"),
    "XETRA": ExchangeProfile("XETRA", "Deutsche Börse Xetra", "DE", "EUROPE", "GERMANY"),
    "SIX": ExchangeProfile("SIX", "SIX Swiss Exchange", "CH", "EUROPE", "SWITZERLAND"),
    "NSE": ExchangeProfile("NSE", "National Stock Exchange of India", "IN", "ASIA_PACIFIC", "INDIA"),
    "BSE": ExchangeProfile("BSE", "BSE India", "IN", "ASIA_PACIFIC", "INDIA"),
    "TSE": ExchangeProfile("TSE", "Tokyo Stock Exchange", "JP", "ASIA_PACIFIC", "JAPAN"),
    "SSE": ExchangeProfile("SSE", "Shanghai Stock Exchange", "CN", "ASIA_PACIFIC", "CHINA"),
    "SZSE": ExchangeProfile("SZSE", "Shenzhen Stock Exchange", "CN", "ASIA_PACIFIC", "CHINA"),
    "HKEX": ExchangeProfile("HKEX", "Hong Kong Exchanges and Clearing", "HK", "ASIA_PACIFIC", "HONG_KONG"),
    "KRX": ExchangeProfile("KRX", "Korea Exchange", "KR", "ASIA_PACIFIC", "SOUTH_KOREA"),
    "TWSE": ExchangeProfile("TWSE", "Taiwan Stock Exchange", "TW", "ASIA_PACIFIC", "TAIWAN"),
    "ASX": ExchangeProfile("ASX", "Australian Securities Exchange", "AU", "ASIA_PACIFIC", "AUSTRALIA"),
    "TSX": ExchangeProfile("TSX", "Toronto Stock Exchange", "CA", "AMERICAS", "CANADA"),
    "B3": ExchangeProfile("B3", "B3 Brasil Bolsa Balcão", "BR", "AMERICAS", "BRAZIL"),
}


def normalize_exchange(exchange: str) -> str:
    value = (exchange or "").upper().strip()
    aliases = {
        "NASDAQ": "NASDAQ", "NASDAQGS": "NASDAQ", "NASDAQGM": "NASDAQ",
        "NYSE": "NYSE", "LONDON": "LSE", "LSE": "LSE",
        "EURONEXT AMSTERDAM": "EURONEXT", "EURONEXT PARIS": "EURONEXT",
        "EURONEXT LISBON": "EURONEXT", "EURONEXT MILAN": "EURONEXT",
        "XETRA": "XETRA", "SIX": "SIX",
        "NSE INDIA": "NSE", "NATIONAL STOCK EXCHANGE OF INDIA": "NSE",
        "BSE INDIA": "BSE", "TOKYO": "TSE", "JPX": "TSE",
        "SHANGHAI": "SSE", "SHENZHEN": "SZSE", "HKEX": "HKEX",
        "KOREA": "KRX", "KRX": "KRX", "TAIWAN": "TWSE", "TWSE": "TWSE",
        "ASX": "ASX", "TSX": "TSX", "TMX": "TSX", "B3": "B3",
    }
    return aliases.get(value, value)


def classify_exchange(exchange: str) -> ExchangeProfile:
    code = normalize_exchange(exchange)
    return EXCHANGES.get(
        code,
        ExchangeProfile(code, exchange, "UNKNOWN", "OTHER", "OTHER"),
    )


def group_companies_by_market(companies: Iterable[object], listings_by_company: Dict[str, object]) -> Dict[str, Dict[str, List[object]]]:
    result: Dict[str, Dict[str, List[object]]] = {}
    for company in companies:
        listing = listings_by_company.get(company.real_company_id)
        if listing is None:
            continue
        profile = classify_exchange(getattr(listing, "exchange", ""))
        result.setdefault(profile.region, {}).setdefault(profile.group, []).append(company)
    return result


def market_counts(companies: Iterable[object], listings_by_company: Dict[str, object]) -> Dict[str, int]:
    grouped = group_companies_by_market(companies, listings_by_company)
    return {
        f"{region}/{group}": len(items)
        for region, groups in grouped.items()
        for group, items in groups.items()
    }
