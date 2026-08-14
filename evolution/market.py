"""A deterministic strategy market with token wallets and sealed bids."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from evolution.lamarckian import Strategy


@dataclass(frozen=True)
class Transaction:
    amount: float
    reason: str
    counterparty: str = ""


@dataclass
class TokenWallet:
    balance: float = 100.0
    income_history: list[Transaction] = field(default_factory=list)
    expense_history: list[Transaction] = field(default_factory=list)
    _lock: threading.Lock = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()

    def earn(self, amount: float, reason: str, counterparty: str = "") -> None:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        with self._lock:
            self.balance += amount
            self.income_history.append(Transaction(amount, reason, counterparty))

    def spend(self, amount: float, reason: str, counterparty: str = "") -> bool:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        with self._lock:
            if amount > self.balance + 1e-9:
                return False
            self.balance -= amount
            self.expense_history.append(Transaction(amount, reason, counterparty))
            return True

    def net_worth(self) -> float:
        with self._lock:
            return round(self.balance, 6)


@dataclass
class MarketListing:
    strategy: Strategy
    seller_id: str
    adoption_count: int = 0
    bids: dict[str, float] = field(default_factory=dict)


class StrategyMarket:
    """A simple exchange where scarcity and adoption determine price."""

    def __init__(self, base_price: float = 100.0) -> None:
        self.base_price = float(base_price)
        self.listings: dict[str, MarketListing] = {}
        self.wallets: dict[str, TokenWallet] = {}
        self.trade_history: list[dict[str, Any]] = []

    def wallet_for(self, organism: Any) -> TokenWallet:
        wallet = getattr(organism, "token_wallet", None)
        if wallet is None:
            wallet = self.wallets.setdefault(str(getattr(organism, "object_id", organism)), TokenWallet())
            setattr(organism, "token_wallet", wallet)
        return wallet

    def register(self, strategy: Strategy, seller_id: str | None = None) -> MarketListing:
        listing = MarketListing(strategy, seller_id or strategy.author_id)
        self.listings[strategy.name] = listing
        self.wallets.setdefault(listing.seller_id, TokenWallet())
        return listing

    def price(self, strategy_name: str) -> float:
        listing = self.listings.get(strategy_name)
        if listing is None:
            raise KeyError(f"strategy not listed: {strategy_name}")
        rarity = 1.0 + max(0.0, 1.0 - listing.strategy.effectiveness)
        return round(max(0.01, self.base_price * rarity / (1.0 + listing.adoption_count)), 6)

    def buy(self, buyer: Any, strategy_name: str) -> bool:
        listing = self.listings.get(strategy_name)
        if listing is None:
            return False
        buyer_id = str(getattr(buyer, "object_id", buyer))
        price = self.price(strategy_name)
        buyer_wallet = self.wallet_for(buyer)
        if not buyer_wallet.spend(price, f"adopt:{strategy_name}", listing.seller_id):
            return False
        install = getattr(buyer, "install_strategy", None)
        if not callable(install) or not install(listing.strategy):
            buyer_wallet.earn(price, "refund:failed-adoption", listing.seller_id)
            return False
        seller_wallet = self.wallets.setdefault(listing.seller_id, TokenWallet())
        seller_wallet.earn(price, f"sale:{strategy_name}", buyer_id)
        listing.adoption_count += 1
        self.trade_history.append({"type": "buy", "buyer": buyer_id, "seller": listing.seller_id, "strategy": strategy_name, "price": price})
        return True

    def bid(self, bidder: Any, strategy_name: str, amount: float) -> bool:
        listing = self.listings.get(strategy_name)
        if listing is None or amount <= 0:
            return False
        bidder_id = str(getattr(bidder, "object_id", bidder))
        wallet = self.wallet_for(bidder)
        if not wallet.spend(amount, f"escrow:{strategy_name}"):
            return False
        previous = listing.bids.get(bidder_id)
        if previous is not None:
            wallet.earn(previous, "refund:replaced-bid")
        listing.bids[bidder_id] = amount
        return True

    def auction(self, strategy_name: str, duration_generations: int = 3) -> str:
        listing = self.listings.get(strategy_name)
        if listing is None or duration_generations < 1 or not listing.bids:
            return ""
        winner_id, winning_bid = max(listing.bids.items(), key=lambda pair: pair[1])
        for bidder_id, amount in listing.bids.items():
            if bidder_id != winner_id:
                self.wallets.setdefault(bidder_id, TokenWallet()).earn(amount, "refund:auction")
        self.wallets.setdefault(listing.seller_id, TokenWallet()).earn(winning_bid, f"auction:{strategy_name}", winner_id)
        listing.adoption_count += 1
        listing.bids.clear()
        self.trade_history.append({"type": "auction", "winner": winner_id, "strategy": strategy_name, "price": winning_bid, "duration": duration_generations})
        return winner_id


__all__ = ["MarketListing", "StrategyMarket", "TokenWallet", "Transaction"]
