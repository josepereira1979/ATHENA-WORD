from __future__ import annotations

import json
import random
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================
# ATHENA WORLD
# MARKET ENGINE V01
# ============================================================
#
# Responsabilidade:
#   - mercados
#   - ativos
#   - compradores
#   - vendedores
#   - ordens
#   - livro de ordens
#   - transações
#   - preços
#   - volume
#   - liquidez
#   - spread
#   - volatilidade
#   - formação de preço
#
# Este motor representa os mercados internos da ATHENA WORLD.
#
# NÃO controla diretamente:
#   - agentes
#   - empresas
#   - economia
#   - bancos
#   - recursos
#
# Esses sistemas comunicam com o Market Engine através
# de interfaces/eventos numa fase posterior.
#
# ============================================================


ENGINE_NAME = "ATHENA WORLD - MARKET ENGINE"
ENGINE_VERSION = "V01"

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STATE_FILE = DATA_DIR / "market_state.json"


# ============================================================
# ATIVO
# ============================================================


@dataclass
class Asset:
    asset_id: str
    symbol: str
    name: str
    asset_type: str

    last_price: float = 0.0
    previous_price: float = 0.0

    total_volume: float = 0.0
    total_trades: int = 0

    volatility: float = 0.0
    liquidity: float = 1.0

    best_bid: float = 0.0
    best_ask: float = 0.0
    spread: float = 0.0

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ORDEM
# ============================================================


@dataclass
class Order:
    order_id: str
    asset_id: str
    agent_id: str

    side: str
    quantity: float
    price: float

    remaining_quantity: float = 0.0

    status: str = "OPEN"

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# NEGÓCIO
# ============================================================


@dataclass
class Trade:
    trade_id: str
    asset_id: str

    buyer_agent_id: str
    seller_agent_id: str

    quantity: float
    price: float

    tick: int
    world_date: str

    created_at: str = ""


# ============================================================
# MERCADO
# ============================================================


@dataclass
class Market:
    market_id: str
    name: str
    market_type: str

    asset_ids: List[str] = field(
        default_factory=list
    )

    order_ids: List[str] = field(
        default_factory=list
    )

    trade_ids: List[str] = field(
        default_factory=list
    )

    active: bool = True

    created_at: str = ""
    updated_at: str = ""


# ============================================================
# ESTADO
# ============================================================


@dataclass
class MarketState:
    world_date: str

    tick: int = 0
    total_ticks: int = 0

    markets: Dict[str, Market] = field(
        default_factory=dict
    )

    assets: Dict[str, Asset] = field(
        default_factory=dict
    )

    orders: Dict[str, Order] = field(
        default_factory=dict
    )

    trades: Dict[str, Trade] = field(
        default_factory=dict
    )

    total_markets: int = 0
    total_assets: int = 0
    total_orders: int = 0
    total_trades: int = 0

    created_at: str = ""
    updated_at: str = ""

    engine_name: str = ENGINE_NAME
    engine_version: str = ENGINE_VERSION


# ============================================================
# MARKET ENGINE
# ============================================================


class MarketEngine:

    def __init__(
        self,
        state_file: Optional[Path] = None,
        random_seed: Optional[int] = None,
    ) -> None:

        self.state_file = (
            Path(state_file)
            if state_file
            else STATE_FILE
        )

        DATA_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.state: Optional[MarketState] = None

        self.random = random.Random(
            random_seed
        )

    # ========================================================
    # UTILIDADES
    # ========================================================

    @staticmethod
    def _now() -> str:
        return datetime.now().astimezone().isoformat()

    @staticmethod
    def _safe_float(
        value: float,
    ) -> float:
        return max(0.0, float(value))

    @staticmethod
    def _normalize_side(
        side: str,
    ) -> str:

        side = str(side).upper().strip()

        if side not in {"BUY", "SELL"}:
            raise ValueError(
                "Order side must be BUY or SELL."
            )

        return side

    # ========================================================
    # INICIALIZAÇÃO
    # ========================================================

    def initialize(
        self,
        world_date: str,
    ) -> MarketState:

        now = self._now()

        self.state = MarketState(
            world_date=world_date,
            tick=0,
            total_ticks=0,
            markets={},
            assets={},
            orders={},
            trades={},
            total_markets=0,
            total_assets=0,
            total_orders=0,
            total_trades=0,
            created_at=now,
            updated_at=now,
        )

        self._save()

        return self.state

    # ========================================================
    # MERCADOS
    # ========================================================

    def create_market(
        self,
        market_id: str,
        name: str,
        market_type: str = "EXCHANGE",
    ) -> Market:

        self._require_state()

        if market_id in self.state.markets:
            raise ValueError(
                f"Market already exists: {market_id}"
            )

        now = self._now()

        market = Market(
            market_id=market_id,
            name=name,
            market_type=market_type,
            created_at=now,
            updated_at=now,
        )

        self.state.markets[market_id] = market

        self._refresh_aggregates()
        self._touch()
        self._save()

        return market

    # ========================================================
    # ATIVOS
    # ========================================================

    def create_asset(
        self,
        asset_id: str,
        symbol: str,
        name: str,
        asset_type: str,
        initial_price: float,
        market_id: Optional[str] = None,
    ) -> Asset:

        self._require_state()

        if asset_id in self.state.assets:
            raise ValueError(
                f"Asset already exists: {asset_id}"
            )

        price = self._safe_float(
            initial_price
        )

        now = self._now()

        asset = Asset(
            asset_id=asset_id,
            symbol=symbol,
            name=name,
            asset_type=asset_type,
            last_price=price,
            previous_price=price,
            total_volume=0.0,
            total_trades=0,
            volatility=0.0,
            liquidity=1.0,
            best_bid=0.0,
            best_ask=0.0,
            spread=0.0,
            active=True,
            created_at=now,
            updated_at=now,
        )

        self.state.assets[asset_id] = asset

        if market_id is not None:

            market = self.get_market(
                market_id
            )

            market.asset_ids.append(
                asset_id
            )

            market.updated_at = now

        self._refresh_aggregates()
        self._touch()
        self._save()

        return asset

    # ========================================================
    # CONSULTAS
    # ========================================================

    def get_market(
        self,
        market_id: str,
    ) -> Market:

        self._require_state()

        try:
            return self.state.markets[
                market_id
            ]
        except KeyError:
            raise KeyError(
                f"Market not found: {market_id}"
            )

    def get_asset(
        self,
        asset_id: str,
    ) -> Asset:

        self._require_state()

        try:
            return self.state.assets[
                asset_id
            ]
        except KeyError:
            raise KeyError(
                f"Asset not found: {asset_id}"
            )

    def get_all_assets(
        self,
    ) -> List[Asset]:

        self._require_state()

        return list(
            self.state.assets.values()
        )

    # ========================================================
    # ORDENS
    # ========================================================

    def place_order(
        self,
        asset_id: str,
        agent_id: str,
        side: str,
        quantity: float,
        price: float,
    ) -> Order:

        self._require_state()

        asset = self.get_asset(
            asset_id
        )

        if not asset.active:
            raise ValueError(
                f"Asset is inactive: {asset_id}"
            )

        quantity = self._safe_float(
            quantity
        )

        price = self._safe_float(
            price
        )

        if quantity <= 0:
            raise ValueError(
                "Order quantity must be greater than zero."
            )

        if price <= 0:
            raise ValueError(
                "Order price must be greater than zero."
            )

        side = self._normalize_side(
            side
        )

        now = self._now()

        order_id = (
            "ORDER-"
            + uuid.uuid4().hex[:12].upper()
        )

        order = Order(
            order_id=order_id,
            asset_id=asset_id,
            agent_id=agent_id,
            side=side,
            quantity=quantity,
            price=price,
            remaining_quantity=quantity,
            status="OPEN",
            created_at=now,
            updated_at=now,
        )

        self.state.orders[
            order_id
        ] = order

        self._match_orders(
            asset_id
        )

        self._refresh_aggregates()
        self._touch()
        self._save()

        return order

    # ========================================================
    # LIVRO DE ORDENS
    # ========================================================

    def get_order_book(
        self,
        asset_id: str,
    ) -> Dict[str, List[Order]]:

        self._require_state()

        self.get_asset(asset_id)

        buy_orders = []
        sell_orders = []

        for order in self.state.orders.values():

            if order.asset_id != asset_id:
                continue

            if order.status != "OPEN":
                continue

            if order.remaining_quantity <= 0:
                continue

            if order.side == "BUY":
                buy_orders.append(order)

            elif order.side == "SELL":
                sell_orders.append(order)

        buy_orders.sort(
            key=lambda item: (
                -item.price,
                item.created_at,
            )
        )

        sell_orders.sort(
            key=lambda item: (
                item.price,
                item.created_at,
            )
        )

        return {
            "bids": buy_orders,
            "asks": sell_orders,
        }

    # ========================================================
    # MATCHING
    # ========================================================

    def _match_orders(
        self,
        asset_id: str,
    ) -> None:

        while True:

            book = self.get_order_book(
                asset_id
            )

            bids = book["bids"]
            asks = book["asks"]

            if not bids or not asks:
                break

            best_bid = bids[0]
            best_ask = asks[0]

            if best_bid.price < best_ask.price:
                break

            quantity = min(
                best_bid.remaining_quantity,
                best_ask.remaining_quantity,
            )

            trade_price = (
                best_ask.price
            )

            self._execute_trade(
                buy_order=best_bid,
                sell_order=best_ask,
                quantity=quantity,
                price=trade_price,
            )

    # ========================================================
    # EXECUÇÃO
    # ========================================================

    def _execute_trade(
        self,
        buy_order: Order,
        sell_order: Order,
        quantity: float,
        price: float,
    ) -> Trade:

        now = self._now()

        trade_id = (
            "TRADE-"
            + uuid.uuid4().hex[:12].upper()
        )

        trade = Trade(
            trade_id=trade_id,
            asset_id=buy_order.asset_id,
            buyer_agent_id=buy_order.agent_id,
            seller_agent_id=sell_order.agent_id,
            quantity=quantity,
            price=price,
            tick=self.state.tick,
            world_date=self.state.world_date,
            created_at=now,
        )

        self.state.trades[
            trade_id
        ] = trade

        buy_order.remaining_quantity = max(
            0.0,
            buy_order.remaining_quantity
            - quantity,
        )

        sell_order.remaining_quantity = max(
            0.0,
            sell_order.remaining_quantity
            - quantity,
        )

        if buy_order.remaining_quantity <= 0:
            buy_order.status = "FILLED"

        if sell_order.remaining_quantity <= 0:
            sell_order.status = "FILLED"

        buy_order.updated_at = now
        sell_order.updated_at = now

        asset = self.get_asset(
            buy_order.asset_id
        )

        asset.previous_price = (
            asset.last_price
        )

        asset.last_price = price

        asset.total_volume += quantity

        asset.total_trades += 1

        asset.updated_at = now

        self._update_market_metrics(
            asset
        )

        return trade

    # ========================================================
    # MÉTRICAS
    # ========================================================

    def _update_market_metrics(
        self,
        asset: Asset,
    ) -> None:

        book = self.get_order_book(
            asset.asset_id
        )

        bids = book["bids"]
        asks = book["asks"]

        if bids:
            asset.best_bid = bids[0].price
        else:
            asset.best_bid = 0.0

        if asks:
            asset.best_ask = asks[0].price
        else:
            asset.best_ask = 0.0

        if (
            asset.best_bid > 0
            and asset.best_ask > 0
        ):

            asset.spread = (
                asset.best_ask
                - asset.best_bid
            )

        else:

            asset.spread = 0.0

        # ----------------------------------------------------
        # LIQUIDEZ
        # ----------------------------------------------------

        bid_volume = sum(
            order.remaining_quantity
            for order in bids
        )

        ask_volume = sum(
            order.remaining_quantity
            for order in asks
        )

        total_book = (
            bid_volume
            + ask_volume
        )

        if total_book > 0:

            asset.liquidity = min(
                1.0,
                total_book / 1000.0,
            )

        else:

            asset.liquidity = 0.0

        # ----------------------------------------------------
        # VOLATILIDADE
        # ----------------------------------------------------

        if asset.previous_price > 0:

            price_change = (
                asset.last_price
                - asset.previous_price
            ) / asset.previous_price

            asset.volatility = abs(
                price_change
            )

        else:

            asset.volatility = 0.0

    # ========================================================
    # CANCELAMENTO
    # ========================================================

    def cancel_order(
        self,
        order_id: str,
    ) -> Order:

        self._require_state()

        try:
            order = self.state.orders[
                order_id
            ]
        except KeyError:
            raise KeyError(
                f"Order not found: {order_id}"
            )

        if order.status == "OPEN":

            order.status = "CANCELLED"
            order.updated_at = self._now()

        self._touch()
        self._save()

        return order

    # ========================================================
    # TICK
    # ========================================================

    def process_tick(
        self,
        world_date: str,
    ) -> MarketState:

        self._require_state()

        self.state.tick += 1
        self.state.total_ticks += 1
        self.state.world_date = world_date

        for asset in (
            self.state.assets.values()
        ):

            self._update_market_metrics(
                asset
            )

        self._refresh_aggregates()
        self._touch()
        self._save()

        return self.state

    # ========================================================
    # AGREGADOS
    # ========================================================

    def _refresh_aggregates(
        self,
    ) -> None:

        if self.state is None:
            return

        self.state.total_markets = len(
            self.state.markets
        )

        self.state.total_assets = len(
            self.state.assets
        )

        self.state.total_orders = len(
            self.state.orders
        )

        self.state.total_trades = len(
            self.state.trades
        )

    # ========================================================
    # ESTADO
    # ========================================================

    def _require_state(
        self,
    ) -> None:

        if self.state is None:
            raise RuntimeError(
                "MarketEngine is not initialized."
            )

    def _touch(
        self,
    ) -> None:

        if self.state is not None:
            self.state.updated_at = (
                self._now()
            )

    # ========================================================
    # PERSISTÊNCIA
    # ========================================================

    def save(self) -> None:
        self._save()

    def _save(self) -> None:

        if self.state is None:
            return

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = asdict(
            self.state
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

    def load(
        self,
    ) -> MarketState:

        if not self.state_file.exists():

            raise FileNotFoundError(
                "Market state file not found: "
                f"{self.state_file}"
            )

        with self.state_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        markets = {}

        for market_id, market_data in (
            data.get(
                "markets",
                {},
            ).items()
        ):

            markets[market_id] = Market(
                **market_data
            )

        assets = {}

        for asset_id, asset_data in (
            data.get(
                "assets",
                {},
            ).items()
        ):

            assets[asset_id] = Asset(
                **asset_data
            )

        orders = {}

        for order_id, order_data in (
            data.get(
                "orders",
                {},
            ).items()
        ):

            orders[order_id] = Order(
                **order_data
            )

        trades = {}

        for trade_id, trade_data in (
            data.get(
                "trades",
                {},
            ).items()
        ):

            trades[trade_id] = Trade(
                **trade_data
            )

        data["markets"] = markets
        data["assets"] = assets
        data["orders"] = orders
        data["trades"] = trades

        self.state = MarketState(
            **data
        )

        return self.state

    def reset(self) -> None:

        self.state = None

        if self.state_file.exists():
            self.state_file.unlink()


# ============================================================
# TESTE MANUAL
# ============================================================


if __name__ == "__main__":

    print("=" * 60)
    print(ENGINE_NAME)
    print(ENGINE_VERSION)
    print("=" * 60)

    engine = MarketEngine(
        random_seed=42
    )

    engine.initialize(
        world_date="2026-09-29"
    )

    # --------------------------------------------------------
    # MERCADO
    # --------------------------------------------------------

    engine.create_market(
        market_id="MARKET-001",
        name="Bolsa Central",
        market_type="STOCK_EXCHANGE",
    )

    # --------------------------------------------------------
    # ATIVO
    # --------------------------------------------------------

    asset = engine.create_asset(
        asset_id="ASSET-001",
        symbol="ATLA",
        name="Atlas Industries",
        asset_type="STOCK",
        initial_price=100.0,
        market_id="MARKET-001",
    )

    print()
    print("MERCADO")
    print(
        "Nome          :",
        engine.get_market(
            "MARKET-001"
        ).name,
    )

    print()
    print("ATIVO")
    print(
        "Símbolo       :",
        asset.symbol,
    )
    print(
        "Preço inicial :",
        f"{asset.last_price:.2f}",
    )

    # --------------------------------------------------------
    # ORDENS
    # --------------------------------------------------------

    engine.place_order(
        asset_id="ASSET-001",
        agent_id="AGENT-BUYER",
        side="BUY",
        quantity=100,
        price=101.0,
    )

    engine.place_order(
        asset_id="ASSET-001",
        agent_id="AGENT-SELLER",
        side="SELL",
        quantity=100,
        price=99.0,
    )

    asset = engine.get_asset(
        "ASSET-001"
    )

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("MERCADO APÓS MATCH")

    print(
        "Preço         :",
        f"{asset.last_price:.2f}",
    )

    print(
        "Volume        :",
        f"{asset.total_volume:.2f}",
    )

    print(
        "Trades        :",
        asset.total_trades,
    )

    print(
        "Volatilidade  :",
        f"{asset.volatility:.2%}",
    )

    print(
        "Best Bid      :",
        f"{asset.best_bid:.2f}",
    )

    print(
        "Best Ask      :",
        f"{asset.best_ask:.2f}",
    )

    print(
        "Spread        :",
        f"{asset.spread:.2f}",
    )

    print()
    print("ORDENS")

    for order in engine.state.orders.values():

        print(
            order.order_id,
            "|",
            order.side,
            "|",
            order.status,
            "| restante:",
            f"{order.remaining_quantity:.2f}",
        )

    print()
    print(
        "TRADES:",
        engine.state.total_trades,
    )

    print()
    print(
        "MARKET ENGINE V01 "
        "TESTE CONCLUIDO"
    )

    print("=" * 60)