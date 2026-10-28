import argparse
import csv
from pathlib import Path

from budget_app.decorators import handle_cli_errors
from budget_app.models import Transaction, Category, Budget
from budget_app.repositories import (
    TransactionRepository,
    CategoryRepository,
    BudgetRepository,
)
from budget_app.services import (
    BudgetService,
    CategoryService,
    BudgetLimitService,
)
from budget_app.validators import (
    validate_date,
    validate_transaction_type,
    validate_amount,
)


class BudgetCLI:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)

        self.service = None
        self.category_service = None
        self.budget_service = None

    def setup_services(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        transaction_file = self.data_dir / "transactions.jsonl"
        category_file = self.data_dir / "categories.jsonl"
        budget_file = self.data_dir / "budgets.jsonl"

        transaction_repository = TransactionRepository(str(transaction_file))
        category_repository = CategoryRepository(str(category_file))
        budget_repository = BudgetRepository(str(budget_file))

        self.service = BudgetService(transaction_repository)
        self.category_service = CategoryService(category_repository)
        self.budget_service = BudgetLimitService(
            budget_repository,
            transaction_repository,
        )

    def create_parser(self):
        parser = argparse.ArgumentParser(
            prog="budget-app",
            description="콘솔 가계부 앱",
        )

        parser.add_argument(
            "--data-dir",
            default="data",
            help="데이터 저장 폴더 경로",
        )

        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
        )

        # add
        add_parser = subparsers.add_parser("add", help="거래 추가")
        add_parser.add_argument("--date", required=True, help="날짜 YYYY-MM-DD")
        add_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="거래 유형 income 또는 expense",
        )
        add_parser.add_argument("--category", required=True, help="카테고리")
        add_parser.add_argument("--amount", required=True, help="금액")
        add_parser.add_argument("--memo", default="", help="메모")
        add_parser.add_argument(
            "--tags",
            default="",
            help="태그 목록, 예: 식비,점심,카드",
        )

        # list
        list_parser = subparsers.add_parser("list", help="거래 목록 조회")
        list_parser.add_argument("--month", help="조회 월 YYYY-MM")
        list_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="거래 유형 필터",
        )
        list_parser.add_argument("--category", help="카테고리 필터")
        list_parser.add_argument(
            "--limit",
            type=int,
            help="출력 개수 제한",
        )

        # summary
        summary_parser = subparsers.add_parser("summary", help="월별 요약")
        summary_parser.add_argument("--month", required=True, help="요약 월 YYYY-MM")
        summary_parser.add_argument(
            "--top",
            type=int,
            default=3,
            help="지출 카테고리 TOP N",
        )

        # export
        export_parser = subparsers.add_parser("export", help="CSV 내보내기")
        export_parser.add_argument(
            "--out",
            default=None,
            help="CSV 저장 경로",
        )

        # category
        category_parser = subparsers.add_parser("category", help="카테고리 관리")
        category_subparsers = category_parser.add_subparsers(
            dest="category_command",
            required=True,
        )

        category_add_parser = category_subparsers.add_parser(
            "add",
            help="카테고리 추가",
        )
        category_add_parser.add_argument("name", help="카테고리 이름")
        category_add_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="카테고리 유형",
        )

        category_subparsers.add_parser(
            "list",
            help="카테고리 목록 조회",
        )

        category_remove_parser = category_subparsers.add_parser(
            "remove",
            help="카테고리 삭제",
        )
        category_remove_parser.add_argument("name", help="카테고리 이름")
        category_remove_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="카테고리 유형",
        )

        # budget
        budget_parser = subparsers.add_parser("budget", help="예산 관리")
        budget_subparsers = budget_parser.add_subparsers(
            dest="budget_command",
            required=True,
        )

        budget_set_parser = budget_subparsers.add_parser(
            "set",
            help="월별 카테고리 예산 설정",
        )
        budget_set_parser.add_argument("--month", required=True, help="월 YYYY-MM")
        budget_set_parser.add_argument("--category", required=True, help="카테고리")
        budget_set_parser.add_argument("--amount", required=True, help="예산 금액")

        budget_list_parser = budget_subparsers.add_parser(
            "list",
            help="예산 목록 조회",
        )
        budget_list_parser.add_argument("--month", help="월 YYYY-MM")

        budget_check_parser = budget_subparsers.add_parser(
            "check",
            help="예산 대비 지출 확인",
        )
        budget_check_parser.add_argument("--month", required=True, help="월 YYYY-MM")

        # search
        search_parser = subparsers.add_parser(
            "search",
            help="거래 내역 검색",
        )
        search_parser.add_argument(
            "keyword",
            help="검색어",
        )
        search_parser.add_argument(
            "--month",
            help="조회할 월, 예: 2025-01",
        )
        search_parser.add_argument(
            "--type",
            choices=["income", "expense"],
            help="거래 타입",
        )
        search_parser.add_argument(
            "--category",
            help="카테고리",
        )
        search_parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="검색 결과 개수 제한",
        )

        # update
        update_parser = subparsers.add_parser("update", help="거래 수정")
        update_parser.add_argument("id", help="수정할 거래 ID")

        update_parser.add_argument("--date", help="날짜 YYYY-MM-DD")
        update_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="거래 유형",
        )
        update_parser.add_argument("--category", help="카테고리")
        update_parser.add_argument("--amount", help="금액")
        update_parser.add_argument("--memo", help="메모")
        update_parser.add_argument(
            "--tags",
            help="태그 목록, 예: 식비,점심,카드",
        )
        return parser

    @handle_cli_errors
    def run(self, argv=None):
        parser = self.create_parser()
        args = parser.parse_args(argv)

        self.setup_services(args.data_dir)

        if args.command == "add":
            return self.handle_add(args)

        if args.command == "update":
            return self.handle_update(args)

        if args.command == "list":
            return self.handle_list(args)

        if args.command == "summary":
            return self.handle_summary(args)

        if args.command == "export":
            return self.handle_export(args.out)

        if args.command == "category":
            return self.handle_category(args)

        if args.command == "budget":
            return self.handle_budget(args)

        if args.command == "search":
            return self.handle_search(args)

        parser.print_help()
        return 1

    def handle_add(self, args):
        date = validate_date(args.date)
        type_ = validate_transaction_type(args.tx_type)
        category = args.category.strip()
        amount = validate_amount(args.amount)
        memo = args.memo.strip()

        if not category:
            raise ValueError("카테고리는 비워둘 수 없습니다.")

        tags = [
            tag.strip()
            for tag in args.tags.split(",")
            if tag.strip()
        ] if args.tags else []

        transaction = Transaction(
            date=date,
            type=type_,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )

        self.service.add_transaction(transaction)
        print("거래가 저장되었습니다.")
        return 0

    def handle_list(self, args):
        transactions = self.service.get_all_transactions()

        if args.month:
            month = self.validate_month(args.month)
            transactions = [
                t for t in transactions
                if t.date.startswith(month)
            ]

        if args.tx_type:
            transactions = [
                t for t in transactions
                if t.type == args.tx_type
            ]

        if args.category:
            keyword = args.category.strip().lower()
            transactions = [
                t for t in transactions
                if t.category.strip().lower() == keyword
            ]

        transactions = sorted(
            transactions,
            key=lambda t: t.date,
            reverse=True,
        )

        if args.limit is not None:
            limit = self.validate_limit(args.limit)
            transactions = transactions[:limit]

        if not transactions:
            print("거래 내역이 없습니다.")
            return 0

        for t in transactions:
            print(
                f"[{t.id}] {t.date} | {t.type} | {t.category} | "
                f"{t.amount:,}원 | 메모: {t.memo or '-'} | "
                f"태그: {', '.join(t.tags) if t.tags else '-'}"
            )

        return 0

    def handle_summary(self, args):
        month = self.validate_month(args.month)

        if args.top <= 0:
            raise ValueError("top은 1 이상의 숫자여야 합니다.")

        transactions = self.service.get_all_transactions()

        month_transactions = [
            t for t in transactions
            if t.date.startswith(month)
        ]

        income = sum(
            t.amount
            for t in month_transactions
            if t.type == "income"
        )

        expense = sum(
            t.amount
            for t in month_transactions
            if t.type == "expense"
        )

        balance = income - expense

        expense_by_category = {}

        for t in month_transactions:
            if t.type != "expense":
                continue

            expense_by_category[t.category] = (
                expense_by_category.get(t.category, 0) + t.amount
            )

        top_expenses = sorted(
            expense_by_category.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:args.top]

        print(f"{month} 요약")
        print("-" * 40)
        print(f"총 수입: {income:,}원")
        print(f"총 지출: {expense:,}원")
        print(f"잔액: {balance:,}원")

        print()
        print(f"지출 TOP {args.top}")

        if not top_expenses:
            print("지출 내역이 없습니다.")
        else:
            for index, (category, amount) in enumerate(top_expenses, start=1):
                print(f"{index}. {category}: {amount:,}원")

        return 0

    def handle_export(self, out_path=None):
        transactions = self.service.get_all_transactions()

        if out_path is None:
            out_path = self.data_dir / "transactions.csv"
        else:
            out_path = Path(out_path)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            writer.writerow([
                "id",
                "date",
                "type",
                "category",
                "amount",
                "memo",
                "tags",
            ])

            for t in transactions:
                writer.writerow([
                    t.id,
                    t.date,
                    t.type,
                    t.category,
                    t.amount,
                    t.memo,
                    ",".join(t.tags) if t.tags else "",
                ])

        print(f"CSV 파일로 내보냈습니다: {out_path}")
        return 0

    def handle_category(self, args):
        if args.category_command == "add":
            name = args.name.strip()
            type_ = validate_transaction_type(args.tx_type)

            if not name:
                raise ValueError("카테고리 이름은 비워둘 수 없습니다.")

            category = Category(
                name=name,
                type=type_,
            )

            self.category_service.add_category(category)

            print("카테고리가 추가되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {type_}")
            return 0

        if args.category_command == "list":
            categories = self.category_service.get_all_categories()

            if not categories:
                print("등록된 카테고리가 없습니다.")
                return 0

            print("카테고리 목록")
            print("-" * 40)

            for category in categories:
                print(f"{category.type} | {category.name}")

            return 0

        if args.category_command == "remove":
            name = args.name.strip()
            type_ = validate_transaction_type(args.tx_type)

            if not name:
                raise ValueError("카테고리 이름은 비워둘 수 없습니다.")

            self.category_service.remove_category(name, type_)

            print("카테고리가 삭제되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {type_}")
            return 0

        raise ValueError("알 수 없는 category 명령어입니다.")

    def handle_budget(self, args):
        if args.budget_command == "set":
            month = self.validate_month(args.month)
            category = args.category.strip()
            amount = validate_amount(args.amount)

            if not category:
                raise ValueError("카테고리는 비워둘 수 없습니다.")

            budget = Budget(
                month=month,
                category=category,
                amount=amount,
            )

            self.budget_service.set_budget(budget)

            print("예산이 설정되었습니다.")
            print(f"월: {month}")
            print(f"카테고리: {category}")
            print(f"금액: {amount:,}원")
            return 0

        if args.budget_command == "list":
            month = self.validate_month(args.month) if args.month else None

            budgets = self.budget_service.list_budgets(month)

            if not budgets:
                print("등록된 예산이 없습니다.")
                return 0

            print("예산 목록")
            print("-" * 40)

            for budget in budgets:
                print(
                    f"{budget.month} | "
                    f"{budget.category} | "
                    f"{budget.amount:,}원"
                )

            return 0

        if args.budget_command == "check":
            month = self.validate_month(args.month)

            results = self.budget_service.check_budget(month)

            if not results:
                print("확인할 예산이 없습니다.")
                return 0

            print(f"{month} 예산 사용 현황")
            print("-" * 50)

            for result in results:
                category = result["category"]
                budget_amount = result["budget"]
                used_amount = result["spent"]
                usage_rate = result["usage_rate"]
                is_over = result["is_over"]

                status = "초과" if is_over else "정상"

                print(
                    f"{category} | "
                    f"{used_amount:,}원 / {budget_amount:,}원 | "
                    f"{usage_rate:.1f}% | "
                    f"{status}"
                )

            return 0

        raise ValueError("알 수 없는 budget 명령어입니다.")

    def handle_search(self, args):
        keyword = args.keyword.strip()

        if not keyword:
            raise ValueError("검색어는 비워둘 수 없습니다.")

        month = self.validate_month(args.month) if args.month else None
        limit = self.validate_limit(args.limit) if args.limit is not None else None

        transactions = self.service.search_transactions(
            keyword=keyword,
            month=month,
            type_=args.type,
            category=args.category,
            limit=limit,
        )

        if not transactions:
            print("검색 결과가 없습니다.")
            return 0

        print(f"검색어: {keyword}")
        print("-" * 80)

        for transaction in transactions:
            tags = ""

            if transaction.tags:
                tags = " #" + " #".join(transaction.tags)

            memo = transaction.memo or ""

            print(
                f"{transaction.id} | "
                f"{transaction.date} | "
                f"{transaction.type} | "
                f"{transaction.category} | "
                f"{transaction.amount:,}원 | "
                f"{memo}"
                f"{tags}"
            )

        return 0
    
    def handle_update(self, args):
        date = None
        type_ = None
        category = None
        amount = None
        memo = None
        tags = None

        if args.date is not None:
            date = validate_date(args.date)

        if args.tx_type is not None:
            type_ = validate_transaction_type(args.tx_type)

        if args.category is not None:
            category = args.category.strip()

            if not category:
                raise ValueError("카테고리는 비워둘 수 없습니다.")

        if args.amount is not None:
            amount = validate_amount(args.amount)

        if args.memo is not None:
            memo = args.memo.strip()

        if args.tags is not None:
            tags = [
                tag.strip()
                for tag in args.tags.split(",")
                if tag.strip()
            ]

        if (
            date is None
            and type_ is None
            and category is None
            and amount is None
            and memo is None
            and tags is None
        ):
            raise ValueError("수정할 항목을 하나 이상 입력해야 합니다.")

        updated_transaction = self.service.update_transaction(
            transaction_id=args.id,
            date=date,
            type_=type_,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags,
        )

        print("거래가 수정되었습니다.")
        print(
            f"[{updated_transaction.id}] "
            f"{updated_transaction.date} | "
            f"{updated_transaction.type} | "
            f"{updated_transaction.category} | "
            f"{updated_transaction.amount:,}원 | "
            f"메모: {updated_transaction.memo or '-'} | "
            f"태그: {', '.join(updated_transaction.tags) if updated_transaction.tags else '-'}"
        )

        return 0

    @staticmethod
    def validate_month(month):
        if not isinstance(month, str):
            raise ValueError("월은 YYYY-MM 형식이어야 합니다.")
