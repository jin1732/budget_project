from dataclasses import dataclass, field
from typing import List, Optional
import uuid

@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8]) # 고유 ID (8자리)
    date: str = ""          # 날짜 (YYYY-MM-DD)
    type: str = ""          # 수입(income) / 지출(expense)
    category: str = ""      # 카테고리
    amount: int = 0         # 금액
    memo: str = ""          # 메모
    tags: List[str] = field(default_factory=list) # 태그 리스트

@dataclass
class Category:
    name: str
    type: str  # income 또는 expense

@dataclass
class Budget:
    month: str  # YYYY-MM
    amount: int