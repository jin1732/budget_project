import argparse
import calendar
import re
from pathlib import Path
from datetime import datetime 
from itertools import chain

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


def _normalize_text(value):
    if value is None:
        return None
    value = value.strip()
    return value if value else None


class BudgetCLI:
    def __init__(self):
        self.service = None
        self.category_service = None
        self.budget_service = None
        self.transaction_repository = None
        self.category_repository = None
        self.budget_repository = None
        self.parser = self.create_parser()

    def setup_services(self, data_dir="data"):
        """저장소 및 서비스 객체 생성 및 의존성 주입"""
        data_path = Path(data_dir)
        data_path.mkdir(parents=True, exist_ok=True)

        self.transaction_repository = TransactionRepository(
            str(data_path / "transactions.jsonl")
        )
        self.category_repository = CategoryRepository(
            str(data_path / "categories.jsonl")
        )
        self.budget_repository = BudgetRepository(
            str(data_path / "budgets.jsonl")
        )

        self.category_service = CategoryService(
            self.category_repository,
            self.transaction_repository,
        )
        self.budget_service = BudgetLimitService(
            self.budget_repository,
            self.transaction_repository,
        )
        self.service = BudgetService(
            self.transaction_repository,
            self.category_repository,
            self.budget_service,
        )
        self._ensure_default_categories()

    def _ensure_default_categories(self):
        existing = self.category_repository.get_all()
        if existing:
            return

        defaults = [
            Category(name="식비", type="expense"),
            Category(name="교통", type="expense"),
            Category(name="취미", type="expense"),
            Category(name="생필품", type="expense"),
            Category(name="월급", type="income"),
            Category(name="부수입", type="income"),
            Category(name="기타", type="income"),
        ]
        for category in defaults:
            self.category_repository.save(category)

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
        add_parser = subparsers.add_parser(
            "add",
            help="거래 추가 (대화형 입력)",
            description="인자를 생략하면 대화형으로 입력을 받습니다. 모든 필드는 대화형 입력이 기본입니다.",
        )
        add_parser.add_argument("--date", help="날짜 YYYY-MM-DD")
        add_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="거래 유형 income 또는 expense",
        )
        add_parser.add_argument("--category", help="카테고리")
        add_parser.add_argument("--amount", type=int, help="금액")
        add_parser.add_argument("--memo", default=None, help="메모")
        add_parser.add_argument("--tags", default=None, help="태그 목록 (쉼표 구분)")

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
            default=10,
            help="출력 개수 제한 (기본값: 10)",
        )

        # summary
        summary_parser = subparsers.add_parser("summary", help="월별 요약")
        summary_parser.add_argument("--month", help="조회할 월 (YYYY-MM)")
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
            nargs="?",
            default=None,
            help="CSV 저장 경로",
        )
        export_parser.add_argument(
            "--month",
            default=None,
            help="월 필터 (YYYY-MM)",
        )
        export_parser.add_argument(
            "--category",
            default=None,
            help="카테고리 필터",
        )
        export_parser.add_argument(
            "--type",
            "--tx-type",
            dest="tx_type",
            choices=["income", "expense"],
            default=None,
            help="유형 필터",
        )
        export_parser.add_argument(
            "--from",
            dest="date_from",
            default=None,
            help="시작일 (YYYY-MM-DD)",
        )
        export_parser.add_argument(
            "--to",
            dest="date_to",
            default=None,
            help="종료일 (YYYY-MM-DD)",
        )

        # import
        import_parser = subparsers.add_parser("import", help="CSV 가져오기")
        import_parser.add_argument(
            "--from",
            dest="filename",
            required=True,
            help="가져올 CSV 파일 경로",
        )
        import_parser.add_argument(
            "--keep-id",
            dest="keep_id",
            action="store_true",
            help="원본 id 유지 (기본: 새 id 생성)",
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
        category_add_parser.add_argument("name", nargs="?", help="카테고리 이름")
        category_add_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="카테고리 유형",
        )

        category_list_parser = category_subparsers.add_parser(
            "list",
            help="카테고리 목록 조회",
        )
        category_list_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="카테고리 유형 필터",
        )

        category_remove_parser = category_subparsers.add_parser(
            "remove",
            help="카테고리 삭제",
        )
        category_remove_parser.add_argument("name", nargs="?", help="카테고리 이름")
        category_remove_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="카테고리 유형",
        )
        category_remove_parser.add_argument(
        "--replace-with",
        dest="replace_with",
        help="사용 중인 카테고리를 대체할 카테고리 이름",
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
        budget_set_parser.add_argument("--amount", type=int, required=True, help="예산 금액")

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
        search_parser = subparsers.add_parser("search", help="거래 검색")
        search_parser.add_argument(
            "--q",
            dest="keyword",
            help="메모 키워드 검색",
        )
        search_parser.add_argument(
            "--category",
            help="카테고리 필터",
        )
        search_parser.add_argument(
            "--type",
            dest="tx_type",
            choices=["income", "expense"],
            help="유형 필터",
        )
        search_parser.add_argument(
            "--from",
            dest="date_from",
            help="시작일 (YYYY-MM-DD)",
        )
        search_parser.add_argument(
            "--to",
            dest="date_to",
            help="종료일 (YYYY-MM-DD)",
        )
        search_parser.add_argument(
            "--tag",
            help="태그 필터",
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
        update_parser.add_argument("--amount", type=int, help="금액")
        update_parser.add_argument("--memo", help="메모")
        update_parser.add_argument(
            "--tags",
            help="태그 목록 (쉼표 구분)",
        )

        # delete
        delete_parser = subparsers.add_parser("delete", help="거래 삭제")
        delete_parser.add_argument(
            "--id",
            required=True,
            help="삭제할 거래 ID",
        )
        delete_parser.add_argument(
            "--yes",
            action="store_true",
            help="확인 없이 삭제",
        )

        return parser
            
    @handle_cli_errors
    def run(self, argv=None):
        parser = self.create_parser()
        if parser is None:
            raise RuntimeError("create_parser() must return an ArgumentParser object.")

        args = parser.parse_args(argv)

        data_dir = getattr(args, "data_dir", "data")
        self.setup_services(data_dir)

        handlers = {
            "add": self.handle_add,
            "list": self.handle_list,
            "update": self.handle_update,
            "delete": self.handle_delete,
            "summary": self.handle_summary,
            "export": self.handle_export,
            "import": self.handle_import,
            "category": self.handle_category,
            "budget": self.handle_budget,
            "search": self.handle_search,
        }

        handler = handlers.get(args.command)
        if handler is None:
            parser.print_help()
            return 1

        return handler(args)

    def handle_add(self, args):
        # 필수 인자가 모두 있는지 확인
        is_interactive = not (args.date and args.tx_type and args.category and args.amount)
        
        if is_interactive:
            print("\n📢 새로운 거래 입력을 시작합니다. (미입력 항목은 대화형으로 진행)")

        # 1. 날짜 입력
        date_input = getattr(args, 'date', None)
        if not date_input:
            date_input = input("- 날짜 (YYYY-MM-DD, 엔터 시 오늘): ").strip()
            if not date_input:
                date_input = datetime.now().strftime("%Y-%m-%d")
        date_input = validate_date(date_input) 

        # 2. 유형 입력
        transaction_type = getattr(args, 'tx_type', None) 
        if not transaction_type:
            while True:
                transaction_type = input("- 유형 (income/expense): ").strip().lower()
                if transaction_type in ['income', 'expense']:
                    break
                print("❌ 'income' 또는 'expense' 중에서 입력해주세요.")

        valid_categories = [
            category.name
            for category in self.category_service.get_all_categories()
            if category.type == transaction_type
        ]
        if not valid_categories:
            valid_categories = self.service.get_categories(transaction_type)

        # 3. 카테고리 입력
        category = getattr(args, 'category', None)
        if not category or category not in valid_categories:
            while True:
                print(f"📍 사용 가능한 카테고리: {', '.join(valid_categories)}")
                category = input("- 카테고리 선택: ").strip()
                if category in valid_categories:
                    break
                print(f"❌ '{category}'은(는) 목록에 없습니다. 다시 입력해주세요.")

        # 4. 금액 입력
        amount = getattr(args, 'amount', None)
        while True:
            if amount is None:
                raw = input("- 금액: ").strip()
            else:
                raw = str(amount).strip()
            try:
                amount = int(raw)
                if amount <= 0:
                    print("❌ 금액은 1원 이상이어야 합니다.")
                    amount = None
                    continue
                break
            except (ValueError, TypeError):
                print("❌ 금액은 숫자로 입력 가능합니다.")
                amount = None

        # 5. 메모 및 태그
        memo = getattr(args, 'memo', None)
        if memo is None:
            memo = input("- 메모 (선택): ").strip()

        tags = getattr(args, 'tags', None)
        if tags is None:
            tags_input = input("- 태그 (쉼표로 구분, 선택): ").strip()
            tags = [t.strip() for t in tags_input.split(",")] if tags_input else []
        elif isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        # 객체 생성 및 저장
        transaction = Transaction(
            date=date_input,
            type=transaction_type,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags
        )

        new_id = self.service.add_transaction(transaction)
        
        print(f"\n✅ 거래가 성공적으로 저장되었습니다!")
        print(f"🆔 생성된 거래 ID: {new_id}")
        return 0

    def handle_list(self, args):
        limit = self.validate_limit(args.limit)
        transaction_type = getattr(args, 'tx_type', None) or getattr(args, 'type', None)

        transactions = iter(self.service.get_list(limit=limit, type=transaction_type))
        first_tx = next(transactions, None)

        if first_tx is None:
            print("거래 내역이 없습니다.")
            return 0

        def print_transaction(tx):
            memo_text = tx.memo if tx.memo else "-"
            tags_text = ", ".join(tx.tags) if tx.tags else "-"
            print(
                f"[{tx.id}] {tx.date} | {tx.type} | {tx.category} | "
                f"{tx.amount:,}원 | 메모: {memo_text} | 태그: {tags_text}"
            )

        print_transaction(first_tx)
        for tx in transactions:
            print_transaction(tx)
        return 0

    def handle_summary(self, args):
        if not args.month:
            month = datetime.now().strftime("%Y-%m")
            print(f"알림: --month가 입력되지 않아 이번 달({month}) 요약을 조회합니다.")
        else:
            month = self.validate_month(args.month)
            if not month:
                print(f"[입력 오류] '{args.month}'는 올바른 날짜 형식이 아닙니다. (YYYY-MM 형식 필요)")
                return 1

        top = args.top if args.top is not None else 5
        if top <= 0:
            print("[입력 오류] top은 1 이상의 숫자여야 합니다.")
            return 1

        summary = self.service.get_monthly_summary(month, top=top)

        if not summary:
            print(f"\n[{month}]에 등록된 데이터가 없습니다.")
            return 0

        print(f"\n[{month} 요약]")
        print("-" * 40)
        print(f"총 수입: {summary.get('income', 0):,}원")
        print(f"총 지출: {summary.get('expense', 0):,}원")
        print(f"잔액: {summary.get('balance', 0):,}원")

        budget_info = self.budget_service.check_budget(month)
        if budget_info:
            print(f"예산: {budget_info['budget']:,}원")
            print(f"사용률: {budget_info['usage_rate']:.1f}%")
            if budget_info['is_over']:
                print("경고: 예산을 초과했습니다.")
            else:
                print("상태: 정상")

        print(f"\n[지출 TOP {top}]")
        top_categories = summary.get("top_categories", [])
        if not top_categories:
            print("지출 내역이 없습니다.")
        else:
            for i, (category, amount) in enumerate(top_categories, start=1):
                print(f"{i}. {category}: {amount:,}원")

        return 0

    def handle_export(self, args):
        if not args.out:
            print("오류: export 시 --out 경로는 필수입니다.")
            print("힌트: 'python3 -m budget_app export --out transactions.csv --month 2026-11' 또는 'python3 -m budget_app export --out transactions.csv --from 2023-01-01 --to 2023-01-31'")
            return 1

        if not args.month and not (args.date_from and args.date_to):
            print("오류: export 시 --month 또는 --from과 --to를 모두 입력해야 합니다.")
            print("힌트: 'python3 -m budget_app export --out transactions.csv --month 2023-10' 또는 'python3 -m budget_app export --out transactions.csv --from 2023-01-01 --to 2023-01-31'")
            return 1

        file_path, row_count = self.service.export_transactions_to_csv(
            filename=args.out,
            month=args.month,
            category=args.category,
            tx_type=args.tx_type,
            date_from=args.date_from,
            date_to=args.date_to,
        )
        print(f"CSV 파일로 내보냈습니다: {file_path} (총 {row_count}건)")
        return 0

    def handle_import(self, args):
        result = self.service.import_transactions_from_csv(
            filename=args.filename,
            keep_id=args.keep_id,
        )
        print(f"가져오기 완료: 성공 {result}건 (반영 위치: {self.transaction_repository.file_path})")
        return 0

    def handle_category(self, args):
        if args.category_command == "add":
            name = (args.name or "").strip()
            while not name:
                print("카테고리 이름은 비워둘 수 없습니다.")
                name = input("카테고리 이름: ").strip()

            tx_type = getattr(args, "tx_type", None)
            while tx_type not in ("income", "expense"):
                print("카테고리 유형은 income 또는 expense만 가능합니다.")
                tx_type = input("카테고리 유형 (income/expense): ").strip().lower()

            tx_type = validate_transaction_type(tx_type)

            if self.category_repository.exists(name, tx_type):
                print(f"이미 존재하는 카테고리입니다: {name} ({tx_type})")
                return 0

            category = Category(name=name, type=tx_type)
            self.category_repository.save(category)

            print("카테고리가 추가되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {tx_type}")
            return 0

        elif args.category_command == "list":
            categories = self.category_repository.get_all()
            tx_type = getattr(args, "tx_type", None)
            if tx_type:
                tx_type = validate_transaction_type(tx_type)
                categories = [c for c in categories if c.type == tx_type]

            if not categories:
                print("등록된 카테고리가 없습니다.")
                return 0

            print("카테고리 목록")
            print("-" * 40)
            for category in categories:
                print(f"{category.name} | {category.type}")
            return 0

        elif args.category_command == "remove":
            name = (args.name or "").strip()
            while not name:
                print("카테고리 이름은 비워둘 수 없습니다.")
                name = input("카테고리 이름: ").strip()

            tx_type = getattr(args, "tx_type", None)
            while tx_type not in ("income", "expense"):
                print("카테고리 유형은 income 또는 expense만 가능합니다.")
                tx_type = input("카테고리 유형 (income/expense): ").strip().lower()

            tx_type = validate_transaction_type(tx_type)

            replace_with = getattr(args, "replace_with", None)
            if replace_with is not None:
                replace_with = replace_with.strip()
                if not replace_with:
                    replace_with = None

            self.category_service.remove_category(name, tx_type, replace_with)

            print("카테고리가 삭제되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {tx_type}")
            if replace_with:
                print(f"대체 카테고리: {replace_with}")
            return 0

        raise ValueError("알 수 없는 category 명령어입니다.")

    def handle_budget(self, args):
        if args.budget_command == "set":
            month = self.validate_month(args.month)
            amount = validate_amount(args.amount)

            budget = Budget(month=month, amount=amount)
            replaced = self.budget_service.set_budget(budget)

            if replaced:
                print("기존 예산을 덮어썼습니다.")
            else:
                print("새 예산을 추가했습니다.")

            print("예산이 설정되었습니다.")
            print(f"월: {month}")
            print(f"금액: {amount:,}원")
            return 0

        elif args.budget_command == "list":
            month = getattr(args, "month", None)
            budgets = self.budget_service.list_budgets(month)

            if not budgets:
                print("설정된 예산이 없습니다.")
                return 0

            print("예산 목록")
            print("-" * 30)
            for budget in budgets:
                print(f"{budget.month} | {budget.amount:,}원")
            return 0

        elif args.budget_command == "check":
            month = self.validate_month(args.month)
            result = self.budget_service.check_budget(month)

            if result is None:
                print(f"{month} 예산이 설정되지 않았습니다.")
                return 0

            print(f"{month} 예산 사용 현황")
            print("-" * 40)
            print(f"예산: {result['budget']:,}원")
            print(f"지출: {result['spent']:,}원")
            print(f"사용률: {result['usage_rate']:.1f}%")
            print(f"남은 금액: {result['remaining']:,}원")
            print("상태: 정상" if not result['is_over'] else "상태: 초과")
            return 0

        raise ValueError("알 수 없는 budget 명령어입니다.")

    def handle_search(self, args):
        keyword_raw = getattr(args, "keyword", None)
        category_raw = getattr(args, "category", None)
        type_raw = getattr(args, "tx_type", None) or getattr(args, "type", None)
        date_from_raw = getattr(args, "date_from", None)
        date_to_raw = getattr(args, "date_to", None)
        tag_raw = getattr(args, "tag", None)

        keyword = _normalize_text(keyword_raw)
        category = _normalize_text(category_raw)
        type_name = _normalize_text(type_raw)
        date_from = _normalize_text(date_from_raw)
        date_to = _normalize_text(date_to_raw)
        tag = _normalize_text(tag_raw)

        if type_name:
            type_name = validate_transaction_type(type_name)

        if not any([keyword, category, type_name, date_from, date_to, tag]):
            raise ValueError("검색 조건(--q, --category, --type, --from, --to, --tag) 중 하나는 입력해야 합니다.")

        if date_from:
            date_from = validate_date(date_from)
        if date_to:
            date_to = validate_date(date_to)

        if date_from and date_to and date_from > date_to:
            raise ValueError("--from 날짜는 --to 날짜보다 늦을 수 없습니다.")

        transactions = self.service.search_transactions(
            keyword=keyword,
            category=category,
            type_=type_name,
            date_from=date_from,
            date_to=date_to,
            tag=tag,
        )

        iterator = iter(transactions)
        first_tx = next(iterator, None)

        if first_tx is None:
            print("검색 결과가 없습니다.")
            return 0

        conditions = []
        if keyword:
            conditions.append(f"키워드={keyword}")
        if category:
            conditions.append(f"카테고리={category}")
        if type_name:
            conditions.append(f"타입={type_name}")
        if date_from or date_to:
            conditions.append(f"기간={date_from or ''}~{date_to or ''}")
        if tag:
            conditions.append(f"태그={tag}")

        print(f"\n[검색 결과] (조건: {', '.join(conditions)})\n")
        print("-" * 80)

        for transaction in chain([first_tx], iterator):
            tags = " #" + " #".join(transaction.tags) if transaction.tags else ""
            memo = transaction.memo or ""
            print(
                f"{transaction.id} | "
                f"{transaction.date} | "
                f"{transaction.type} | "
                f"{transaction.category} | "
                f"{transaction.amount:,}원 | "
                f"{memo}{tags}"
            )

        return 0

    def handle_update(self, args):
        # 먼저 대상 거래 ID가 실제로 존재하는지 확인한다.
        # 존재하지 않는 ID는 "없는 ID" 메시지로 처리하고, 예외가 밖으로 새지 않도록
        # ValueError 그대로 CLI 에러 핸들러로 넘긴다.
        self.service.get_transaction_by_id(args.id)

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
            tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]

        if date is None and type_ is None and category is None and amount is None and memo is None and tags is None:
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

    def handle_delete(self, args):
        transaction_id = getattr(args, "id", None)

        if not transaction_id:
            print("삭제할 거래 ID가 필요합니다.")
            return 1

        target = self.service.get_transaction_by_id(transaction_id)
        if target is None:
            print("해당 ID의 거래를 찾을 수 없습니다.")
            return 1

        print("다음 거래를 삭제합니다.")
        print(
            f"[{target.id}] {target.date} | {target.type} | "
            f"{target.category} | {target.amount:,}원 | "
            f"메모: {target.memo or '-'}"
        )

        if not getattr(args, "yes", False):
            answer = input("정말 삭제하시겠습니까? (y/N): ").strip().lower()
            if answer not in ("y", "yes"):
                print("삭제를 취소했습니다.")
                return 0

        result = self.service.delete_transaction(transaction_id)

        if result is False:
            print("삭제 중 문제가 발생했습니다.")
            return 1

        print("거래가 삭제되었습니다.")
        return 0

    def validate_month(self, month):
        if not month:
            return None

        if not re.match(r"^\d{4}-\d{2}$", month):
            raise ValueError("월은 YYYY-MM 형식이어야 합니다.")

        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError("올바른 월을 입력하세요. 예: 2026-11")

        return month

    @staticmethod
    def validate_limit(limit):
        if limit is None:
            return 10

        try:
            val = int(limit)
        except (ValueError, TypeError):
            raise ValueError("제한값(limit)은 올바른 숫자 형식이어야 합니다.")

        if val <= 0:
            raise ValueError("제한값은 1 이상의 정수여야 합니다.")

        return val
