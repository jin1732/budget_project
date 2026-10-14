from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Transaction:
    id: str
    date: str          # YYYY-MM-DD
    type: str          # income / expense
    category: str
    amount: int
    memo: str = ""
    tags: List[str] = field(default_factory=list)