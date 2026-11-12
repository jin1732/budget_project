import argparse
import csv
from pathlib import Path
from datetime import datetime 

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

        # 저장소 생성
        self.transaction_repository = TransactionRepository(
            str(data_path / "transactions.jsonl")
        )
        self.category_repository = CategoryRepository(
            str(data_path / "categories.jsonl")
        )
        self.budget_repository = BudgetRepository(
            str(data_path / "budgets.jsonl")
        )

        # 서비스 생성
        self.category_service = CategoryService(self.category_repository)
        self.service = BudgetService(
            self.transaction_repository,
            self.category_repository,
        )
        self.budget_service = BudgetLimitService(
            self.budget_repository,
            self.transaction_repository,
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
            required=True,
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
            "--month",
            help="조회 월 YYYY-MM",
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
            "delete": lambda args: print("🚧 delete 기능은 준비 중입니다."),
            "summary": lambda args: print("🚧 summary 기능은 준비 중입니다."),
            "export": lambda args: print("🚧 export 기능은 준비 중입니다."),
            "import": lambda args: print("🚧 import 기능은 준비 중입니다."),
            "category": lambda args: print("🚧 category 기능은 준비 중입니다."),
            "budget": lambda args: print("🚧 budget 기능은 준비 중입니다."),
            "search": lambda args: print("🚧 search 기능은 준비 중입니다."),
        }

        handler = handlers.get(args.command)
        if handler is None:
            parser.print_help()
            return 1

        return handler(args)

    def handle_add(self, args):
        print("\n📢 새로운 거래 입력을 시작합니다. (미입력 항목은 대화형으로 진행)")

        # 1. 날짜 입력
        date_input = getattr(args, 'date', None)
        if not date_input:
            date_input = input("- 날짜 (YYYY-MM-DD, 엔터 시 오늘): ").strip()
            if not date_input:
                date_input = datetime.now().strftime("%Y-%m-%d")

        date_input = self.validate_date(date_input)

        # 2. 유형 입력 (🌟 여기를 'tx_type'으로 수정!)
        transaction_type = getattr(args, 'tx_type', None) 
        if not transaction_type:
            while True:
                transaction_type = input("- 유형 (income/expense): ").strip().lower()
                if transaction_type in ['income', 'expense']:
                    break
                print("❌ 'income' 또는 'expense' 중에서 입력해주세요.")

        # 3. 카테고리 입력
        category = getattr(args, 'category', None)
        categories = self.service.get_categories(transaction_type)
        
        # 인자로 받은 카테고리가 유효하지 않으면 다시 질문
        if not category or category not in categories:
            while True:
                print(f"📍 사용 가능한 카테고리: {', '.join(categories)}")
                category = input("- 카테고리 선택: ").strip()
                if category in categories:
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
        elif isinstance(tags, str): # 문자열로 들어온 경우 리스트화
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

        transactions = iter(self.service.get_list(limit=limit))
        first_tx = next(transactions, None)

        if first_tx is None:
            print("거래 내역이 없습니다.")
            return

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
    
    def handle_summary(self, args):
        # 1. month 설정 및 검증
        if not args.month:
            month = datetime.now().strftime("%Y-%m")
            print(f"알림: --month가 입력되지 않아 이번 달({month}) 요약을 조회합니다.")
        else:
            month = self.validate_month(args.month)
            # validate_month가 None을 반환할 경우를 대비한 방어 코드
            if not month:
                print(f"[입력 오류] '{args.month}'는 올바른 날짜 형식이 아닙니다. (YYYY-MM 형식 필요)")
                return 1

        # 2. top 값 안전하게 가져오기
        top = args.top if args.top is not None else 5
        if top <= 0:
            print("[입력 오류] top은 1 이상의 숫자여야 합니다.")
            return 1

        # 3. 서비스 호출
        summary = self.service.get_monthly_summary(month, top=top)

        # 4. 데이터 존재 여부 확인 (None이거나 빈 딕셔너리인 경우)
        if not summary:
            print(f"\n[{month}]에 등록된 데이터가 없습니다.")
            return 0

        # 5. 결과 출력 (get 메서드를 사용하여 KeyError 방지)
        print(f"\n[{month} 요약]")
        print("-" * 40)
        print(f"총 수입: {summary.get('income', 0):,}원")
        print(f"총 지출: {summary.get('expense', 0):,}원")
        print(f"잔액: {summary.get('balance', 0):,}원")

        # 6. 지출 TOP 출력
        print(f"\n[지출 TOP {top}]")
        top_categories = summary.get("top_categories", [])
        if not top_categories:
            print("지출 내역이 없습니다.")
        else:
            for i, (category, amount) in enumerate(top_categories, start=1):
                print(f"{i}. {category}: {amount:,}원")

        # 7. 예산 경고 출력
        alerts = summary.get("budget_alerts", [])
        if alerts:
            print("\n⚠️  예산 경고")
            for a in alerts:
                mark = "🚨 초과!" if a.get("is_over", False) else ""
                print(
                    f"  - {a.get('category', '알 수 없음')}: {a.get('spent', 0):,} / {a.get('budget', 0):,}원 "
                    f"({a.get('usage_rate', 0):.1f}%) {mark}"
                )

        return 0

    def handle_export(self, args):
        # 1. 필수 인자 검증 로직 추가
        if not args.month and not (args.date_from and args.date_to):
            print("오류: export 시 --month 또는 --from과 --to를 모두 입력해야 합니다.")
            print("힌트: 'python main.py export --month 2023-10' 또는 'python main.py export --from 2023-01-01 --to 2023-01-31'을 사용하세요.")
            return 1  # 검증 실패 시 여기서 함수 종료

        # 2. 검증 통과 후 서비스 호출 (이 부분이 검증 로직 아래에 있어야 합니다!)
        file_path = self.service.export_transactions_to_csv(
            filename=args.out,
            month=args.month,
            category=args.category,
            tx_type=args.tx_type,
            date_from=args.date_from, # dest="date_from"으로 설정했으므로 이렇게 접근!
            date_to=args.date_to,     # dest="date_to"로 설정했으므로 이렇게 접근!
        )
        print(f"CSV 파일로 내보냈습니다: {file_path}")
        return 0

    def handle_import(self, args):
        # 1. CSV 파일로부터 데이터를 가져옵니다. 
        # (현재 service의 이 함수는 성공한 '숫자'를 반환하고 있습니다.)
        result = self.service.import_transactions_from_csv(
            filename=args.filename,
            keep_id=args.keep_id,
        )

        # 2. 결과 출력 (result가 정수이므로 바로 출력)
        print(f"가져오기 완료: 성공 {result}건")

        # 3. 함수 종료
        return 0
    
    def handle_category(self, args):
        if args.category_command == "add":
            name = args.name.strip()
            tx_type = validate_transaction_type(args.tx_type)

            if not name:
                raise ValueError("카테고리 이름은 비워둘 수 없습니다.")

            if self.category_repository.exists(name, tx_type):
                print(f"이미 존재하는 카테고리입니다: {name} ({tx_type})")
                return 0

            category = Category(
                name=name,
                type=tx_type,
            )

            self.category_repository.save(category)

            print("카테고리가 추가되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {tx_type}")
            return 0

        elif args.category_command == "list":
            categories = self.category_repository.get_all()

            if not categories:
                print("등록된 카테고리가 없습니다.")
                return 0

            print("카테고리 목록")
            print("-" * 40)

            for category in categories:
                print(f"{category.name} | {category.type}")

            return 0

        elif args.category_command == "remove":
            name = args.name.strip()
            tx_type = validate_transaction_type(args.tx_type)

            if not name:
                raise ValueError("카테고리 이름은 비워둘 수 없습니다.")

            deleted = self.category_repository.delete(name, tx_type)

            if not deleted:
                print(f"삭제할 카테고리를 찾을 수 없습니다: {name} ({tx_type})")
                return 0

            print("카테고리가 삭제되었습니다.")
            print(f"이름: {name}")
            print(f"유형: {tx_type}")
            return 0

        else:
            raise ValueError("알 수 없는 category 명령어입니다.")
    
    def handle_budget(self, args):
        if args.budget_command == "set":
            month = self.validate_month(args.month)
            amount = validate_amount(args.amount)

            budget = Budget(
                month=month,
                amount=amount,
            )

            self.budget_service.set_budget(budget)

            print("예산이 설정되었습니다.")
            print(f"월: {month}")
            print(f"금액: {amount:,}원")
            return 0

        elif args.budget_command == "list":
            month = self.validate_month(args.month) if args.month else None

            budgets = self.budget_service.get_budgets(month)

            if not budgets:
                print("등록된 예산이 없습니다.")
                return 0

            print("예산 목록")
            print("-" * 30)

            for budget in budgets:
                print(f"{budget.month} | {budget.amount:,}원")

            return 0

        elif args.budget_command == "check":
            month = self.validate_month(args.month)

            result = self.budget_service.check_budget(month)

            if not result:
                print("확인할 예산이 없습니다.")
                return 0

            print(f"{month} 예산 사용 현황")
            print("-" * 40)
            print(f"예산: {result['budget']:,}원")
            print(f"지출: {result['spent']:,}원")
            print(f"사용률: {result['usage_rate']:.1f}%")
            print(f"남은 금액: {result['remaining']:,}원")

            if result["is_over"]:
                print("경고: 예산을 초과했습니다.")
            else:
                print("상태: 정상")

            return 0

        else:
            raise ValueError("알 수 없는 budget 명령어입니다.")
    
    def handle_search(self, args):
        # 1. 모든 인자를 안전하게 가져옵니다.
        # argparse의 dest 설정과 일치해야 합니다. (예: dest='tx_type'이면 'tx_type'으로 가져와야 함)
        keyword_raw = getattr(args, 'keyword', None)
        category = getattr(args, 'category', None)
        month_raw = getattr(args, 'month', None)
        tx_type = getattr(args, 'tx_type', None) # 'type' 대신 'tx_type'으로 수정
        limit_raw = getattr(args, 'limit', None)
        date_from = getattr(args, 'date_from', None)
        date_to = getattr(args, 'date_to', None)

        # 2. keyword 처리
        keyword = keyword_raw.strip() if keyword_raw is not None else None

        # 3. 검색 조건 검사
        # 사용자가 입력한 모든 조건 중 하나라도 True이면 통과
        if not any([keyword, category, month_raw, tx_type, date_from, date_to]):
            raise ValueError("검색 조건(검색어, 카테고리, 월, 타입, 또는 기간) 중 하나는 입력해야 합니다.")

        # 4. 입력값 검증 및 변환
        # month가 들어왔다면 date_from/to로 변환
        if month_raw:
            month_val = self.validate_month(month_raw)
            date_from = f"{month_val}-01"
            date_to = f"{month_val}-31"
            
        limit = self.validate_limit(limit_raw) if limit_raw is not None else None

        # 5. 서비스 호출
        transactions = self.service.search_transactions(
            keyword=keyword,
            category=category,
            type_=tx_type,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        # 6. 결과 출력
        # 제너레이터가 비어있는지 확인하기 위해 리스트로 변환하거나 
        # 첫 번째 요소를 확인해야 합니다. (스트리밍을 유지하려면 주의 필요)
        tx_list = list(transactions)
        if not tx_list:
            print("검색 결과가 없습니다.")
            return 0

        print(f"\n[검색 결과] (조건: ", end="")
        conditions = []
        if keyword: conditions.append(f"키워드={keyword}")
        if category: conditions.append(f"카테고리={category}")
        if month_raw: conditions.append(f"월={month_raw}")
        if tx_type: conditions.append(f"타입={tx_type}")
        if date_from or date_to: conditions.append(f"기간={date_from}~{date_to}")
        print(", ".join(conditions) + ")\n")
            
        print("-" * 80)

        for transaction in tx_list:
            tags = " #" + " #".join(transaction.tags) if transaction.tags else ""
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
