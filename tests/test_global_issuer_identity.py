from pathlib import Path

from world.reality_bridge.global_listed_company_ingestion import GlobalListedCompanyIngestion
from world.reality_bridge.real_company_universe import RealCompanyUniverse


def test_global_ingestion_deduplicates_same_issuer_across_listings(tmp_path: Path):
    universe = RealCompanyUniverse(state_file=tmp_path / "universe.json")
    ingestion = GlobalListedCompanyIngestion(universe)
    result = ingestion.ingest([
        {
            "legal_name": "Example Holdings",
            "ticker": "EXA",
            "exchange": "NASDAQ",
            "country": "US",
            "source_identity": "LEI:EXAMPLE",
        },
        {
            "legal_name": "Example Holdings",
            "ticker": "EXB",
            "exchange": "NYSE",
            "country": "US",
            "source_identity": "LEI:EXAMPLE",
        },
    ])
    assert result["created_companies"] == 1
    assert result["created_listings"] == 2
    assert universe.count() == 1
    assert len(universe.get_all_listings()) == 2
