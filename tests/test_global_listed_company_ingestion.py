from world.reality_bridge.global_listed_company_ingestion import GlobalListedCompanyIngestion
from world.reality_bridge.real_company_universe import RealCompanyUniverse


def test_ingestion_deduplicates_ticker_exchange(tmp_path):
    universe = RealCompanyUniverse(tmp_path / "universe.json", auto_load=False)
    ingest = GlobalListedCompanyIngestion(universe)

    records = [
        {"name": "Example Corp", "ticker": "EXM", "exchange": "NASDAQ", "country": "US"},
        {"name": "Example Corp", "ticker": "EXM", "exchange": "NASDAQ", "country": "US"},
        {"name": "Example ETF", "ticker": "EXETF", "exchange": "NASDAQ", "country": "US"},
    ]

    result = ingest.ingest(records)
    assert result["created_companies"] == 1
    assert result["created_listings"] == 1
    assert result["skipped"] == 2
    assert universe.count() == 1


def test_ingestion_classifies_market(tmp_path):
    universe = RealCompanyUniverse(tmp_path / "universe.json", auto_load=False)
    ingest = GlobalListedCompanyIngestion(universe)
    ingest.ingest([{"name": "India Corp", "ticker": "IND", "exchange": "NSE India", "country": "IN"}])

    company = universe.get_all_companies()[0]
    assert company.region == "ASIA_PACIFIC"
    assert company.exchange_group == "INDIA"
