import json
import os
from dataclasses import asdict
from typing import List
from .models import Transaction

class TransactionRepository:
    def __init__(self, file_path: str):
        self.file_path = file_path
        # 데이터 폴더가 없으면 생성
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def save(self, transaction: Transaction):
        """거래 내역 하나를 파일 끝에 추가 저장합니다."""
        # dataclass 객체를 딕셔너리로 변환 후 JSON 문자열로 변환
        with open(self.file_path, 'a', encoding='utf-8') as f:
            json_str = json.dumps(asdict(transaction), ensure_ascii=False)
            f.write(json_str + '\n')

    def load_all(self) -> List[Transaction]:
        """파일에서 모든 거래 내역을 읽어와 객체 리스트로 반환합니다."""
        if not os.path.exists(self.file_path):
            return []

        transactions = []
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    # 딕셔너리 데이터를 Transaction 객체로 변환
                    transactions.append(Transaction(**data))
        return transactions