from budget_app.models import Transaction
from budget_app.repositories import TransactionRepository


class BudgetService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, transaction: Transaction):
        self.repository.save(transaction)

    def get_all_transaction(self):
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