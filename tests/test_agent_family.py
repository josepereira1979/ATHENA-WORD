from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from world.api.world_api import WorldAPI
from world.agents.agent_engine import AgentEngine
from world.families.family_engine import FamilyEngine

def main() -> None:
    print("=" * 70)
    print("ATHENA WORLD - TESTE AGENT <-> FAMILY")
    print("=" * 70)

    api = WorldAPI()
    agents = AgentEngine(auto_load=False)
    families = FamilyEngine(auto_load=False)

    world_date = api.state.world_date

    print()
    print(f"DATA INICIAL: {world_date}")

    agent_1 = agents.create_agent(
        world_date=world_date,
        first_name="Joao",
        last_name="Pereira",
        age=30,
        gender="M",
        profession="Engenheiro",
        capital=10000.0,
        income=2000.0,
        expenses=1000.0,
    )

    agent_2 = agents.create_agent(
        world_date=world_date,
        first_name="Maria",
        last_name="Pereira",
        age=29,
        gender="F",
        profession="Professora",
        capital=9000.0,
        income=1800.0,
        expenses=930.0,
    )

    family = families.create_family(
        world_date=world_date,
        family_name="Pereira",
        generation=1,
    )

    member_1 = families.add_member(
        family_id=family.family_id,
        agent_id=agent_1.agent_id,
        world_date=world_date,
    )

    member_2 = families.add_member(
        family_id=family.family_id,
        agent_id=agent_2.agent_id,
        world_date=world_date,
    )

    spouses = families.set_spouses(
        agent_id_1=agent_1.agent_id,
        agent_id_2=agent_2.agent_id,
        world_date=world_date,
    )

    link_1 = api.assign_agent_to_family(
        agent_engine=agents,
        agent_id=agent_1.agent_id,
        family_id=family.family_id,
    )

    link_2 = api.assign_agent_to_family(
        agent_engine=agents,
        agent_id=agent_2.agent_id,
        family_id=family.family_id,
    )

    saved_agent_1 = agents.get_agent(agent_1.agent_id)
    saved_agent_2 = agents.get_agent(agent_2.agent_id)

    print()
    print("AGENTES")
    print(f"Agent 1: {agent_1.agent_id} {agent_1.first_name}")
    print(f"Agent 2: {agent_2.agent_id} {agent_2.first_name}")

    print()
    print("FAMILIA")
    print(f"Family ID: {family.family_id}")
    print(f"Nome: {family.family_name}")

    print()
    print("LIGACOES")
    print(f"Agent 1 -> Family: {link_1}")
    print(f"Agent 2 -> Family: {link_2}")

    print()
    print("VERIFICACAO")
    print(f"Agent 1 family_id: {saved_agent_1.family_id}")
    print(f"Agent 2 family_id: {saved_agent_2.family_id}")

    family_ok = (
        member_1
        and member_2
        and spouses
    )

    agent_1_ok = (
        saved_agent_1.family_id == family.family_id
    )

    agent_2_ok = (
        saved_agent_2.family_id == family.family_id
    )

    print()
    print("RESULTADO")
    print(f"FAMILIA: {'OK' if family_ok else 'ERRO'}")
    print(f"AGENTE 1/FAMILIA: {'OK' if agent_1_ok else 'ERRO'}")
    print(f"AGENTE 2/FAMILIA: {'OK' if agent_2_ok else 'ERRO'}")
    print(f"CONJUGES: {'OK' if spouses else 'ERRO'}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()