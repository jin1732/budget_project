import csv
from pathlib import Path

from budget_app.models import Transaction, Category
from budget_app.repositories import TransactionRepository, CategoryRepository


class BudgetService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, transaction: Transaction) -> None:
        self.repository.save(transaction)

    def get_all_transactions(self):
        return self.repository.get_all()

    def get_total_summary(self) -> dict[str, int]:
        transactions = self.repository.get_all()

        income = 0
        expense = 0

        for transaction in transactions:
            if transaction.type == "income":
                income += transaction.amount
            elif transaction.type == "expense":
                expense += transaction.amount

        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
        }

    def export_transactions_to_csv(self, filename: str | None = None) -> Path:
        transactions = self.repository.get_all()

        if filename is None:
            repo_path = Path(self.repository.file_path)
            file_path = repo_path.parent / "transactions.csv"
        else:
            file_path = Path(filename)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])

            for transaction in transactions:
                writer.writerow([
                    transaction.date,
                    transaction.type,
                    transaction.category,
                    transaction.amount,
                    transaction.memo or "",
                    ",".join(transaction.tags) if transaction.tags else "",
                ])

        return file_path


class CategoryService:
    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    def add_category(self, category: Category) -> None:
        if self.repository.exists(category.name, category.type):
            raise ValueError("이미 존재하는 카테고리입니다.")
        self.repository.save(category)

    def get_all_categories(self):
        return self.repository.get_all()

    def remove_category(self, name: str, type_: str) -> None:
        deleted = self.repository.delete(name, type_)
        if not deleted:
            raise ValueError("삭제할 카테고리가 없습니다.")