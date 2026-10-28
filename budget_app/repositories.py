import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, List

from budget_app.models import Transaction, Category, Budget


class TransactionRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, transaction: Transaction) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            json_str = json.dumps(asdict(transaction), ensure_ascii=False)
            f.write(json_str + "\n")

    def iter_transactions(self) -> Iterator[Transaction]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Transaction(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"거래 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def get_all(self) -> List[Transaction]:
        return list(self.iter_transactions())

    def update_transaction(self, updated_transaction):
        transactions = list(self.get_all())

        found = False

        for index, transaction in enumerate(transactions):
            if str(transaction.id) == str(updated_transaction.id):
                transactions[index] = updated_transaction
                found = True
                break

        if not found:
            raise ValueError("수정할 거래를 찾을 수 없습니다.")

        self.save_all(transactions)

    def save_all(self, transactions):
        with open(self.file_path, "w", encoding="utf-8") as file:
            for transaction in transactions:
                data = transaction.to_dict()
                file.write(json.dumps(data, ensure_ascii=False) + "\n")

class CategoryRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, category: Category) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            json_str = json.dumps(asdict(category), ensure_ascii=False)
            f.write(json_str + "\n")

    def iter_categories(self) -> Iterator[Category]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Category(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"카테고리 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def get_all(self) -> List[Category]:
        return list(self.iter_categories())

    def exists(self, name: str, type_: str) -> bool:
        normalized_name = name.strip().lower()
        normalized_type = type_.strip().lower()

        for category in self.iter_categories():
            if (
                category.name.strip().lower() == normalized_name
                and category.type.strip().lower() == normalized_type
            ):
                return True
        return False

    def delete(self, name: str, type_: str) -> bool:
        categories = self.get_all()

        normalized_name = name.strip().lower()
        normalized_type = type_.strip().lower()

        original_count = len(categories)
        remaining = [
            category
            for category in categories
            if not (
                category.name.strip().lower() == normalized_name
                and category.type.strip().lower() == normalized_type
            )
        ]

        if len(remaining) == original_count:
            return False

        with open(self.file_path, "w", encoding="utf-8") as f:
            for category in remaining:
                json_str = json.dumps(asdict(category), ensure_ascii=False)
                f.write(json_str + "\n")

        return True

class BudgetRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, budget: Budget) -> None:
        with open(self.file_path, "a", encoding="utf-8") as f:
            json_str = json.dumps(asdict(budget), ensure_ascii=False)
            f.write(json_str + "\n")

    def iter_budgets(self) -> Iterator[Budget]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Budget(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"예산 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def get_all(self) -> List[Budget]:
        return list(self.iter_budgets())