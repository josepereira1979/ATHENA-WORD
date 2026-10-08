from world.market.market_engine import MarketEngine
from world.financial.financial_engine import FinancialEngine


def main():
    print("=" * 70)
    print("TESTE DE INTEGRACAO: MARKET <-> FINANCIAL")
    print("=" * 70)

    world_date = "2027-01-01"

    # ============================================================
    # ENGINES
    # ============================================================

    market = MarketEngine()
    financial = FinancialEngine()

    market.initialize(world_date)
    financial.initialize(world_date)

    # ============================================================
    # FINANCIAL
    # ============================================================

    financial.create_bank(
        bank_id="BANK-001",
        name="Banco Central do Mundo",
        reserves=100_000.0,
        interest_rate=0.05,
    )

    buyer_account = financial.create_account(
        account_id="ACC-BUYER",
        owner_id="AGENT-BUYER",
        bank_id="BANK-001",
        initial_balance=10_000.0,
    )

    seller_account = financial.create_account(
        account_id="ACC-SELLER",
        owner_id="AGENT-SELLER",
        bank_id="BANK-001",
        initial_balance=5_000.0,
    )

    print()
    print("FINANCIAL")
    print("-" * 70)
    print("Comprador inicial :", f"{buyer_account.balance:,.2f}")
    print("Vendedor inicial  :", f"{seller_account.balance:,.2f}")

    # ============================================================
    # MARKET
    # ============================================================

    market.create_market(
        market_id="MARKET-001",
        name="Central Exchange",
        market_type="EXCHANGE",
    )

    market.create_asset(
        asset_id="ASSET-001",
        symbol="ATLA",
        name="Atlas Industries",
        asset_type="STOCK",
        initial_price=100.0,
        market_id="MARKET-001",
    )

    # ============================================================
    # ORDENS
    # ============================================================

    market.place_order(
        asset_id="ASSET-001",
        agent_id="AGENT-BUYER",
        side="BUY",
        quantity=10,
        price=101.0,
    )

    market.place_order(
        asset_id="ASSET-001",
        agent_id="AGENT-SELLER",
        side="SELL",
        quantity=10,
        price=99.0,
    )

    # ============================================================
    # VERIFICAR TRADE
    # ============================================================

    trades = list(market.state.trades.values())

    if len(trades) != 1:
        raise AssertionError(
            f"Esperava 1 trade, encontrado: {len(trades)}"
        )

    trade = trades[0]

    trade_value = trade.quantity * trade.price

    print()
    print("MARKET")
    print("-" * 70)
    print("Trade ID         :", trade.trade_id)
    print("Ativo            :", trade.asset_id)
    print("Comprador        :", trade.buyer_agent_id)
    print("Vendedor         :", trade.seller_agent_id)
    print("Quantidade       :", f"{trade.quantity:,.2f}")
    print("Preço            :", f"{trade.price:,.2f}")
    print("Valor da operação:", f"{trade_value:,.2f}")

    # ============================================================
    # LIGACAO MARKET -> FINANCIAL
    # ============================================================

    buyer = None
    seller = None

    for account in financial.state.accounts.values():
        if account.owner_id == trade.buyer_agent_id:
            buyer = account

        if account.owner_id == trade.seller_agent_id:
            seller = account

    if buyer is None:
        raise AssertionError(
            "Conta financeira do comprador não encontrada."
        )

    if seller is None:
        raise AssertionError(
            "Conta financeira do vendedor não encontrada."
        )

    buyer_before = buyer.balance
    seller_before = seller.balance

    if buyer_before < trade_value:
        raise AssertionError(
            "Comprador sem saldo suficiente."
        )

    # Débito ao comprador
    financial.withdraw(
        account_id=buyer.account_id,
        amount=trade_value,
    )

    # Crédito ao vendedor
    financial.deposit(
        account_id=seller.account_id,
        amount=trade_value,
    )

    # ============================================================
    # VERIFICACAO FINANCEIRA
    # ============================================================

    buyer_after = financial.get_account(
        buyer.account_id
    )

    seller_after = financial.get_account(
        seller.account_id
    )

    expected_buyer = buyer_before - trade_value
    expected_seller = seller_before + trade_value

    if abs(buyer_after.balance - expected_buyer) > 0.000001:
        raise AssertionError(
            "Saldo do comprador incorreto."
        )

    if abs(seller_after.balance - expected_seller) > 0.000001:
        raise AssertionError(
            "Saldo do vendedor incorreto."
        )

    print()
    print("LIGACAO MARKET -> FINANCIAL")
    print("-" * 70)
    print(
        "Comprador:",
        f"{buyer_before:,.2f}",
        "->",
        f"{buyer_after.balance:,.2f}",
    )
    print(
        "Vendedor :",
        f"{seller_before:,.2f}",
        "->",
        f"{seller_after.balance:,.2f}",
    )

    # ============================================================
    # TICKS
    # ============================================================

    market.process_tick(world_date)
    financial.process_tick(world_date)

    print()
    print("TICKS")
    print("-" * 70)
    print("Market tick   :", market.state.tick)
    print("Financial tick:", financial.state.tick)

    # ============================================================
    # VERIFICACAO FINAL
    # ============================================================

    print()
    print("=" * 70)
    print("VERIFICACAO")
    print("=" * 70)

    print("MARKET          : OK")
    print("FINANCIAL       : OK")
    print("DINHEIRO        : OK")
    print("TRADE           : OK")
    print("LIGACAO         : OK")

    print()
    print("RESULTADO FINAL: MARKET <-> FINANCIAL OK")
    print("=" * 70)


if __name__ == "__main__":
    main()