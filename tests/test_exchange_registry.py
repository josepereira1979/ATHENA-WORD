from world.reality_bridge.exchange_registry import classify_exchange, normalize_exchange


def test_exchange_aliases():
    assert normalize_exchange("NASDAQGS") == "NASDAQ"
    assert normalize_exchange("Euronext Lisbon") == "EURONEXT"
    assert classify_exchange("NSE India").group == "INDIA"
    assert classify_exchange("Tokyo").region == "ASIA_PACIFIC"


def test_unknown_exchange_is_safe():
    profile = classify_exchange("UNKNOWN-X")
    assert profile.region == "OTHER"
    assert profile.group == "OTHER"



def test_global_exchange_regions():
    assert classify_exchange("BMV").region == "AMERICAS"
    assert classify_exchange("BME").group == "SPAIN"
    assert classify_exchange("JSE").region == "AFRICA"
    assert classify_exchange("Tadawul").region == "MIDDLE_EAST"
    assert classify_exchange("SGX").group == "SINGAPORE"
