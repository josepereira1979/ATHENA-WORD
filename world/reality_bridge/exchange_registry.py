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
    "BMV": ExchangeProfile("BMV", "Bolsa Mexicana de Valores", "MX", "AMERICAS", "MEXICO"),
    "BME": ExchangeProfile("BME", "Bolsas y Mercados Españoles", "ES", "EUROPE", "SPAIN"),
    "MILAN": ExchangeProfile("MILAN", "Borsa Italiana", "IT", "EUROPE", "ITALY"),
    "OMX": ExchangeProfile("OMX", "Nasdaq Nordic", "EU", "EUROPE", "NORDICS"),
    "OSLO": ExchangeProfile("OSLO", "Oslo Børs", "NO", "EUROPE", "NORWAY"),
    "COPENHAGEN": ExchangeProfile("COPENHAGEN", "Nasdaq Copenhagen", "DK", "EUROPE", "DENMARK"),
    "STOCKHOLM": ExchangeProfile("STOCKHOLM", "Nasdaq Stockholm", "SE", "EUROPE", "SWEDEN"),
    "HELSINKI": ExchangeProfile("HELSINKI", "Nasdaq Helsinki", "FI", "EUROPE", "FINLAND"),
    "SGX": ExchangeProfile("SGX", "Singapore Exchange", "SG", "ASIA_PACIFIC", "SINGAPORE"),
    "JSE": ExchangeProfile("JSE", "Johannesburg Stock Exchange", "ZA", "AFRICA", "SOUTH_AFRICA"),
    "TADAWUL": ExchangeProfile("TADAWUL", "Saudi Exchange", "SA", "MIDDLE_EAST", "SAUDI_ARABIA"),
    "ADX": ExchangeProfile("ADX", "Abu Dhabi Securities Exchange", "AE", "MIDDLE_EAST", "UAE"),
    "DFM": ExchangeProfile("DFM", "Dubai Financial Market", "AE", "MIDDLE_EAST", "UAE"),
    "QSE": ExchangeProfile("QSE", "Qatar Stock Exchange", "QA", "MIDDLE_EAST", "QATAR"),
    "IDX": ExchangeProfile("IDX", "Indonesia Stock Exchange", "ID", "ASIA_PACIFIC", "INDONESIA"),
    "SET": ExchangeProfile("SET", "Stock Exchange of Thailand", "TH", "ASIA_PACIFIC", "THAILAND"),
    "MYX": ExchangeProfile("MYX", "Bursa Malaysia", "MY", "ASIA_PACIFIC", "MALAYSIA"),
    "NZSX": ExchangeProfile("NZSX", "New Zealand Exchange", "NZ", "ASIA_PACIFIC", "NEW_ZEALAND"),
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
        "ASX": "ASX", "TSX": "TSX", "TMX": "TSX", "B3": "B3", "BMV": "BMV", "BME": "BME", "BORSA ITALIANA": "MILAN", "MILAN": "MILAN", "NASDAQ NORDIC": "OMX", "OSLO BORS": "OSLO", "OSLO BØRS": "OSLO", "COPENHAGEN": "COPENHAGEN", "STOCKHOLM": "STOCKHOLM", "HELSINKI": "HELSINKI", "SGX": "SGX", "JSE": "JSE", "TADAWUL": "TADAWUL", "SAUDI EXCHANGE": "TADAWUL", "ADX": "ADX", "DFM": "DFM", "QSE": "QSE", "IDX": "IDX", "SET": "SET", "MYX": "MYX", "BURSA MALAYSIA": "MYX", "NZSX": "NZSX",
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



MARKET_SOURCE_REGISTRY = {
    "NASDAQ": {"region": "AMERICAS", "country": "US", "source_type": "EXCHANGE"},
    "NYSE": {"region": "AMERICAS", "country": "US", "source_type": "EXCHANGE"},
    "TSX": {"region": "AMERICAS", "country": "CA", "source_type": "EXCHANGE"},
    "BMV": {"region": "AMERICAS", "country": "MX", "source_type": "EXCHANGE"},
    "B3": {"region": "AMERICAS", "country": "BR", "source_type": "EXCHANGE"},
    "LSE": {"region": "EUROPE", "country": "GB", "source_type": "EXCHANGE"},
    "EURONEXT": {"region": "EUROPE", "country": "EU", "source_type": "EXCHANGE"},
    "XETRA": {"region": "EUROPE", "country": "DE", "source_type": "EXCHANGE"},
    "BME": {"region": "EUROPE", "country": "ES", "source_type": "EXCHANGE"},
    "MILAN": {"region": "EUROPE", "country": "IT", "source_type": "EXCHANGE"},
    "SIX": {"region": "EUROPE", "country": "CH", "source_type": "EXCHANGE"},
    "OMX": {"region": "EUROPE", "country": "EU", "source_type": "EXCHANGE"},
    "NSE": {"region": "ASIA_PACIFIC", "country": "IN", "source_type": "EXCHANGE"},
    "BSE": {"region": "ASIA_PACIFIC", "country": "IN", "source_type": "EXCHANGE"},
    "TSE": {"region": "ASIA_PACIFIC", "country": "JP", "source_type": "EXCHANGE"},
    "SSE": {"region": "ASIA_PACIFIC", "country": "CN", "source_type": "EXCHANGE"},
    "SZSE": {"region": "ASIA_PACIFIC", "country": "CN", "source_type": "EXCHANGE"},
    "HKEX": {"region": "ASIA_PACIFIC", "country": "HK", "source_type": "EXCHANGE"},
    "KRX": {"region": "ASIA_PACIFIC", "country": "KR", "source_type": "EXCHANGE"},
    "TWSE": {"region": "ASIA_PACIFIC", "country": "TW", "source_type": "EXCHANGE"},
    "SGX": {"region": "ASIA_PACIFIC", "country": "SG", "source_type": "EXCHANGE"},
    "JSE": {"region": "AFRICA", "country": "ZA", "source_type": "EXCHANGE"},
    "TADAWUL": {"region": "MIDDLE_EAST", "country": "SA", "source_type": "EXCHANGE"},
    "ADX": {"region": "MIDDLE_EAST", "country": "AE", "source_type": "EXCHANGE"},
    "DFM": {"region": "MIDDLE_EAST", "country": "AE", "source_type": "EXCHANGE"},
    "QSE": {"region": "MIDDLE_EAST", "country": "QA", "source_type": "EXCHANGE"},
    "ASX": {"region": "ASIA_PACIFIC", "country": "AU", "source_type": "EXCHANGE"},
    "NZSX": {"region": "ASIA_PACIFIC", "country": "NZ", "source_type": "EXCHANGE"},
}


def market_source(exchange: str) -> Dict[str, str]:
    return MARKET_SOURCE_REGISTRY.get(normalize_exchange(exchange), {
        "region": "OTHER",
        "country": "UNKNOWN",
        "source_type": "UNKNOWN",
    })
