import csv
import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from budget_app.models import Transaction, Category, Budget
from budget_app.repositories import (
    TransactionRepository,
    CategoryRepository,
    BudgetRepository,
)


class BudgetService:
    """
    거래 내역 관리 서비스

    이름은 BudgetService지만,
    현재 역할은 거래(Transaction) 관리입니다.
    기존 CLI 코드와의 호환을 위해 이름은 유지합니다.
    """

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, transaction: Transaction) -> None:
        self.repository.save(transaction)

    def import_transactions_from_csv(
        self,
        filename: str,
        keep_id: bool = False,
    ) -> dict:
        file_path = Path(filename)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filename}")

        expected = ["id", "date", "type", "category", "amount", "memo", "tags"]
        success = 0
        failed = []  # (줄번호, 이유) 튜플 목록

        # export와 동일하게 utf-8-sig로 읽어야 BOM이 깨지지 않음
        with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            # 헤더 검증
            if reader.fieldnames != expected:
                raise ValueError(
                    f"CSV 헤더가 올바르지 않습니다.\n"
                    f"기대: {expected}\n실제: {reader.fieldnames}"
                )

            # enumerate(start=2): 1번째 줄은 헤더이므로 데이터는 2번부터
            for line_no, row in enumerate(reader, start=2):
                try:
                    # amount 변환 (문자열 → 정수)
                    amount = int(row["amount"])

                    # tags 파싱 (빈 문자열이면 빈 리스트)
                    tags = row["tags"].split(",") if row["tags"] else []

                    # Transaction 생성
                    tx_kwargs = {
                        "date": row["date"],
                        "type": row["type"],
                        "category": row["category"],
                        "amount": amount,
                        "memo": row["memo"],
                        "tags": tags,
                    }
                    # keep_id=True면 원본 id 유지, 아니면 새 id 자동 생성
                    if keep_id and row["id"]:
                        tx_kwargs["id"] = row["id"]

                    transaction = Transaction(**tx_kwargs)
                    self.add_transaction(transaction)
                    success += 1

                except (ValueError, KeyError) as e:
                    failed.append((line_no, str(e)))

        return {"success": success, "failed": failed}

    def get_all_transactions(self) -> list[Transaction]:
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

    def get_monthly_summary(self, month: str, top: int = 3) -> dict:
        # ... (기존 income, expense, category_expenses, top_categories 그대로) ...

        # 🆕 예산 경고: check_budget 재사용
        budget_results = self.check_budget(month)
        budget_alerts = [
            result
            for result in budget_results
            if result["usage_rate"] >= 80  # 80% 이상만 경고
        ]

        return {
            "month": month,
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "top_categories": top_categories,
            "budget_alerts": budget_alerts,  # 🆕
        }

    def get_transaction_by_id(self, transaction_id):
        for transaction in self.get_all_transactions():
            if str(transaction.id) == str(transaction_id):
                return transaction

        return None

    def filter_transactions(
        self,
        month: str | None = None,
        type_: str | None = None,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        """
        거래 목록을 월, 타입, 카테고리 기준으로 필터링합니다.
        """

        transactions = self.repository.get_all()

        if month:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.date.startswith(month)
            ]

        if type_:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.type == type_
            ]

        if category:
            normalized_category = category.strip().lower()
            transactions = [
                transaction
                for transaction in transactions
                if transaction.category.strip().lower() == normalized_category
            ]

        transactions = sorted(
            transactions,
            key=lambda transaction: transaction.date,
            reverse=True,
        )

        if limit is not None:
            transactions = transactions[:limit]

        return transactions

    def search_transactions(
        self,
        keyword: str,
        month: str | None = None,
        type_: str | None = None,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        """
        키워드로 거래 내역을 검색합니다.
        검색 대상: 카테고리, 메모, 태그
        """

        normalized_keyword = keyword.strip().lower()

        if not normalized_keyword:
            raise ValueError("검색어는 비워둘 수 없습니다.")

        transactions = self.filter_transactions(
            month=month,
            type_=type_,
            category=category,
            limit=None,
        )

        searched_transactions = []

        for transaction in transactions:
            category_text = transaction.category.lower()
            memo_text = (transaction.memo or "").lower()
            tags_text = " ".join(transaction.tags).lower() if transaction.tags else ""

            if (
                normalized_keyword in category_text
                or normalized_keyword in memo_text
                or normalized_keyword in tags_text
            ):
                searched_transactions.append(transaction)

        if limit is not None:
            searched_transactions = searched_transactions[:limit]

        return searched_transactions

    def export_transactions_to_csv(
        self,
        filename: str | None = None,
        month: str | None = None,
        category: str | None = None,
        tx_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Path:
        transactions = self.repository.get_all()

        filtered = []
        for t in transactions:
            if month and not t.date.startswith(month):
                continue
            if category and t.category != category:
                continue
            if tx_type and t.type != tx_type:
                continue
            if date_from and t.date < date_from:
                continue
            if date_to and t.date > date_to:
                continue
            filtered.append(t)

        if filename is None:
            repo_path = Path(self.repository.file_path)
            file_path = repo_path.parent / "transactions.csv"
        else:
            file_path = Path(filename)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "date", "type", "category", "amount", "memo", "tags"])
            for t in filtered:
                writer.writerow([
                    t.id, t.date, t.type, t.category, t.amount,
                    t.memo or "",
                    ",".join(t.tags) if t.tags else "",
                ])

        return file_path

    def update_transaction(
        self,
        transaction_id,
        date=None,
        type_=None,
        category=None,
        amount=None,
        memo=None,
        tags=None,
    ):
        transactions = self.get_all_transactions()

        target = None

        for transaction in transactions:
            if str(transaction.id) == str(transaction_id):
                target = transaction
                break

        if target is None:
            raise ValueError("수정할 거래를 찾을 수 없습니다.")

        updated_transaction = Transaction(
            id=target.id,
            date=date if date is not None else target.date,
            type=type_ if type_ is not None else target.type,
            category=category if category is not None else target.category,
            amount=amount if amount is not None else target.amount,
            memo=memo if memo is not None else target.memo,
            tags=tags if tags is not None else target.tags,
        )

        self.repository.update_transaction(updated_transaction)

        return updated_transaction


class BudgetService:
    """
    카테고리 관리 서비스
    """

    def __init__(self, repository: CategoryRepository):
        self.repository = repository

    def add_category(self, category: Category) -> None:
        if self.repository.exists(category.name, category.type):
            raise ValueError("이미 존재하는 카테고리입니다.")

        self.repository.save(category)

    def get_all_categories(self) -> list[Category]:
        return self.repository.get_all()

    def remove_category(self, name: str, type_: str) -> None:
        deleted = self.repository.delete(name, type_)

        if not deleted:
            raise ValueError("삭제할 카테고리가 없습니다.")


class BudgetLimitService:
    """
    월별 카테고리 예산 관리 서비스
    """

    def __init__(
        self,
        budget_repository: BudgetRepository,
        transaction_repository: TransactionRepository,
    ):
        self.budget_repository = budget_repository
        self.transaction_repository = transaction_repository

    def set_budget(self, budget: Budget) -> None:
        """
        예산을 설정합니다.

        같은 month + category 조합이 이미 있으면 덮어씁니다.
        없으면 새로 추가합니다.
        """

        self._validate_month(budget.month)

        if budget.amount <= 0:
            raise ValueError("예산 금액은 1원 이상이어야 합니다.")

        category_name = budget.category.strip()

        if not category_name:
            raise ValueError("카테고리는 비워둘 수 없습니다.")

        budgets = self.budget_repository.get_all()

        normalized_month = budget.month.strip()
        normalized_category = category_name.lower()

        updated = False
        new_budgets: list[Budget] = []

        for existing_budget in budgets:
            same_month = existing_budget.month.strip() == normalized_month
            same_category = (
                existing_budget.category.strip().lower() == normalized_category
            )

            if same_month and same_category:
                new_budgets.append(
                    Budget(
                        month=normalized_month,
                        category=category_name,
                        amount=budget.amount,
                    )
                )
                updated = True
            else:
                new_budgets.append(existing_budget)

        if not updated:
            new_budgets.append(
                Budget(
                    month=normalized_month,
                    category=category_name,
                    amount=budget.amount,
                )
            )

        self._write_all_budgets(new_budgets)

    def get_budgets(self, month: str | None = None) -> list[Budget]:
        """
        예산 목록을 조회합니다.
        month가 있으면 해당 월 예산만 조회합니다.
        """

        budgets = self.budget_repository.get_all()

        if month:
            self._validate_month(month)
            budgets = [
                budget
                for budget in budgets
                if budget.month == month
            ]

        return budgets

    def check_budget(self, month: str) -> list[dict]:
        """
        특정 월의 예산 대비 실제 지출을 계산합니다.
        """

        self._validate_month(month)

        budgets = self.get_budgets(month)
        transactions = self.transaction_repository.get_all()

        results = []

        for budget in budgets:
            spent = 0

            for transaction in transactions:
                is_same_month = transaction.date.startswith(month)
                is_expense = transaction.type == "expense"
                is_same_category = (
                    transaction.category.strip().lower()
                    == budget.category.strip().lower()
                )

                if is_same_month and is_expense and is_same_category:
                    spent += transaction.amount

            remaining = budget.amount - spent

            if budget.amount > 0:
                usage_rate = spent / budget.amount * 100
            else:
                usage_rate = 0

            results.append({
                "month": budget.month,
                "category": budget.category,
                "budget": budget.amount,
                "spent": spent,
                "remaining": remaining,
                "usage_rate": usage_rate,
                "is_over": spent > budget.amount,
            })

        return results

    def _write_all_budgets(self, budgets: list[Budget]) -> None:
        """
        전체 예산 목록을 JSONL 파일에 다시 저장합니다.
        """

        file_path = Path(self.budget_repository.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            for budget in budgets:
                json_str = json.dumps(asdict(budget), ensure_ascii=False)
                file.write(json_str + "\n")

    def list_budgets(self, month: str | None = None) -> list[Budget]:
        budgets = self.get_budgets(month)

        return sorted(
            budgets,
            key=lambda budget: (budget.month, budget.category),
        )     

    @staticmethod
    def _validate_month(month: str) -> None:
        """
        YYYY-MM 형식의 월 문자열을 검증합니다.
        """

        if not re.fullmatch(r"\d{4}-\d{2}", month):
            raise ValueError("월은 YYYY-MM 형식이어야 합니다.")

        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError("존재하지 않는 월입니다.")