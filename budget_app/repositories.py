import json
import os
from dataclasses import asdict
from typing import List
from .models import Transaction

class TransactionRepository:
    def __init__(self, file_path: str):
        self.file_path = file_path
        # 데이터 폴더가 없으면 생성
        directory = os.path.dirname(self.file_path)

        if directory:
            os.makedirs(directory, exist_ok=True)

    def save(self, transaction: Transaction):
        """거래 내역 하나를 파일 끝에 추가 저장합니다."""
        # dataclass 객체를 딕셔너리로 변환 후 JSON 문자열로 변환
        with open(self.file_path, 'a', encoding='utf-8') as f:
            json_str = json.dumps(asdict(transaction), ensure_ascii=False)
            f.write(json_str + '\n')

    def iter_transactions(self):
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    yield Transaction(**data)

    def load_all(self) -> List[Transaction]:
        return list(self.iter_transactions())