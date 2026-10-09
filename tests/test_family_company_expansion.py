from world.intelligence.family_company_expansion import FamilyCompanyExpansion


class FakeListing:
    listing_id = "L1"


class FakeReal:
    def __init__(self, rid, name):
        self.real_company_id = rid
        self.legal_name = name
        self.active = True
        self.sector = "TECHNOLOGY"
        self.country = "US"


class FakeFamily:
    def __init__(self, fid):
        self.family_id = fid
        self.virtual_company_id = None
        self.alive = True


class FakeVirtual:
    def __init__(self, cid):
        self.company_id = cid
        self.real_company_id = None


class FakeUniverse:
    def __init__(self):
        self.rows = [FakeReal("R1", "Alpha"), FakeReal("R2", "Beta")]
    def get_all_companies(self):
        return self.rows
    def get_primary_listing(self, rid):
        return FakeListing()


class FakeFamilyEngine:
    def __init__(self):
        self.rows = [FakeFamily("F1"), FakeFamily("F2")]
    def get_all_families(self):
        return self.rows


class FakeCompanyEngine:
    def __init__(self):
        self.rows = []
        self.n = 0
    def get_all_companies(self):
        return self.rows
    def create_company(self, **kwargs):
        self.n += 1
        row = FakeVirtual(f"V{self.n}")
        self.rows.append(row)
        return row


class FakeRuntime:
    def assign_family_to_real_company(self, **kwargs):
        return kwargs


def test_expand_one_family_per_real_company():
    families = FakeFamilyEngine()
    companies = FakeCompanyEngine()
    service = FamilyCompanyExpansion(families, companies, FakeUniverse(), FakeRuntime())
    result = service.expand("2027-02-06")
    assert result["created_assignments"] == 2
    assert len(companies.rows) == 2
