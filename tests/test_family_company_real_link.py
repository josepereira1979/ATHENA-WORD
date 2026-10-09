from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.companies.company_engine import CompanyEngine
from world.families.family_engine import FamilyEngine


def test_family_company_real_link() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        families = FamilyEngine(state_file=Path(tmp) / "families.json", auto_load=False)
        companies = CompanyEngine(state_file=Path(tmp) / "companies.json", auto_load=False)

        family = families.create_family(
            world_date="2027-01-01",
            family_name="Pereira",
        )
        company = companies.create_company(
            world_date="2027-01-01",
            company_name="Example Corporation",
        )

        assert companies.link_real_company(company.company_id, "REAL-TEST-001")
        assert families.link_company(
            family.family_id,
            company.company_id,
            "REAL-TEST-001",
            "2027-01-01",
        )

        assert families.get_family_by_company(company.company_id).family_id == family.family_id
        assert families.get_intelligence_assignment(family.family_id)["real_company_id"] == "REAL-TEST-001"

        other_family = families.create_family(
            world_date="2027-01-01",
            family_name="Silva",
        )
        assert not families.link_company(
            other_family.family_id,
            company.company_id,
            "REAL-TEST-001",
            "2027-01-01",
        )

        print("FAMILY <-> COMPANY REAL LINK TEST: OK")


if __name__ == "__main__":
    test_family_company_real_link()
