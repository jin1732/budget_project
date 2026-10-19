from models import Transaction
from repositories import TransactionRepository
from datetime import datetime

class BudgetService:
    def __init__(self, repository:TransactionRepository):
        # 저장소를 주입(Injection)받아서 사용합니다.
        self.repo = repository

    def add_transaction(self, amount, category, description, trans_type):
        """
        새로운 거래 내역을 생성하고 저장소에 저장합니다.
        """
        # 1. Transaction 객체(실제 데이터) 생성
        new_transaction = Transaction(
            amount=amount,
            category=category,
            description=description, 
            type=trans_type, # '수입' 또는 '지출'
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")# 현재 시간 저장
        )

        # 2. 저장소를 통해 파일에 저장
        self.repo.save(new_transaction)
        return new_transaction

    def get_all_transaction(self):
        """
        전체 거래 내역을 가져옵니다.
        """
        return self.repo.load_all()

    def get_total_summary(self):
        """
        총 수입, 총 지출, 잔액을 계산합니다.
        """
        transaction = self.repo.load_all()
        income = sum(t.amount for t in transaction if t.type == "수입")
        expense = sum(t.amount for t in transaction if t.type == "지출")
        balance = income - expense

        return {
            "total_income" : income,
            "total_expense" : expense,
            "balance" : balance
        }