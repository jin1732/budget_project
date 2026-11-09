from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from budget_app.models import Budget, Category, Transaction
from budget_app.repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)

from .repositories import TransactionRepository, CategoryRepository


class BudgetService:
    """
    거래 관리 서비스
    """

    def __init__(
        self,
        repository: TransactionRepository,
        category_repo: CategoryRepository,
        budget_limit_service: BudgetLimitService | None = None,
    ):
        self.repository = repository
        self.category_repo = category_repo
        self.budget_limit_service = budget_limit_service

    def add_transaction(self, transaction: Transaction) -> None:
        """
        거래를 추가합니다.
        거래의 타입(income/expense)에 맞는 카테고리가 등록되어 있어야 합니다.
        """

        self._validate_category(transaction.category, transaction.type)
        self.repository.save(transaction)

    def get_all_transactions(self) -> list[Transaction]:
        return self.repository.get_all()

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
            self._validate_month(month)
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
        keyword: str | None = None,
        category: str | None = None,
        type_: str | None = None,
        month: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        """
        거래 내역을 검색합니다.
        필터링 조건: 날짜 범위, 카테고리, 타입, 키워드(메모/카테고리/태그)
        """

        if month:
            self._validate_month(month)
            date_from = f"{month}-01"
            date_to = f"{month}-31"

        normalized_keyword = keyword.strip().lower() if keyword else None
        normalized_category = category.strip().lower() if category else None

        results: list[Transaction] = []

        for tx in self.repository.get_all():
            if date_from and tx.date < date_from:
                continue
            if date_to and tx.date > date_to:
                continue

            if normalized_category:
                if tx.category.strip().lower() != normalized_category:
                    continue

            if type_ and tx.type != type_:
                continue

            if normalized_keyword:
                category_text = tx.category.lower()
                memo_text = (tx.memo or "").lower()
                tags_text = " ".join(tx.tags).lower() if tx.tags else ""

                if (
                    normalized_keyword not in category_text
                    and normalized_keyword not in memo_text
                    and normalized_keyword not in tags_text
                ):
                    continue

            results.append(tx)

        results = sorted(results, key=lambda tx: tx.date, reverse=True)

        if limit is not None:
            results = results[:limit]

        return results

    def get_monthly_summary(self, month: str, top: int = 3) -> dict:
        """
        월별 수입/지출 요약을 반환합니다.
        """

        self._validate_month(month)

        transactions = self.filter_transactions(month=month)

        if not transactions:
            return {}

        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")

        category_expenses: dict[str, int] = {}
        for transaction in transactions:
            if transaction.type != "expense":
                continue

            category_name = transaction.category.strip()
            category_expenses[category_name] = (
                category_expenses.get(category_name, 0) + transaction.amount
            )

        top_categories = sorted(
            category_expenses.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:top]

        budget_alerts = []

        if self.budget_limit_service is not None:
            budget_result = self.budget_limit_service.check_budget(month)
            if budget_result:
                budget_alerts.append(budget_result)

        return {
            "month": month,
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "category_expenses": category_expenses,
            "top_categories": top_categories,
            "budget_alerts": budget_alerts,
        }

    def update_transaction(
        self,
        transaction_id,
        date=None,
        type_=None,
        category=None,
        amount=None,
        memo=None,
        tags=None,
    ) -> Transaction:
        transactions = self.get_all_transactions()

        target = None

        for transaction in transactions:
            if str(transaction.id) == str(transaction_id):
                target = transaction
                break

        if target is None:
            raise ValueError("수정할 거래를 찾을 수 없습니다.")

        final_type = type_ if type_ is not None else target.type
        final_category = category if category is not None else target.category

        self._validate_category(final_category, final_type)

        updated_transaction = Transaction(
            id=target.id,
            date=date if date is not None else target.date,
            type=final_type,
            category=final_category,
            amount=amount if amount is not None else target.amount,
            memo=memo if memo is not None else target.memo,
            tags=tags if tags is not None else target.tags,
        )

        self.repository.update_transaction(updated_transaction)
        return updated_transaction

    def delete_transaction(self, transaction_id) -> None:
        """
        저장소 메서드명이 delete_transaction 또는 delete 중 무엇이든 대응할 수 있게 작성.
        """

        deleted = None

        if hasattr(self.repository, "delete_transaction"):
            deleted = self.repository.delete_transaction(transaction_id)
        elif hasattr(self.repository, "delete"):
            deleted = self.repository.delete(transaction_id)
        else:
            raise AttributeError(
                "TransactionRepository에 delete_transaction() 또는 delete()가 필요합니다."
            )

        if not deleted:
            raise ValueError("삭제할 거래를 찾을 수 없습니다.")

    def export_transactions_to_csv(
        self,
        filename: str | None = None,
        month: str | None = None,
        category: str | None = None,
        tx_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> Path:
        if month:
            self._validate_month(month)

        transactions = self.repository.get_all()
        normalized_category = category.strip().lower() if category else None

        filtered: list[Transaction] = []

        for transaction in transactions:
            if month and not transaction.date.startswith(month):
                continue
            if (
                normalized_category
                and transaction.category.strip().lower() != normalized_category
            ):
                continue
            if tx_type and transaction.type != tx_type:
                continue
            if date_from and transaction.date < date_from:
                continue
            if date_to and transaction.date > date_to:
                continue

            filtered.append(transaction)

        if filename is None:
            repo_path = Path(self.repository.file_path)
            file_path = repo_path.parent / "transactions.csv"
        else:
            file_path = Path(filename)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["id", "date", "type", "category", "amount", "memo", "tags"])

            for transaction in filtered:
                writer.writerow(
                    [
                        transaction.id,
                        transaction.date,
                        transaction.type,
                        transaction.category,
                        transaction.amount,
                        transaction.memo or "",
                        ",".join(transaction.tags) if transaction.tags else "",
                    ]
                )

        return file_path

    def _validate_category(self, category_name: str, type_: str) -> None:
        """
        등록된 카테고리인지 검증합니다.
        거래 타입(income/expense)도 함께 맞아야 합니다.
        """

        normalized_name = category_name.strip().lower()
        normalized_type = type_.strip().lower()

        categories = self.category_repo.get_all()

        for category in categories:
            same_name = category.name.strip().lower() == normalized_name
            same_type = category.type.strip().lower() == normalized_type

            if same_name and same_type:
                return

        raise ValueError(
            f"오류: '{category_name}'는 등록되지 않은 {type_} 카테고리입니다."
        )

    @staticmethod
    def _validate_month(month: str) -> None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError("월 형식은 YYYY-MM 이어야 합니다.") from None


class CategoryService:
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
    월별 총예산 관리 서비스
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
        월 예산을 설정합니다.
        같은 month가 이미 있으면 덮어씁니다.
        없으면 새로 추가합니다.
        """

        self._validate_month(budget.month)

        if budget.amount <= 0:
            raise ValueError("예산 금액은 1원 이상이어야 합니다.")

        budgets = self.budget_repository.get_all()
        normalized_month = budget.month.strip()

        updated = False
        new_budgets: list[Budget] = []

        for existing_budget in budgets:
            same_month = existing_budget.month.strip() == normalized_month

            if same_month:
                new_budgets.append(
                    Budget(
                        month=normalized_month,
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
            budgets = [budget for budget in budgets if budget.month == month]

        return budgets

    def list_budgets(self, month: str | None = None) -> list[Budget]:
        """
        get_budgets와 같은 역할을 하는 별칭 메서드
        handle_budget에서 list_budgets를 호출해도 동작하도록 추가
        """
        return self.get_budgets(month)

    def check_budget(self, month: str) -> dict | None:
        """
        특정 월의 총예산 대비 실제 총지출을 계산합니다.
        """

        self._validate_month(month)

        budgets = self.get_budgets(month)

        if not budgets:
            return None

        budget = budgets[0]
        transactions = self.transaction_repository.get_all()

        spent = 0

        for transaction in transactions:
            is_same_month = transaction.date.startswith(month)
            is_expense = transaction.type == "expense"

            if is_same_month and is_expense:
                spent += transaction.amount

        remaining = budget.amount - spent
        usage_rate = (spent / budget.amount * 100) if budget.amount > 0 else 0

        return {
            "month": budget.month,
            "budget": budget.amount,
            "spent": spent,
            "remaining": remaining,
            "usage_rate": usage_rate,
            "is_over": spent > budget.amount,
        }

    def _write_all_budgets(self, budgets: list[Budget]) -> None:
        """
        BudgetRepository가 파일 기반이라고 가정한 구현입니다.
        budget_repository에 file_path 속성이 있어야 동작합니다.
        """

        file_path = Path(self.budget_repository.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as file:
            for budget in budgets:
                file.write(json.dumps(asdict(budget), ensure_ascii=False) + "\n")

    @staticmethod
    def _validate_month(month: str) -> None:
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError("월 형식은 YYYY-MM 이어야 합니다.") from None