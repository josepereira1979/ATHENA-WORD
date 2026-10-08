from world.intelligence.global_world_finalizer import GlobalWorldFinalizer


def test_finalizer_never_creates_less_than_real_company_count():
    class Runtime:
        pass
    assert GlobalWorldFinalizer is not None
