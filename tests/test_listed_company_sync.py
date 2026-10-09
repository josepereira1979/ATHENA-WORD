from world.reality_bridge.listed_company_sync import ListedCompanySync


def test_parse_sec_filters_funds_and_otc():
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [
            [1, "ALPHA CORP", "ALPH", "Nasdaq"],
            [2, "BETA ETF TRUST", "BETF", "NYSE"],
            [3, "GAMMA LTD", "GAMM", "OTC"],
        ],
    }
    rows = ListedCompanySync.parse_sec_payload(payload)
    assert len(rows) == 1
    assert rows[0].ticker == "ALPH"
    assert rows[0].exchange == "NASDAQ"


def test_parse_preserves_real_company_identity():
    payload = {
        "data": [[123, "NVIDIA CORP", "NVDA", "Nasdaq"]]
    }
    row = ListedCompanySync.parse_sec_payload(payload)[0]
    assert row.cik == "0000000123"
    assert row.legal_name == "NVIDIA CORP"
