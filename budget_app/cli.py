from datetime import datetime
from budget_app.models import Transaction
from budget_app.repositories import TransactionRepository
from budget_app.services import BudgetService


class BudgetCLI:
    def __init__(self, file_path: str):
        self.repository = TransactionRepository(file_path)
        self.service = BudgetService(self.repository)

    def show_menu(self):
        print("\n====== 가계부 프로그램 ======")
        print("1. 거래추가")
        print("2. 전체 거래 조회")
        print("3. 수입/지출 요약")
        print("4. 종료")
        print("===========================")

    def add_transaction(self):
        print("\n[거래추가]")
        type_ = input("유형 (income/expense): ").strip()
        category = input("카테고리: ").strip()
        amount = int(input("금액: ").strip())
        memo = input("메모: ").strip()
        tags_input = input("태그(쉼표로 구분): ").strip()
        tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

        transaction = Transaction(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            type=type_,
            category=category,
            amount=amount,
            memo=memo,
            tags=tags
        )

        self.service.add_transaction(transaction)
        print("거래가 저장되었습니다.")

    def show_all_transactions(self):
        print("\n[전체 거래 조회]")
        transactions = self.service.get_all_transaction()  # 이름 확인 필요

        if not transactions:
            print("저장된 거래가 없습니다.")
            return

        for t in transactions:
            print(f"{t.date} | {t.type} | {t.category} | {t.amount}원 | {t.memo} | {t.tags}")

    def show_summary(self):
        print("\n[수입/지출 요약]")
        summary = self.service.get_total_summary()
        print(f"총 수입: {summary['income']}원")
        print(f"총 지출: {summary['expense']}원")
        print(f"잔액: {summary['balance']}원")

    def run(self):
        while True:
            self.show_menu()
            choice = input("메뉴를 선택하세요: ").strip()

            if choice == "1":
                self.add_transaction()
            elif choice == "2":
                self.show_all_transactions()
            elif choice == "3":
                self.show_summary()
            elif choice == "4":
                print("프로그램을 종료합니다.")
                break
            else:
                print("잘못된 입력입니다. 다시 선택해 주세요.")
                