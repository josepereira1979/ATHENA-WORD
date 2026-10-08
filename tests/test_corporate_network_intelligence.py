from world.intelligence.corporate_network_intelligence import CorporateNetworkIntelligence

class Family:
    def __init__(self, fid, rid):
        self.family_id=fid; self.real_company_id=rid; self.alive=True

class Families:
    def get_all_families(self): return [Family("F1","R1")]

class Network:
    def intelligence_for_company(self, cid):
        return {"relationships":[{"relationship_type":"SUPPLIES","source_real_company_id":"R2","target_real_company_id":cid,"confidence":0.9,"status":"CONFIRMED","evidence":"filing"}]}

class Learning:
    def __init__(self): self.rows=[]
    def record_experience(self, **kwargs): self.rows.append(kwargs)
    def _refresh_aggregates(self): pass
    def save(self): pass

def test_process_real_network():
    learning=Learning()
    result=CorporateNetworkIntelligence(Network(),Families(),learning).process("2027-01-03")
    assert result == {"families_processed":1,"signals_recorded":1}
    assert learning.rows[0]["knowledge_domain"] == "REAL_NETWORK"
