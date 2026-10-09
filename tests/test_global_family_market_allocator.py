from world.intelligence.global_family_market_allocator import GlobalFamilyMarketAllocator


def test_allocator_preview_empty_without_candidates():
    class F:
        def get_all_families(self):
            return []
    class U:
        def get_all_companies(self):
            return []
    class RB:
        universe = U()
    class C:
        def get_all_companies(self):
            return []
    class R:
        engines = {"FAMILY": F(), "REALITY_BRIDGE": RB(), "COMPANY": C()}
    allocator = GlobalFamilyMarketAllocator(R())
    result = allocator.preview()
    assert result["assignable"] == 0
    assert result["market_groups"] == {}
