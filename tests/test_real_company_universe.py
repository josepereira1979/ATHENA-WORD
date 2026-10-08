from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.reality_bridge.real_company_universe import RealCompanyUniverse


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state = Path(tmp) / "universe.json"
        universe = RealCompanyUniverse(state_file=state, auto_load=False)

        company = universe.create_company(
            legal_name="Example Corporation",
            country="USA",
            sector="TECHNOLOGY",
            industry="SEMICONDUCTORS",
            real_company_id="REAL-TEST-001",
        )

        first = universe.add_listing(
            real_company_id=company.real_company_id,
            exchange="NASDAQ",
            ticker="EXMP",
            country="USA",
            currency="USD",
            primary=True,
        )

        second = universe.add_listing(
            real_company_id=company.real_company_id,
            exchange="NYSE",
            ticker="EXMP2",
            country="USA",
            currency="USD",
            primary=False,
        )

        assert universe.count() == 1
        assert universe.active_count() == 1
        assert universe.get_company_by_ticker("exmp", "nasdaq").real_company_id == company.real_company_id
        assert universe.get_primary_listing(company.real_company_id).listing_id == first.listing_id
        assert second.listing_id in company.listing_ids

        reloaded = RealCompanyUniverse(state_file=state, auto_load=True)
        assert reloaded.count() == 1
        assert reloaded.get_company_by_ticker("EXMP", "NASDAQ").legal_name == "Example Corporation"

        print("REAL COMPANY UNIVERSE TEST: OK")


if __name__ == "__main__":
    main()
