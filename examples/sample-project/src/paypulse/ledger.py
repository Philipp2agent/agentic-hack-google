from dataclasses import dataclass
from typing import List

@dataclass
class JournalEntry:
    account_id: str
    amount_cents: int
    direction: str  # "DEBIT" or "CREDIT"

@dataclass
class Transaction:
    transaction_id: str
    description: str
    entries: List[JournalEntry]

    def is_balanced(self) -> bool:
        debits = sum(e.amount_cents for e in self.entries if e.direction == "DEBIT")
        credits = sum(e.amount_cents for e in self.entries if e.direction == "CREDIT")
        return debits == credits

class LedgerEngine:
    def __init__(self):
        self.transactions = []

    def record_transaction(self, tx: Transaction) -> bool:
        if not tx.is_balanced():
            raise ValueError(f"Transaction {tx.transaction_id} is not balanced.")
        self.transactions.append(tx)
        return True
