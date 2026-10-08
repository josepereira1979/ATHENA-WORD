from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD - FAMILY ENGINE V01
# ============================================================
#
# Responsabilidade:
# - Criar famílias
# - Associar agentes a famílias
# - Relações familiares
# - Pais / filhos
# - Gerações
# - Património familiar
# - Herança
# - Transferência de conhecimento
# - Persistência
#
# O FAMILY ENGINE não cria agentes.
# Os agentes continuam a ser responsabilidade do AGENT ENGINE.
#
# O FAMILY ENGINE trabalha através dos agent_id.
# ============================================================


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "families_state.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# FAMILY
# ============================================================

@dataclass
class Family:

    family_id: str

    family_name: str

    created_world_date: str

    generation: int

    parent_family_id: Optional[str]

    member_ids: List[str] = field(default_factory=list)

    child_family_ids: List[str] = field(default_factory=list)

    wealth: float = 0.0

    inherited_wealth: float = 0.0

    knowledge_transfer_count: int = 0

    inheritance_count: int = 0

    alive: bool = True

    last_update_world_date: str = ""


# ============================================================
# FAMILY ENGINE
# ============================================================

class FamilyEngine:

    ENGINE_NAME = "ATHENA WORLD - FAMILY ENGINE"
    ENGINE_VERSION = "V01"

    def __init__(
        self,
        state_file: Path = STATE_FILE,
        auto_load: bool = True,
    ):

        self.state_file = Path(state_file)

        self.families: Dict[str, Family] = {}

        # Relações:
        #
        # child_agent_id -> parent_agent_ids
        self.parents: Dict[str, List[str]] = {}

        # parent_agent_id -> child_agent_ids
        self.children: Dict[str, List[str]] = {}

        # spouse_agent_id -> spouse_agent_id
        self.spouses: Dict[str, str] = {}

        if auto_load:
            self.load()

    # ========================================================
    # UTILITÁRIOS
    # ========================================================

    @staticmethod
    def _new_id(prefix: str) -> str:

        return (
            f"{prefix}-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    # ========================================================
    # CRIAR FAMÍLIA
    # ========================================================

    def create_family(
        self,
        world_date: str,
        family_name: Optional[str] = None,
        generation: int = 1,
        parent_family_id: Optional[str] = None,
    ) -> Family:

        if not family_name:

            family_names = [
                "Pereira",
                "Silva",
                "Costa",
                "Santos",
                "Oliveira",
                "Ferreira",
                "Martins",
                "Gomes",
                "Rodrigues",
                "Sousa",
            ]

            family_name = random.choice(
                family_names
            )

        family = Family(
            family_id=self._new_id("FAMILY"),
            family_name=family_name,
            created_world_date=world_date,
            generation=int(generation),
            parent_family_id=parent_family_id,
            member_ids=[],
            child_family_ids=[],
            wealth=0.0,
            inherited_wealth=0.0,
            knowledge_transfer_count=0,
            inheritance_count=0,
            alive=True,
            last_update_world_date=world_date,
        )

        self.families[
            family.family_id
        ] = family

        # Se esta família nasceu de outra,
        # registamos a ligação entre gerações.
        if parent_family_id:

            parent_family = self.get_family(
                parent_family_id
            )

            if parent_family:

                if (
                    family.family_id
                    not in parent_family.child_family_ids
                ):

                    parent_family.child_family_ids.append(
                        family.family_id
                    )

        self.save()

        return family

    # ========================================================
    # ADICIONAR MEMBRO
    # ========================================================

    def add_member(
        self,
        family_id: str,
        agent_id: str,
        world_date: str,
    ) -> bool:

        family = self.get_family(
            family_id
        )

        if family is None:
            return False

        if agent_id not in family.member_ids:

            family.member_ids.append(
                agent_id
            )

        family.last_update_world_date = (
            world_date
        )

        self.save()

        return True

    # ========================================================
    # REMOVER MEMBRO
    # ========================================================

    def remove_member(
        self,
        family_id: str,
        agent_id: str,
        world_date: str,
    ) -> bool:

        family = self.get_family(
            family_id
        )

        if family is None:
            return False

        if agent_id in family.member_ids:

            family.member_ids.remove(
                agent_id
            )

        family.last_update_world_date = (
            world_date
        )

        self.save()

        return True

    # ========================================================
    # CASAMENTO / COMPANHEIROS
    # ========================================================

    def set_spouses(
        self,
        agent_id_1: str,
        agent_id_2: str,
        world_date: str,
    ) -> bool:

        if agent_id_1 == agent_id_2:
            return False

        self.spouses[
            agent_id_1
        ] = agent_id_2

        self.spouses[
            agent_id_2
        ] = agent_id_1

        self._update_all_family_dates(
            world_date
        )

        self.save()

        return True

    def get_spouse(
        self,
        agent_id: str,
    ) -> Optional[str]:

        return self.spouses.get(
            agent_id
        )

    # ========================================================
    # RELAÇÃO PAIS / FILHOS
    # ========================================================

    def register_child(
        self,
        parent_agent_id_1: str,
        child_agent_id: str,
        world_date: str,
        parent_agent_id_2: Optional[str] = None,
    ) -> bool:

        if child_agent_id not in self.parents:

            self.parents[
                child_agent_id
            ] = []

        parent_list = self.parents[
            child_agent_id
        ]

        if (
            parent_agent_id_1
            not in parent_list
        ):

            parent_list.append(
                parent_agent_id_1
            )

        if (
            parent_agent_id_2
            and parent_agent_id_2
            not in parent_list
        ):

            parent_list.append(
                parent_agent_id_2
            )

        for parent_id in parent_list:

            if parent_id not in self.children:

                self.children[
                    parent_id
                ] = []

            if (
                child_agent_id
                not in self.children[parent_id]
            ):

                self.children[parent_id].append(
                    child_agent_id
                )

        self._update_all_family_dates(
            world_date
        )

        self.save()

        return True

    # ========================================================
    # CONSULTAR PAIS
    # ========================================================

    def get_parents(
        self,
        agent_id: str,
    ) -> List[str]:

        return list(
            self.parents.get(
                agent_id,
                []
            )
        )

    # ========================================================
    # CONSULTAR FILHOS
    # ========================================================

    def get_children(
        self,
        agent_id: str,
    ) -> List[str]:

        return list(
            self.children.get(
                agent_id,
                []
            )
        )

    # ========================================================
    # TRANSFERÊNCIA DE CONHECIMENTO
    # ========================================================

    def transfer_knowledge(
        self,
        from_agent_id: str,
        to_agent_id: str,
        knowledge: Dict[str, float],
        world_date: str,
    ) -> bool:

        # Nesta fase o Family Engine regista a transferência.
        #
        # A alteração efectiva do conhecimento do agente será
        # feita através do AGENT ENGINE / LEARNING ENGINE.
        #
        # Aqui apenas registamos o evento na estrutura familiar.

        from_family = self._find_family_by_agent(
            from_agent_id
        )

        to_family = self._find_family_by_agent(
            to_agent_id
        )

        if from_family:

            from_family.knowledge_transfer_count += 1
            from_family.last_update_world_date = (
                world_date
            )

        if to_family:

            to_family.knowledge_transfer_count += 1
            to_family.last_update_world_date = (
                world_date
            )

        self.save()

        return True

    # ========================================================
    # HERANÇA
    # ========================================================

    def register_inheritance(
        self,
        deceased_agent_id: str,
        beneficiary_agent_id: str,
        amount: float,
        world_date: str,
    ) -> bool:

        amount = max(
            0.0,
            float(amount)
        )

        deceased_family = (
            self._find_family_by_agent(
                deceased_agent_id
            )
        )

        beneficiary_family = (
            self._find_family_by_agent(
                beneficiary_agent_id
            )
        )

        if deceased_family:

            deceased_family.wealth = max(
                0.0,
                deceased_family.wealth
                - amount
            )

            deceased_family.inheritance_count += 1
            deceased_family.last_update_world_date = (
                world_date
            )

        if beneficiary_family:

            beneficiary_family.wealth += amount

            beneficiary_family.inherited_wealth += (
                amount
            )

            beneficiary_family.inheritance_count += 1
            beneficiary_family.last_update_world_date = (
                world_date
            )

        self.save()

        return True

    # ========================================================
    # PATRIMÓNIO
    # ========================================================

    def change_wealth(
        self,
        family_id: str,
        amount: float,
        world_date: str,
    ) -> bool:

        family = self.get_family(
            family_id
        )

        if family is None:
            return False

        family.wealth += float(amount)

        if family.wealth < 0:

            family.wealth = 0.0

        family.last_update_world_date = (
            world_date
        )

        self.save()

        return True

    # ========================================================
    # ENCONTRAR FAMÍLIA DO AGENTE
    # ========================================================

    def _find_family_by_agent(
        self,
        agent_id: str,
    ) -> Optional[Family]:

        for family in self.families.values():

            if agent_id in family.member_ids:

                return family

        return None

    def get_family_by_agent(
        self,
        agent_id: str,
    ) -> Optional[Family]:

        return self._find_family_by_agent(
            agent_id
        )

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_family(
        self,
        family_id: str,
    ) -> Optional[Family]:

        return self.families.get(
            family_id
        )

    def get_all_families(
        self,
    ) -> List[Family]:

        return list(
            self.families.values()
        )

    def count(self) -> int:

        return len(
            self.families
        )

    def alive_count(self) -> int:

        return sum(
            1
            for family in self.families.values()
            if family.alive
        )

    # ========================================================
    # ACTUALIZAÇÃO
    # ========================================================

    def update_family_date(
        self,
        family_id: str,
        world_date: str,
    ) -> bool:

        family = self.get_family(
            family_id
        )

        if family is None:
            return False

        family.last_update_world_date = (
            world_date
        )

        self.save()

        return True

    def _update_all_family_dates(
        self,
        world_date: str,
    ) -> None:

        for family in self.families.values():

            family.last_update_world_date = (
                world_date
            )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:

        payload = {
            "engine_name": self.ENGINE_NAME,
            "engine_version": self.ENGINE_VERSION,
            "updated_at": datetime.now().isoformat(),
            "families": [
                asdict(family)
                for family in self.families.values()
            ],
            "parents": self.parents,
            "children": self.children,
            "spouses": self.spouses,
        }

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.state_file.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=4,
            )

    def load(self) -> None:

        if not self.state_file.exists():
            return

        try:

            with self.state_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                payload = json.load(file)

            self.families = {}

            for data in payload.get(
                "families",
                [],
            ):

                family = Family(
                    **data
                )

                self.families[
                    family.family_id
                ] = family

            self.parents = {
                str(key): list(value)
                for key, value
                in payload.get(
                    "parents",
                    {}
                ).items()
            }

            self.children = {
                str(key): list(value)
                for key, value
                in payload.get(
                    "children",
                    {}
                ).items()
            }

            self.spouses = {
                str(key): str(value)
                for key, value
                in payload.get(
                    "spouses",
                    {}
                ).items()
            }

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ):

            self.families = {}
            self.parents = {}
            self.children = {}
            self.spouses = {}

    # ========================================================
    # RESET
    # ========================================================

    def reset(self) -> None:

        self.families = {}
        self.parents = {}
        self.children = {}
        self.spouses = {}

        if self.state_file.exists():

            self.state_file.unlink()


# ============================================================
# TESTE DIRECTO
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("ATHENA WORLD - FAMILY ENGINE")
    print("=" * 70)

    engine = FamilyEngine()

    # Teste limpo.
    engine.reset()

    world_date = "2026-11-03"

    # --------------------------------------------------------
    # Criar família
    # --------------------------------------------------------

    family = engine.create_family(
        world_date=world_date,
        family_name="Pereira",
        generation=1,
    )

    print(
        f"Family ID      : "
        f"{family.family_id}"
    )

    print(
        f"Family Name    : "
        f"{family.family_name}"
    )

    print(
        f"Generation     : "
        f"{family.generation}"
    )

    print(
        f"Members        : "
        f"{len(family.member_ids)}"
    )

    print(
        f"Wealth         : "
        f"{family.wealth:.2f}"
    )

    # --------------------------------------------------------
    # Adicionar dois agentes fictícios
    # --------------------------------------------------------

    agent_1 = "AGENT-TEST-001"
    agent_2 = "AGENT-TEST-002"
    child_1 = "AGENT-TEST-003"

    engine.add_member(
        family_id=family.family_id,
        agent_id=agent_1,
        world_date=world_date,
    )

    engine.add_member(
        family_id=family.family_id,
        agent_id=agent_2,
        world_date=world_date,
    )

    # --------------------------------------------------------
    # Criar relação
    # --------------------------------------------------------

    engine.set_spouses(
        agent_id_1=agent_1,
        agent_id_2=agent_2,
        world_date=world_date,
    )

    # --------------------------------------------------------
    # Filho
    # --------------------------------------------------------

    engine.add_member(
        family_id=family.family_id,
        agent_id=child_1,
        world_date=world_date,
    )

    engine.register_child(
        parent_agent_id_1=agent_1,
        parent_agent_id_2=agent_2,
        child_agent_id=child_1,
        world_date=world_date,
    )

    # --------------------------------------------------------
    # Património
    # --------------------------------------------------------

    engine.change_wealth(
        family_id=family.family_id,
        amount=50000.0,
        world_date=world_date,
    )

    # --------------------------------------------------------
    # Conhecimento
    # --------------------------------------------------------

    engine.transfer_knowledge(
        from_agent_id=agent_1,
        to_agent_id=child_1,
        knowledge={
            "economics": 0.5,
            "finance": 0.3,
            "technology": 0.7,
        },
        world_date=world_date,
    )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    family = engine.get_family(
        family.family_id
    )

    print()
    print("=" * 70)
    print("RESULTADO DO TESTE")
    print("-" * 70)

    print(
        f"Famílias       : "
        f"{engine.count()}"
    )

    print(
        f"Membros        : "
        f"{len(family.member_ids)}"
    )

    print(
        f"Pais do filho  : "
        f"{engine.get_parents(child_1)}"
    )

    print(
        f"Filhos do pai  : "
        f"{engine.get_children(agent_1)}"
    )

    print(
        f"Companheiro    : "
        f"{engine.get_spouse(agent_1)}"
    )

    print(
        f"Património     : "
        f"{family.wealth:.2f}"
    )

    print(
        f"Transf. conhec.: "
        f"{family.knowledge_transfer_count}"
    )

    print(
        f"Heranças       : "
        f"{family.inheritance_count}"
    )

    print(
        f"Data           : "
        f"{family.last_update_world_date}"
    )

    print("=" * 70)

    print()
    print(
        "ATHENA WORLD - FAMILY ENGINE V01 "
        "carregado com sucesso."
    )

    print("=" * 70)