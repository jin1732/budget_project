from dataclasses import dataclass, field, asdict
from typing import List
import uuid


@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    date: str = ""          # 날짜 YYYY-MM-DD
    type: str = ""          # income 또는 expense
    category: str = ""      # 카테고리
    amount: int = 0         # 금액
    memo: str = ""          # 메모
    tags: List[str] = field(default_factory=list)


@dataclass
class Category:
    name: str
    type: str  # income 또는 expense


@dataclass
class Budget:
    month: str      # YYYY-MM
    category: str
    amount: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Budget":
        return cls(
            month=data["month"],
            category=data["category"],
            amount=int(data["amount"]),
        )