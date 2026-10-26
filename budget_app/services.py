import csv
from pathlib import Path

from budget_app.models import Transaction
from budget_app.repositories import TransactionRepository


class BudgetService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, transaction: Transaction):
        self.repository.save(transaction)

    def get_all_transactions(self):
        return list(self.repository.get_all())

    def get_total_summary(self):
        transactions = self.repository.get_all()

        income = 0
        expense = 0

        for t in transactions:
            if t.type == "income":
                income += t.amount
            elif t.type == "expense":
                expense += t.amount

        return {
            "income": income,
            "expense": expense,
            "balance": income - expense
        }

    def export_transactions_to_csv(self, filename=None):
        transactions = list(self.repository.get_all())

        if filename is None:
            file_path = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"
        else:
            file_path = Path(filename)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])

            for t in transactions:
                writer.writerow([
                    str(t.date),
                    t.type,
                    t.category,
                    t.amount,
                    t.memo if t.memo else "",
                    ",".join(t.tags) if t.tags else ""
                ])

        return file_path