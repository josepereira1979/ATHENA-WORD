import sys

sys.path.insert(0, r"C:\Users\jpereira\ATHENA_WORLD")

from world.core.world_core import WorldCore
from world.api.world_api import WorldAPI
from world.agents.agent_engine import AgentEngine


core = WorldCore()
api = WorldAPI()
agents = AgentEngine()

agent = agents.create_agent(
    first_name="Joao",
    last_name="Pereira",
    age=30,
    profession="Engenheiro",
    capital=10000.0,
    income=3000.0,
    expenses=2000.0,
    world_date=core.get_world_date(),
)

inicio = agent.capital

print("=" * 60)
print("TESTE WORLD CORE + API + AGENT")
print("=" * 60)

print()
print("INICIO")
print("Data          :", core.get_world_date())
print("Tick          :", core.get_tick())
print("Capital       :", round(inicio, 2))
print("Idade         :", agent.age)

for _ in range(30):
    core.advance(1)

    api.sync_world(
        core.get_world_date(),
        core.get_tick(),
        core.state.total_ticks,
    )

    agents.process_tick(
        core.get_world_date()
    )

agent = agents.get_agent(agent.agent_id)

print()
print("FIM")
print("Data          :", core.get_world_date())
print("Tick          :", core.get_tick())
print("API           :", api.get_world_time())
print("Capital       :", round(agent.capital, 2))
print("Idade         :", agent.age)
print("Ticks agente  :", agent.total_ticks_processed)

print()
print("VERIFICAÇÕES")

if core.get_tick() == 30:
    print("WORLD CORE    : OK")
else:
    print("WORLD CORE    : ERRO")

if api.state.tick == core.get_tick():
    print("API           : OK")
else:
    print("API           : ERRO")

if agent.total_ticks_processed == 30:
    print("AGENT ENGINE  : OK")
else:
    print("AGENT ENGINE  : ERRO")

esperado = inicio + 1000.0

if abs(agent.capital - esperado) < 0.01:
    print("CAPITAL       : OK")
else:
    print("CAPITAL       : ERRO")
    print("Esperado      :", round(esperado, 2))

print()
print("=" * 60)
print("TESTE CONCLUIDO")
print("=" * 60)