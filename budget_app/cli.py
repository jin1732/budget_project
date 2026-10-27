import argparse
from pathlib import Path

from budget_app.decorators import handle_cli_errors
from budget_app.models import Transaction, Category
from budget_app.repositories import TransactionRepository, CategoryRepository
from budget_app.services import BudgetService, CategoryService
from budget_app.validators import (
    validate_amount,
    validate_date,
    validate_transaction_type,
)

class BudgetCLI:
    def __init__(self, data_dir="data"):
        self.setup_services(data_dir)

    def setup_services(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        transaction_file = self.data_dir / "transactions.jsonl"
        category_file = self.data_dir / "categories.jsonl"

        transaction_repository = TransactionRepository(str(transaction_file))
        category_repository = CategoryRepository(str(category_file))

        self.service = BudgetService(transaction_repository)
        self.category_service = CategoryService(category_repository)

    def create_parser(self):
        parser = argparse.ArgumentParser(
            prog="python -m budget_app",
            description="가계부 CLI 앱"
        )

        parser.add_argument(
            "--data-dir",
            default="data",
            help="데이터 저장 폴더 경로 (기본값: data)"
        )

        subparsers = parser.add_subparsers(dest="command", required=True)

        # add
        add_parser = subparsers.add_parser("add", help="거래 추가")
        add_parser.add_argument("--date", required=True, help="거래 날짜 (YYYY-MM-DD)")
        add_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="거래 유형 (income 또는 expense)"
        )
        add_parser.add_argument("--amount", required=True, help="금액")
        add_parser.add_argument("--category", required=True, help="카테고리")
        add_parser.add_argument("--memo", default="", help="메모")
        add_parser.add_argument("--tags", default="", help="태그(쉼표로 구분)")

        # list
        list_parser = subparsers.add_parser("list", help="거래 목록 조회")
        list_parser.add_argument("--limit", type=int, default=None, help="최대 출력 개수")
        list_parser.add_argument("--month", help="조회할 월 (YYYY-MM)")
        list_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="거래 유형 필터"
        )
        list_parser.add_argument("--category", help="카테고리 필터")

        # summary
        summary_parser = subparsers.add_parser("summary", help="월별 요약 조회")
        summary_parser.add_argument(
            "--month",
            required=True,
            help="조회할 월 (형식: YYYY-MM)"
        )
        summary_parser.add_argument(
            "-t", "--top",
            type=int,
            default=3,
            help="카테고리별 지출 합계 TOP N (기본값: 3)"
        )

        # export
        export_parser = subparsers.add_parser("export", help="CSV 내보내기")
        export_parser.add_argument("--out", default=None, help="내보낼 CSV 파일 경로")

        # category
        category_parser = subparsers.add_parser("category", help="카테고리 관리")
        category_subparsers = category_parser.add_subparsers(
            dest="category_command",
            required=True
        )

        category_add_parser = category_subparsers.add_parser("add", help="카테고리 추가")
        category_add_parser.add_argument("--name", required=True, help="카테고리 이름")
        category_add_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="카테고리 타입"
        )

        category_subparsers.add_parser("list", help="카테고리 목록")

        category_remove_parser = category_subparsers.add_parser("remove", help="카테고리 삭제")
        category_remove_parser.add_argument("--name", required=True, help="카테고리 이름")
        category_remove_parser.add_argument(
            "--type",
            dest="tx_type",
            required=True,
            choices=["income", "expense"],
            help="카테고리 타입"
        )

        return parser

    @handle_cli_errors
    def run(self, argv=None):
        parser = self.create_parser()
        args = parser.parse_args(argv)

        self.setup_services(args.data_dir)

        if args.command == "add":
            return self.handle_add(args)
        elif args.command == "list":
            return self.handle_list(args)
        elif args.command == "summary":
            return self.handle_summary(args)
        elif args.command == "export":
            return self.handle_export(args.out)
        elif args.command == "category":
            return self.handle_category(args)
        else:
            print("지원하지 않는 명령입니다.")
            return 1

    def handle_add(self, args):
        date = validate_date(args.date)
        type_ = validate_transaction_type(args.tx_type)
        category = args.category.strip()
        amount = validate_amount(args.amount)
        memo = args.memo.strip()

        tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

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
            transactions = [t for t in transactions if t.date.startswith(args.month)]

        if args.tx_type:
            transactions = [t for t in transactions if t.type == args.tx_type]

        if args.category:
            keyword = args.category.strip().lower()
            transactions = [
                t for t in transactions
                if t.category.strip().lower() == keyword
            ]

        transactions = sorted(transactions, key=lambda t: t.date, reverse=True)

        if args.limit is not None:
            transactions = transactions[:args.limit]

        if not transactions:
            print("거래 내역이 없습니다.")
            return 0

        for t in transactions:
            print(
                f"{t.date} | {t.type} | {t.category} | {t.amount}원 | "
                f"메모: {t.memo or '-'} | 태그: {', '.join(t.tags) if t.tags else '-'}"
            )
        return 0

    def handle_summary(self, args):
        transactions = self.service.get_all_transactions()

        month_transactions = [t for t in transactions if t.date.startswith(args.month)]

        income = sum(t.amount for t in month_transactions if t.type == "income")
        expense = sum(t.amount for t in month_transactions if t.type == "expense")

        print(f"{args.month} 요약")
        print(f"총 수입: {income}원")
        print(f"총 지출: {expense}원")
        print(f"잔액: {income - expense}원")

        expense_by_category = {}
        for t in month_transactions:
            if t.type == "expense":
                expense_by_category[t.category] = expense_by_category.get(t.category, 0) + t.amount

        top_items = sorted(
            expense_by_category.items(),
            key=lambda item: item[1],
            reverse=True
        )[:args.top]

        if top_items:
            print(f"\n지출 카테고리 TOP {args.top}")
            for idx, (category, amount) in enumerate(top_items, start=1):
                print(f"{idx}. {category}: {amount}원")
        else:
            print("\n해당 월의 지출 내역이 없습니다.")

        return 0

    def handle_export(self, out_path=None):
        file_path = self.service.export_transactions_to_csv(out_path)
        print(f"CSV 내보내기 완료: {file_path}")
        return 0

    def handle_category(self, args):
        if args.category_command == "add":
            category = Category(name=args.name.strip(), type=args.tx_type)
            self.category_service.add_category(category)
            print("카테고리가 추가되었습니다.")
            return 0

        elif args.category_command == "list":
            categories = self.category_service.get_all_categories()

            if not categories:
                print("등록된 카테고리가 없습니다.")
                return 0

            for c in categories:
                print(f"{c.type} | {c.name}")
            return 0

        elif args.category_command == "remove":
            self.category_service.remove_category(args.name.strip(), args.tx_type)
            print("카테고리가 삭제되었습니다.")
            return 0

        else:
            print("category 하위 명령이 필요합니다. (add/list/remove)")
            return 1