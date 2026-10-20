# 가계부 콘솔 애플리케이션 (Budget App)
### 이 프로젝트는 파이썬을 활용하여 지출과 수입을 체계적으로 관리하는 CLI(Command Line Interface) 기반 가계부 앱입니다. 데이터의 영속성을 위해 파일 시스템을 활용하며, 객체 지향 프로그래밍과 데코레이터 등 파이썬의 핵심 개념을 적용하여 제작되었습니다.

---

>## 1. 실행 환경
- OS: macOS Sequoia 15.7.4
- Editor: VS Code
- Language: Python 3.10+
- Version Control: Git / GitHub

>## 2. 프로젝트 구조 및 데이터 설계
### ① 모듈화 설계
- 애플리케이션의 확장성을 위해 기능을 분리한 구조를 채택했습니다. 각 파일은 단일 책임 원칙(SRP)에 따라 독립적인 역할을 수행
- **models.py**: 데이터 구조 정의
- **repositories.py**: 데이터 저장 및 파일 입출력
- **services.py**: 비즈니스 로직 처리
- **cli.py**: 사용자 인터페이스(명령어 입력) 처리
- **decorators.py & utils.py**: 공통 유틸리티 및 부가 기능
```
budget_project/
├── budget_app/           # 소스 코드 메인 패키지
│   ├── __init__.py
│   ├── __main__.py       # 앱 실행 시작점
│   ├── models.py         # 데이터 모델 정의
│   ├── repositories.py   # 데이터 저장/읽기 로직
│   ├── services.py       # 핵심 비즈니스 로직
│   ├── cli.py            # 명령어 인터페이스 처리
│   └── decorators.py     # 공통 기능(예외 처리 등)
├── data/                 # 데이터 파일(JSONL) 저장 폴더
└── README.md             # 프로젝트 문서
```

### ② 데이터 모델 정의
- 가계부의 핵심 데이터인 '거래(Transaction)'를 정의했습니다. 파이썬의 dataclass를 활용하여 데이터 중심의 클래스를 효율적으로 설계

```python
# budget_app/models.py

@dataclass
class Transaction:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8]) # 고유 ID (8자리)
    date: str = ""          # 날짜 (YYYY-MM-DD)
    type: str = ""          # 수입(income) / 지출(expense)
    category: str = ""      # 카테고리
    amount: int = 0         # 금액
    memo: str = ""          # 메모
    tags: List[str] = field(default_factory=list) # 태그 리스트
```
### 학습한 주요 용어
-**@dataclass**: 클래스 생성 시 반복되는 __init__ 등의 메서드를 자동으로 생성해 주는 파이썬의 편리한 데코레이터입니다.
- **Type Hinting**: 변수나 함수의 반환값에 타입을 명시하여 코드의 안정성과 자동 완성 효율을 높이는 기법입니다.
- **CLI (Command Line Interface)**: 그래픽 화면이 아닌 터미널(검은 창)에서 명령어를 직접 입력하여 프로그램을 조작하는 방식입니다.
- **UUID**: 범용 고유 식별자로, 각 데이터에 중복되지 않는 고유한 키 값을 부여하기 위해 사용했습니다.


>## 3. 저장 방식 구현
### ① JSONL 파일 기반 저장소 설계
- 가계부 데이터는 프로그램이 종료되어도 유지되어야 하므로, 파일 기반 저장 방식을 사용했습니다.이 프로젝트에서는 JSONL(JSON Lines) 형식을 채택했습니다.
**JSON**: 파일 전체가 하나의 큰 JSON 배열로 저장됨
**JSONL**: 한 줄에 JSON 객체 하나씩 저장됨
- JSONL 방식은 데이터 추가 시 파일 끝에 한 줄만 덧붙이면 되어 효율적이고 한 줄 단위로 읽을 수 있어 구조가 단순하고 데이터가 많아져도 관리와 확장이 쉽습니다.

### ② 저장소 모듈 설계
- 데이터 저장과 읽기 기능은 repositories.py에서 담당하도록 분리했습니다.이렇게 하면 저장 방식이 바뀌더라도 서비스 로직은 그대로 유지할 수 있습니다.
**save()**: 거래 내역 1건을 파일에 저장
**load_all()**: 파일에 저장된 모든 거래 내역을 불러오기

``` python
# budget_app/repositories.py

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
                    transactions.append(Transaction(**data))
        return transactions
```

### 학습한 주요 용어
-**JSONL**: 한 줄에 JSON 객체 하나씩 저장하는 파일 형식입니다.
- **asdict()**: dataclass 객체를 딕셔너리로 바꿔 주는 함수입니다.
- **Append 모드('a')**: 파일의 기존 내용을 지우지 않고 뒤에 내용을 추가하는 방식입니다.
- **역직렬화**: 파일에 저장된 데이터를 다시 파이썬 객체로 복원하는 과정입니다.
- **os.makedirs()**: 폴더가 없으면 자동으로 만들어 주는 함수입니다.

>## 4. 서비스 로직 구현 
### ① 비즈니스 로직 설계
- services.py는 저장소(repositories.py)를 기반으로 실제 가계부 기능의 핵심 로직을 처리하는 계층입니다.
- 파일에 저장하거나 읽는 일은 Repository가 맡고, Service는 그 데이터를 활용해 추가, 조회, 요약 계산 같은 기능을 담당합니다. 이렇게 역할을 분리하면 코드가 더 깔끔해지고, 나중에 저장 방식을 바꾸더라도 서비스 로직은 그대로 유지할 수 있습니다.

### ② 서비스 모듈 역할
- BudgetService는 다음과 같은 기능을 담당합니다.
* 거래 내역 추가/
* 전체 거래 내역 조회
* 수입/지출 합계 계산
* 잔액 계산 
- **add_transaction()** : 새로운 거래 내역을 받아서 저장소에 저장합니다.실제로 데이터를 파일에 기록하는 역할은 TransactionRepository.save()가 수행합니다.
- **get_all_transactions()** : 저장된 모든 거래 내역을 불러와 리스트로 반환합니다.
- **get_total_summary()** : 모든 거래를 다시 읽어와서, income이면 수입 합계에 더하고 expense이면 지출 합계에 더한 뒤 최종적으로 수입, 지출, 잔액을 계산해 반환합니다.

```python
# budget_app/services.py

from typing import List, Dict
from .models import Transaction
from .repositories import TransactionRepository


class BudgetService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, transaction: Transaction):
        """거래 내역을 저장소에 추가합니다."""
        self.repository.save(transaction)

    def get_all_transactions(self) -> List[Transaction]:
        """저장된 모든 거래 내역을 반환합니다."""
        return self.repository.load_all()

    def get_total_summary(self) -> Dict[str, int]:
        """수입, 지출, 잔액을 계산해 반환합니다."""
        transactions = self.repository.load_all()

        income = 0
        expense = 0

        for t in transactions:
            if t.type == "income":
                income += t.amount
            elif t.type == "expense":
                expense += t.amount

        balance = income - expense

        return {
            "income": income,
            "expense": expense,
            "balance": balance
        }
```
### 학습한 주요 용어
-**Service Layer**: 프로그램의 핵심 비즈니스 로직을 담당하는 계층입니다.
- **Repository**: 데이터 저장과 조회를 담당하는 계층입니다.
- **의존성 주입**: 파일의 기존 내용을 지우지 않고 뒤에 내용을 추가하는 방식입니다.
- **역직렬화**: 클래스를 만들 때 필요한 객체를 외부에서 전달받는 방식입니다.
- **합계 계산**: 저장된 데이터를 바탕으로 의미 있는 결과를 만들어내는 과정입니다.