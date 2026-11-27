# 가계부 콘솔 애플리케이션 (Budget App)
### 이 프로젝트는 파이썬을 활용하여 지출과 수입을 체계적으로 관리하는 CLI(Command Line Interface) 기반 가계부 앱입니다. 데이터의 영속성을 위해 파일 시스템을 활용하며, 객체 지향 프로그래밍과 데코레이터 등 파이썬의 핵심 개념을 적용하여 제작되었습니다.

---

<br><br>

>## 1. 실행 환경
- OS: macOS Sequoia 15.7.4
- Editor: VS Code
- Language: Python 3.10+
- Version Control: Git / GitHub

<br><br>

>## 2. 프로젝트 구조 및 데이터 설계
### ① 모듈화 설계
- 애플리케이션의 확장성을 위해 기능을 분리한 구조를 채택했습니다. 각 파일은 단일 책임 원칙(SRP)에 따라 독립적인 역할을 수행
- **models.py**: 데이터 구조 정의
- **repositories.py**: 데이터 저장 및 파일 입출력
- **services.py**: 비즈니스 로직 처리
- **cli.py**: 사용자 인터페이스(명령어 입력) 처리
- **validators.py**: 입력값 검증
- **decorators.py & utils.py**: 공통 유틸리티 및 부가 기능
```
budget_project/
├── budget_app/           # 소스 코드 메인 패키지
│   ├── __init__.py
│   ├── __main__.py       # 앱 실행 시작점
│   ├── cli.py            # 사용자와 상호작용, 메뉴 출력, 입력 받기
│   ├── decorators.py     # 공통 예외 처리 데코레이터
│   ├── models.py         # 데이터 모델 정의
│   ├── repositories.py   # 파일에 데이터 저장 및 조회
│   ├── services.py       # 실제 업무 기능 처리
│   └── validators.py     # 입력값 검증
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
- **@dataclass**: 클래스 생성 시 반복되는 __init__ 등의 메서드를 자동으로 생성해 주는 파이썬의 편리한 데코레이터입니다.
- **Type Hinting**: 변수나 함수의 반환값에 타입을 명시하여 코드의 안정성과 자동 완성 효율을 높이는 기법입니다.
- **CLI (Command Line Interface)**: 그래픽 화면이 아닌 터미널(검은 창)에서 명령어를 직접 입력하여 프로그램을 조작하는 방식입니다.
- **UUID**: 범용 고유 식별자로, 각 데이터에 중복되지 않는 고유한 키 값을 부여하기 위해 사용했습니다.

<br><br>

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
- **JSONL**: 한 줄에 JSON 객체 하나씩 저장하는 파일 형식입니다.
- **asdict()**: dataclass 객체를 딕셔너리로 바꿔 주는 함수입니다.
- **Append 모드('a')**: 파일의 기존 내용을 지우지 않고 뒤에 내용을 추가하는 방식입니다.
- **역직렬화**: 파일에 저장된 데이터를 다시 파이썬 객체로 복원하는 과정입니다.
- **os.makedirs()**: 폴더가 없으면 자동으로 만들어 주는 함수입니다.

<br><br>

>## 4. 서비스 로직 구현 
### ① 비즈니스 로직 설계
- services.py는 저장소(repositories.py)를 기반으로 실제 가계부 기능의 핵심 로직을 처리하는 계층입니다.
- 파일에 저장하거나 읽는 일은 Repository가 맡고, Service는 그 데이터를 활용해 추가, 조회, 요약 계산 같은 기능을 담당합니다. 이렇게 역할을 분리하면 코드가 더 깔끔해지고, 나중에 저장 방식을 바꾸더라도 서비스 로직은 그대로 유지할 수 있습니다.

### ② 서비스 모듈 역할
- BudgetService는 다음과 같은 기능을 담당합니다.<br>
거래 내역 추가<br>
전체 거래 내역 조회<br>
수입/지출 합계 계산<br>
잔액 계산<br>
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
- **Service Layer**: 프로그램의 핵심 비즈니스 로직을 담당하는 계층입니다.
- **Repository**: 데이터 저장과 조회를 담당하는 계층입니다.
- **의존성 주입**:  필요한 객체를 클래스 내부에서 직접 만들지 않고, 외부에서 전달받는 방식입니다.
(예: service = BudgetService(repository))
- **역직렬화**: JSON 같은 저장된 데이터를 다시 객체로 바꾸는 과정입니다.(예: JSON 문자열 → Transaction 객체)
- **합계 계산**: 저장된 데이터를 바탕으로 의미 있는 결과를 만들어내는 과정입니다.

<br><br>

>## 5. CLI 인터페이스 구현
### ① 사용자 입력 흐름 설계
- 사용자가 터미널에서 메뉴를 선택하면 원하는 기능을 실행할 수 있도록 CLI 구조를 설계했습니다.
- 메뉴는 거래 추가, 전체 거래 조회, 수입/지출 요약, 종료 기능으로 구성했습니다.
- 사용자의 입력을 받아 Service 계층에 전달하고, 처리 결과를 다시 화면에 출력하도록 구현했습니다.

### ② CLI 모듈 역할
- BudgetCLI 클래스는 사용자와 프로그램이 상호작용하는 진입점 역할을 합니다.
- 내부에서 TransactionRepository와 BudgetService를 생성해 가계부 기능을 연결합니다.
- 주요 기능은 다음과 같습니다.<br>
메뉴 출력<br>
거래 추가 입력 받기<br>
전체 거래 내역 출력<br>
수입/지출 요약 출력<br>
프로그램 반복 실행 및 종료 처리<br>

``` python

class BudgetCLI:

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
```

### 학습한 주요 용어
- **show_menu()**: 사용자에게 선택 가능한 메뉴를 출력합니다.
- **add_transaction()**: 거래 유형, 카테고리, 금액, 메모, 태그를 입력받아 Transaction 객체를 만들고 저장합니다.
- **show_all_transactions()**: 저장된 거래 내역 전체를 조회하여 화면에 출력합니다.
- **show_summary()**: 전체 거래를 바탕으로 계산된 수입, 지출, 잔액을 출력합니다.
- **run()**: 프로그램이 종료될 때까지 메뉴를 반복 실행합니다.

<br><br>

>## 6. 입력 검증 및 예외 처리
### ① 검증 로직 분리
- 사용자 입력값 검증 책임을 validators.py로 분리한다.
- CLI에서 직접 모든 검사를 하지 않고, 검증 함수에 맡긴다.
- 재사용 가능한 검증 함수 예: validate_amount(), validate_transaction_type()

### ② 예외 발생과 처리 분리
- 검증 함수에서는 잘못된 입력을 발견하면 raise ValueError(...)로 예외를 발생시킨다.
- CLI에서는 try-except로 예외를 받아 사용자에게 안내 메시지를 출력한다.
- 이렇게 하면: 검증 로직은 단순해지고 사용자 인터페이스는 친절한 메시지를 제공할 수 있다.

```python

def validate_amount(value: str) -> int:
    amount = int(value)
    if amount <= 0:
        raise ValueError("금액은 0보다 커야 합니다.")
    return amount

```
```python

try:
    amount = validate_amount(input("금액: "))
except ValueError as e:
    print(f"입력 오류: {e}")

```

<br><br>


>## 7. CSV 내보내기 구현
### ① CSV 내보내기 기능 추가
- 저장된 거래 데이터를 다른 프로그램에서도 쉽게 활용할 수 있도록 CSV 내보내기 기능을 추가했다.  
- 이 기능을 통해 사용자는 가계부 데이터를 엑셀 같은 스프레드시트 프로그램에서 확인할 수 있다.
- 프로그램은 저장된 거래 목록을 읽어 와서 CSV 파일로 변환하고, 지정한 경로에 파일을 생성한다.

### ② 파일 생성 및 형식 맞추기
- CSV 파일은 파이썬의 `csv` 모듈을 사용해 생성했다.  
- 엑셀에서 한글이 깨지지 않도록 `UTF-8-sig` 인코딩을 사용했다.
- 또한 과제에서 요구하는 형식에 맞추기 위해 다음 사항을 반영했다.
컬럼 순서를 일관되게 유지<br>
날짜 형식을 `YYYY-MM-DD`로 통일<br>
거래 1건당 CSV 1행으로 저장<br>
헤더(row)를 포함해 파일 생성<br>

``` python
import csv
from pathlib import Path

def export_transactions_to_csv(self, filename=None):
        transactions = list(self.repository.get_all())

        if filename is None:
            file_path = Path(__file__).resolve().parent.parent / "data" / "transactions.csv"
        else:
            file_path = Path(filename)

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)

            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])

            for t in transactions:
                writer.writerow([
                    str(t.date),
                    t.type,
                    t.category,
                    t.amount,
                    t.memo if t.memo else "",
                    ",".join(t.tags) if t.tags else ""
                ])

        return file_path

```

### 학습한 주요 용어
- **CSV (Comma-Separated Values)**: 쉼표로 값을 구분하는 텍스트 기반 데이터 파일 형식
- **encoding**: 문자를 컴퓨터가 저장하고 읽는 방식
- **UTF-8-sig**: 엑셀에서 한글 CSV가 잘 열리도록 도와주는 인코딩 방식
- **header**: CSV 파일의 첫 줄에 들어가는 컬럼 이름

<br><br>

>## 8. CSV 가져오기 구현
### ① CSV 가져오기 기능 추가
- 가계부 데이터를 백업한 CSV 파일을 다시 프로그램으로 불러올 수 있도록 가져오기 기능을 구현했습니다.
- 이를 통해 사용자는 기존 데이터를 재사용하거나, 다른 환경으로 쉽게 옮길 수 있습니다.
- CSV 가져오기 기능은 `export` 기능과 반대로 동작하며, 파일에 저장된 각 행(row)을 하나의 거래(Transaction) 데이터로 변환하여 저장합니다.


### ② 파일 읽기 및 데이터 변환
- CSV 파일은 `csv.DictReader`를 이용해 한 줄씩 딕셔너리 형태로 읽었습니다.
- 각 행에서 날짜, 거래 유형, 카테고리, 금액, 메모 등의 값을 꺼내어 `Transaction` 객체로 변환한 뒤 저장소에 전달했습니다.
- 이 과정에서 문자열로 저장된 금액은 정수형으로 변환하고, 필요한 경우 입력값 검증 로직을 거쳐 데이터의 일관성을 유지했습니다.

```python
import csv
from .models import Transaction

def import_transactions_from_csv(file_path, repo):
    count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            transaction = Transaction(
                date=row["date"],
                type=row["type"],
                category=row["category"],
                amount=int(row["amount"]),
                memo=row.get("memo", ""),
                tags=row.get("tags", "").split(",") if row.get("tags") else []
            )
            repo.save(transaction)
            count += 1

    return count
```
### 학습한 주요 용어
- **csv.DictReader**: CSV 파일의 각 행을 딕셔너리 형태로 읽어 주는 기능입니다.
- **파싱(Parsing)**: 문자열 형태의 데이터를 프로그램이 사용할 수 있는 구조로 해석하는 과정입니다.
- **데이터 변환**: 문자열 데이터를 정수, 리스트, 객체 등 원하는 형태로 바꾸는 작업입니다.
- **파일 입출력(I/O)**: 파일을 읽거나 쓰는 작업을 의미합니다.

<br><br>

>## 9. 부가 기능 구현
### ① 거래 수정 및 삭제 기능 추가
- 단순히 거래를 저장하는 것에서 끝나지 않고, 잘못 입력한 내역을 수정하거나 필요 없는 데이터를 삭제할 수 있도록 기능을 확장했습니다.
- 거래 수정은 **안 A(옵션 기반)로 고정**합니다: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`
- 거래 삭제는 `delete --id <id>`로 실행합니다.
- 존재하지 않는 ID는 수정/삭제 대상이 없다는 메시지로 처리합니다.
- 수정 및 삭제는 전체 JSONL을 임시 파일로 작성한 뒤 원자적으로 교체하여 저장합니다.

### ② 카테고리 및 예산 관리 기능 추가
- 거래 내역을 더 체계적으로 관리하기 위해 카테고리 관리 기능을 추가했습니다.
- 사용자는 새로운 카테고리를 등록하거나 목록을 확인하고, 필요 없는 카테고리를 제거할 수 있습니다.
- 또한 월별 예산을 설정하고 현재 지출과 비교할 수 있도록 예산 관리 기능도 구현했습니다.
- 이 기능을 통해 단순 기록을 넘어, 소비를 점검하고 계획적으로 관리할 수 있는 가계부로 확장했습니다.

```zsh

# 거래 수정
python -m budget_app update --id 거래ID --amount 15000 --memo "금액 수정"

# 거래 삭제
python -m budget_app delete --id 거래ID

# 카테고리 추가
python -m budget_app category add --name 식비

# 카테고리 목록 조회
python -m budget_app category list

# 예산 설정
python -m budget_app budget set --month 2025-08 --limit 500000

# 예산 확인
python -m budget_app budget check --month 2025-08
```

### 학습한 주요 용어
- **CRUD**: Create(생성), Read(조회), Update(수정), Delete(삭제)의 약자로 데이터 관리의 기본 기능입니다.
- **식별자(ID)**: 각 거래를 구분하기 위한 고유 값입니다.

<br><br>

>## 10. 프로젝트를 통해 배운 점
### ① 파이썬 프로젝트 구조화 경험
- 하나의 파일에 모든 기능을 작성하는 대신, 역할별로 모듈을 나누어 설계하면서 구조적인 프로그램 작성 방법을 익혔습니다.
- 특히 `Model - Repository - Service - CLI` 형태로 계층을 분리하면서 유지보수와 확장에 유리한 구조를 경험할 수 있었습니다.

### ② 파일 기반 데이터 처리와 검증의 중요성 이해
- JSONL 파일을 이용해 데이터를 저장하고 다시 불러오는 과정에서 직렬화와 역직렬화의 개념을 실제로 적용해 볼 수 있었습니다.
- 또한 입력값 검증과 예외 처리를 분리하면서, 안정적인 프로그램을 만들기 위해 방어적인 코드가 왜 중요한지 배울 수 있었습니다.

<br><br>

>## 11. 데이터 흐름 예시(지출 등록)

**1. 사용자 → cli.py**
- 사용자가 메뉴에서 지출 등록을 선택하고 금액 10,000원, 항목 식비를 입력합니다.
**2. cli.py → services.py**
- add_expense(10000, "식비")를 호출합니다.
**3. services.py → validators.py**
- 금액이 숫자인지, 0보다 큰지 검사합니다.
**4. services.py → models.py**
- 검사된 정보를 이용해 거래 객체를 생성합니다
**5. services.py → repositories.py**
- 생성된 거래 객체를 저장해 달라고 요청합니다.
**6. repositories.py → budget.json**
- 실제 파일에 거래 데이터를 기록합니다.
**7. services.py → cli.py → 사용자n**
- 저장 결과를 전달하고 사용자에게 등록 완료 메시지를 출력합니다.

<br><br>

>## 12. 사용 예시 (Usage)

#### help

```zsh
son1732321732@c4r2s8 budget_project % python3 -m budget_app --help
usage: budget-app [-h] [--data-dir DATA_DIR]
                  {add,list,summary,export,import,category,budget,search,update,delete}
                  ...

콘솔 가계부 앱

positional arguments:
  {add,list,summary,export,import,category,budget,search,update,delete}
    add                 거래 추가
    list                거래 목록 조회
    summary             월별 요약
    export              CSV 내보내기
    import              CSV 가져오기
    category            카테고리 관리
    budget              예산 관리
    search              거래 검색
    update              거래 수정
    delete              거래 삭제

options:
  -h, --help            show this help message and exit
  --data-dir DATA_DIR   데이터 저장 폴더 경로
```

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app add --help
usage: budget-app add [-h] [--date DATE] [--type {income,expense}] [--category CATEGORY] [--amount AMOUNT] [--memo MEMO] [--tags TAGS]

인자를 생략하면 대화형으로 입력을 받습니다. 모든 필드는 대화형 입력이 기본입니다.

options:
  -h, --help            show this help message and exit
  --date DATE           날짜 YYYY-MM-DD
  --type {income,expense}
                        거래 유형 income 또는 expense
  --category CATEGORY   카테고리
  --amount AMOUNT       금액
  --memo MEMO           메모
  --tags TAGS           태그 목록 (쉼표 구분)

# help 테스트 완료
python3 -m budget_app list --help
python3 -m budget_app search --help
python3 -m budget_app summary --help
python3 -m budget_app budget --help 
python3 -m budget_app category --help
python3 -m budget_app update --help
python3 -m budget_app delete --help
python3 -m budget_app import --help
python3 -m budget_app export --help
```

<dr>

#### add

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app add --date 2026-11-05 --type income --category 월급 --amount 3000000 --memo "11월 급여" --tags "야근수당,연금"           

✅ 거래가 성공적으로 저장되었습니다!
🆔 생성된 거래 ID: 85b6eb2d

son1732321732@c4r3s8 budget_project % python3 -m budget_app add --date 2023-11-15 --type expense --category 식비 --amount 20000 --memo "점심" --tags "카드,2인,돈까스"

✅ 거래가 성공적으로 저장되었습니다!
🆔 생성된 거래 ID: 0f477104
```

**대화형으로도 동작**
```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app add

📢 새로운 거래 입력을 시작합니다. (미입력 항목은 대화형으로 진행)
- 날짜 (YYYY-MM-DD, 엔터 시 오늘): 
- 유형 (income/expense): expense
📍 사용 가능한 카테고리: 식비, 교통, 취미, 생필품
- 카테고리 선택: 식사
❌ '식사'은(는) 목록에 없습니다. 다시 입력해주세요.
📍 사용 가능한 카테고리: 식비, 교통, 취미, 생필품
- 카테고리 선택: 식비
- 금액: 30000
- 메모 (선택): 점심  
- 태그 (쉼표로 구분, 선택): 친구,2인,잠실

✅ 거래가 성공적으로 저장되었습니다!
🆔 생성된 거래 ID: 3e8c4dd2
```

<dr>

#### list
- 최신순 출력
- 거래 목록과 검색 결과는 동일한 형식으로 출력합니다.
- 태그가 없는 경우 `-`, 태그가 있는 경우 쉼표로 구분된 `태그: ...` 형식을 사용합니다.

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app list
[3e8c4dd2] 2026-11-16 | expense | 커피 | 3,000원 | 메모: 블랙커피 | 태그: 구
[0f477104] 2023-11-15 | expense | 식비 | 20,000원 | 메모: 점심 | 태그: 카드, 2인, 돈까스
[85b6eb2d] 2026-11-05 | income | 월급 | 3,000,000원 | 메모: 11월 급여 | 태그: 야근수당, 연금
[c413f807] 2026-11-16 | income | 월급 | 2,000,000원 | 메모: 월 | 태그: 특근
[fb858a7c] 2026-07-05 | expense | 식비 | 3,000원 | 메모: 블랙 | 태그: 아이스, 달콩
[ba649a63] 2026-11-12 | expense | 식비 | 30,000원 | 메모: 인,카레 | 태그: 점심, 카레
[f0b1d750] 2023-11-04 | income | 월급 | 3,000,000원 | 메모: 11월 정기급여 | 태그: -
[db9ee7e5] 2023-11-03 | expense | 취미 | 50,000원 | 메모: 영화관람 | 태그: -
[cf7aee05] 2023-11-02 | expense | 교통 | 1,500원 | 메모: 버스비 | 태그: -
[a6ffd763] 2023-11-01 | expense | 식비 | 10,000원 | 메모: 점심식사 | 태그: -

son1732321732@c4r3s8 budget_project % python3 -m budget_app list --limit 3
[3e8c4dd2] 2026-11-16 | expense | 커피 | 3,000원 | 메모: 블랙커피 | 태그: 구
[0f477104] 2023-11-15 | expense | 식비 | 20,000원 | 메모: 점심 | 태그: 카드, 2인, 돈까스
[85b6eb2d] 2026-11-05 | income | 월급 | 3,000,000원 | 메모: 11월 급여 | 태그: 야근수당, 연금

son1732321732@c4r3s8 budget_project % python3 -m budget_app list --type income
[85b6eb2d] 2026-11-05 | income | 월급 | 3,000,000원 | 메모: 11월 급여 | 태그: 야근수당, 연금
[c413f807] 2026-11-16 | income | 월급 | 2,000,000원 | 메모: 월 | 태그: 특근
[f0b1d750] 2023-11-04 | income | 월급 | 3,000,000원 | 메모: 11월 정기급여 | 태그: -
[c26fcb4a] 2026-07-01 | income | 월급 | 4,000,000원 | 메모: 7월 급여 | 태그: 야근수당, 건강보험, 연금

son1732321732@c4r3s8 budget_project % python3 -m budget_app list --type expense
[3e8c4dd2] 2026-11-16 | expense | 커피 | 3,000원 | 메모: 블랙커피 | 태그: 구
[0f477104] 2023-11-15 | expense | 식비 | 20,000원 | 메모: 점심 | 태그: 카드, 2인, 돈까스
[fb858a7c] 2026-07-05 | expense | 식비 | 3,000원 | 메모: 블랙 | 태그: 아이스, 달콩
[ba649a63] 2026-11-12 | expense | 식비 | 30,000원 | 메모: 인,카레 | 태그: 점심, 카레
[db9ee7e5] 2023-11-03 | expense | 취미 | 50,000원 | 메모: 영화관람 | 태그: -
[cf7aee05] 2023-11-02 | expense | 교통 | 1,500원 | 메모: 버스비 | 태그: -
[a6ffd763] 2023-11-01 | expense | 식비 | 10,000원 | 메모: 점심식사 | 태그: -
[3560bbb3] 2026-07-02 | expense | 교통 | 2,500원 | 메모: 버스 | 태그: 버스, 영업, 목동
[5358e428] 2026-07-02 | expense | 식비 | 30,000원 | 메모: 점심식사 | 태그: 카드, 2인, 한식
```
<dr>

### 제너레이터 기반 스트리밍 완료 체크리스트

#### 1) get_list()가 리스트가 아니라 제너레이터를 반환하는가'

```zsh
services.py

def get_list(self, limit: int):
    self.validate_limit(limit)
    yield from islice(self.repository.iter_transactions_reverse(), limit)
```
- return [...]처럼 리스트를 만들어 반환하지 않고, **yield** from으로 데이터를 순차적으로 전달한다.
- islice(...)를 사용해 필요한 개수(limit)만큼만 가져온다.
- iter_transactions_reverse() : 최신순으로 하나씩 전달해 달라고 요청
- list 명령은 조회 시점에 필요한 데이터만 소비하며, 전체 거래 내역을 한 번에 메모리에 올리지 않는다.

#### 2) repository.iter_transactions_reverse()가 yield로 하나씩 반환하는가
```zsh
repositories.py

def iter_transactions_reverse(self) -> Generator[Transaction, None, None]:
    for line in self._read_lines_reverse():
        data = json.loads(line)
        yield Transaction(**data)
```
- list(...)로 전체 데이터를 한 번에 모으지 않고, 파일의 각 줄을 뒤에서부터 한 줄씩 읽는다.
- 읽은 줄은 즉시 json.loads()로 파싱한 뒤 Transaction 객체로 변환하여 바로 yield한다.
- 파일 전체를 먼저 로드한 뒤 가공하는 방식이 아니라, 필요한 순간에 한 건씩 생성해서 전달하는 스트리밍 방식이다.

#### 3) list가 파일 전체를 한 번에 로드하지 않도록 어떻게 구현했는가
**Repository 계층** <dr>
- iter_transactions_reverse()가 거래 내역 전체를 리스트로 만들지 않고,_read_lines_reverse()를 통해 파일 내용을 역순으로 한 줄씩 읽어 바로 yield한다.

**Service 계층** <dr>
- get_list()가 Repository의 제너레이터를 그대로 받아 islice(...)로 사용자가 요청한 개수만 잘라서 전달한다.

#### 4) 스트리밍 방식으로 바꾸면서 제거한 방식 / 문구
**제거한 방식** <dr>
- load_transactions()처럼 전체 거래 내역을 먼저 불러오는 방식
- return [...]처럼 리스트를 만들어 반환하는 방식
- list(...)로 제너레이터를 즉시 모두 소비하는 방식

<dr>

#### search 

- 검색 결과도 `list`와 동일한 거래 목록 형식으로 출력합니다.
- 태그가 없는 경우 `-`, 태그가 있는 경우 쉼표로 구분된 `태그: ...` 형식을 사용합니다.

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app search --from 2026-01-01 --to 2026-11-30

[검색 결과] (조건: 기간=2026-01-01~2026-11-30)

--------------------------------------------------------------------------------
[3e8c4dd2] 2026-11-16 | expense | 커피 | 3,000원 | 메모: 블랙커피 | 태그: 구
[85b6eb2d] 2026-11-05 | income | 월급 | 3,000,000원 | 메모: 11월 급여 | 태그: 야근수당, 연금
[c413f807] 2026-11-16 | income | 월급 | 2,000,000원 | 메모: 월 | 태그: 특근
[fb858a7c] 2026-07-05 | expense | 식비 | 3,000원 | 메모: 블랙 | 태그: 아이스, 달콩
[ba649a63] 2026-11-12 | expense | 식비 | 30,000원 | 메모: 인,카레 | 태그: 점심, 카레
[3560bbb3] 2026-07-02 | expense | 교통 | 2,500원 | 메모: 버스 | 태그: 버스, 영업, 목동
[5358e428] 2026-07-02 | expense | 식비 | 30,000원 | 메모: 점심식사 | 태그: 카드, 2인, 한식
[c26fcb4a] 2026-07-01 | income | 월급 | 4,000,000원 | 메모: 7월 급여 | 태그: 야근수당, 건강보험, 연금

son1732321732@c4r3s8 budget_project % python3 -m budget_app search --from 2026-01-01 --to 2026-11-31
[입력 오류] 날짜 형식은 YYYY-MM-DD 이어야 합니다.

son1732321732@c4r3s8 budget_project % python3 -m budget_app search --category 식비

[검색 결과] (조건: 카테고리=식비)

--------------------------------------------------------------------------------
[0f477104] 2023-11-15 | expense | 식비 | 20,000원 | 메모: 점심 | 태그: 카드, 2인, 돈까스
[fb858a7c] 2026-07-05 | expense | 식비 | 3,000원 | 메모: 블랙 | 태그: 아이스, 달콩
[ba649a63] 2026-11-12 | expense | 식비 | 30,000원 | 메모: 인,카레 | 태그: 점심, 카레
[a6ffd763] 2023-11-01 | expense | 식비 | 10,000원 | 메모: 점심식사 | 태그: -
[5358e428] 2026-07-02 | expense | 식비 | 30,000원 | 메모: 점심식사 | 태그: 카드, 2인, 한식

son1732321732@c4r3s8 budget_project % python3 -m budget_app search --type expense
[3e8c4dd2] 2026-11-16 | expense | 커피 | 3,000원 | 메모: 블랙커피 | 태그: 구
[0f477104] 2023-11-15 | expense | 식비 | 20,000원 | 메모: 점심 | 태그: 카드, 2인, 돈까스
[fb858a7c] 2026-07-05 | expense | 식비 | 3,000원 | 메모: 블랙 | 태그: 아이스, 달콩
[ba649a63] 2026-11-12 | expense | 식비 | 30,000원 | 메모: 인,카레 | 태그: 점심, 카레
[db9ee7e5] 2023-11-03 | expense | 취미 | 50,000원 | 메모: 영화관람 | 태그: -
[cf7aee05] 2023-11-02 | expense | 교통 | 1,500원 | 메모: 버스비 | 태그: -
[a6ffd763] 2023-11-01 | expense | 식비 | 10,000원 | 메모: 점심식사 | 태그: -
[3560bbb3] 2026-07-02 | expense | 교통 | 2,500원 | 메모: 버스 | 태그: 버스, 영업, 목동
[5358e428] 2026-07-02 | expense | 식비 | 30,000원 | 메모: 점심식사 | 태그: 카드, 2인, 한식
```
<dr>

#### category

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app category add
카테고리 이름은 비워둘 수 없습니다.
카테고리 이름: 쇼핑
카테고리 유형은 income 또는 expense만 가능합니다.
카테고리 유형 (income/expense): income
카테고리가 추가되었습니다.
이름: 쇼핑
유형: income

son1732321732@c4r3s8 budget_project % python3 -m budget_app category add 식비 --type expense
이미 존재하는 카테고리입니다: 식비 (expense)

son1732321732@c4r3s8 budget_project % python3 -m budget_app category add 여행 --type expense
카테고리가 추가되었습니다.
이름: 여행
유형: expense

son1732321732@c4r3s8 budget_project % python3 -m budget_app category list
카테고리 목록
----------------------------------------
식비 | expense
월급 | income
교통 | expense
취미 | expense
의류 | expense
문화 | expense
간식 | expense
커피 | expense
용돈 | income
여행 | expense

son1732321732@c4r3s8 budget_project % python3 -m budget_app category list --type income
카테고리 목록
----------------------------------------
월급 | income
용돈 | income

son1732321732@c4r3s8 budget_project % python3 -m budget_app category remove --type expense 여행
카테고리가 삭제되었습니다.
이름: 여행
유형: expense

son1732321732@c4r3s8 budget_project % python3 -m budget_app category remove --type expense 커피
[입력 오류] 사용 중인 카테고리는 삭제할 수 없습니다. --replace-with 옵션을 사용하세요.

son1732321732@c4r3s8 budget_project % python3 -m budget_app category remove --type expense 커피 --replace-with 간식
카테고리가 삭제되었습니다.
이름: 커피
유형: expense
대체 카테고리: 간식
```

<dr>

#### summary

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app summary
알림: --month가 입력되지 않아 이번 달(2026-11) 요약을 조회합니다.

[2026-11 요약]
----------------------------------------
총 수입: 5,000,000원
총 지출: 33,000원
잔액: 4,967,000원
예산: 300,000원
사용률: 11.0%
상태: 정상

[지출 TOP 3]
1. 식비: 30,000원
2. 간식: 3,000원

son1732321732@c4r3s8 budget_project % python3 -m budget_app summary --month 2023-11
[2023-11 요약]
----------------------------------------
총 수입: 3,000,000원
총 지출: 81,500원
잔액: 2,918,500원

[지출 TOP 3]
1. 취미: 50,000원
2. 식비: 30,000원
3. 교통: 1,500원

son1732321732@c4r3s8 budget_project % python3 -m budget_app summary --month 2025-01
[2025-01]에 등록된 데이터가 없습니다.
```

<dr>

#### budget

- 예산 정책: 같은 월(`YYYY-MM`)의 예산이 이미 있으면 덮어쓰고, 없으면 새로 추가합니다.

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app budget set --month 2023-11 --amount 500000
새 예산을 추가했습니다.
예산이 설정되었습니다.
월: 2023-11
금액: 500,000원

son1732321732@c4r3s8 budget_project % python3 -m budget_app budget set --month 2023-11 --amount 500000
기존 예산을 덮어썼습니다.
예산이 설정되었습니다.
월: 2023-11
금액: 500,000원

son1732321732@c4r3s8 budget_project % python3 -m budget_app summary --month 2023-11
[2023-11 요약]
----------------------------------------
총 수입: 3,000,000원
총 지출: 81,500원
잔액: 2,918,500원
예산: 50,000원
사용률: 163.0%
경고: 예산을 초과했습니다.

[지출 TOP 3]
1. 취미: 50,000원
2. 식비: 30,000원
3. 교통: 1,500원
```

<dr>

#### update

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app update --id 3e8c4dd2 --amount 20000
거래가 수정되었습니다.
[3e8c4dd2] 2026-11-16 | expense | 간식 | 20,000원 | 메모: 블랙커피 | 태그: 구

son1732321732@c4r3s8 budget_project % python3 -m budget_app update --id 3e8c4dd2 --tags "구로,스벅"
거래가 수정되었습니다.
[3e8c4dd2] 2026-11-16 | expense | 간식 | 20,000원 | 메모: 블랙커피 | 태그: 구로, 스벅

son1732321732@c4r3s8 budget_project % python3 -m budget_app update 1254677
[입력 오류] 해당 ID의 거래를 찾을 수 없습니다.
```

<dr>

#### delete

```zsh
son1732321732@c4r2s8 budget_project % python3 -m budget_app delete --id c26fcb4a
다음 거래를 삭제합니다.
[c26fcb4a] 2026-07-01 | income | 월급 | 4,000,000원 | 메모: 7월 급여
거래가 삭제되었습니다.

son1732321732@c4r2s8 budget_project % python3 -m budget_app delete --id 56789489
[입력 오류] 해당 ID의 거래 데이터가 없습니다: 56789489
```

<dr>

#### import

```zsh
son1732321732@c4r2s8 budget_project % python3 -m budget_app import --from tool_data.csv
[파일 오류] 파일을 찾을 수 없습니다: tool_data.csv

son1732321732@c4r3s8 budget_project % python3 -m budget_app import --from test_data.csv
가져오기 완료: 성공 4건 (반영 위치: data/transactions.jsonl)

son1732321732@c4r3s8 budget_project % python3 -m budget_app list
[011f739c] 2023-11-04 | income | 월급 | 3,000,000원 | 메모: 11월 정기급여 | 태그: -
[414b94ff] 2023-11-03 | expense | 취미 | 50,000원 | 메모: 영화관람 | 태그: -
[1784db2c] 2023-11-02 | expense | 교통 | 1,500원 | 메모: 버스비 | 태그: -
[91c5f0cb] 2023-11-01 | expense | 식비 | 10,000원 | 메모: 점심식사 | 태그: -
```

#### CSV 스키마 표준

이 프로젝트는 다음 CSV 스키마를 기준으로 import/export를 처리합니다.

| 컬럼 | 필수 | 설명 |
| --- | --- | --- |
| date | Y | 거래일자, `YYYY-MM-DD` 형식 |
| type | Y | 거래 유형, `income` 또는 `expense` |
| category | Y | 등록된 카테고리 이름 |
| amount | Y | 양수 정수 금액 |
| memo | N | 메모 문자열 |
| tags | N | 태그 목록, 쉼표(`,`)로 구분 |

```python
import csv

from .models import Transaction


def import_transactions_from_csv(file_path, repo):
    count = 0

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            transaction = Transaction(
                date=row["date"],
                type=row["type"],
                category=row["category"],
                amount=int(row["amount"]),
                memo=row.get("memo", ""),
                tags=row.get("tags", "").split(",") if row.get("tags") else [],
            )
            repo.save(transaction)
            count += 1

    return count
```

- CSV 파일은 UTF-8 또는 UTF-8-sig 인코딩을 사용합니다.
- 첫 번째 행은 헤더로 처리되며 데이터가 아닙니다.
- 가져온 거래는 새 8자리 ID를 부여받아 저장됩니다.

<dr>

#### export

```zsh
son1732321732@c4r3s8 budget_project % python3 -m budget_app export --out transactions.csv --month 2026-11
CSV 파일로 내보냈습니다: transactions.csv (총 5건)

son1732321732@c4r2s8 budget_project % echo $?
0

son1732321732@c4r3s8 budget_project % python3 -m budget_app export --out transactions.csv --from 2023-11-01 --to 2023-11-30
CSV 파일로 내보냈습니다: transactions.csv (총 28건)

son1732321732@c4r3s8 budget_project % python3 -m budget_app export --out transactions.csv
오류: export 시 --month 또는 --from과 --to를 모두 입력해야 합니다.

son1732321732@c4r3s8 budget_project % python3 -m budget_app export --month 2026-11
오류: export 시 --out 경로는 필수입니다.
```

CSV 내보내기는 저장된 거래를 다음 6개 컬럼으로 작성합니다.

```csv
date,type,category,amount,memo,tags
2026-11-05,income,월급,3000000,11월 급여,"야근수당,연금"
2026-11-16,expense,간식,3000,블랙커피,구
```

<br><br>

>## 13. 파일 기반 update/delete의 안전한 처리
### 임시 파일을 이용한 원자적 저장
- 거래 수정과 삭제는 원본 JSONL 파일을 직접 열어 덮어쓰지 않고, 전체 거래 목록을 새로 작성한 임시 파일로 저장한 뒤 원본 파일과 교체합니다.
- 임시 파일은 `tempfile.NamedTemporaryFile()`로 생성하며, 원본과 같은 폴더(`dir=self.file_path.parent`)에 만들었습니다.
- 임시 파일과 원본이 같은 파일 시스템에 있어야 `os.replace()`를 이용한 교체가 안전하게 수행됩니다.

```python
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    dir=self.file_path.parent,
    prefix=f".{self.file_path.name}.",
    suffix=".tmp",
    delete=False,
) as file:
    temp_path = Path(file.name)

    for transaction in transactions:
        file.write(json.dumps(asdict(transaction), ensure_ascii=False) + "\n")

    file.flush()
    os.fsync(file.fileno())

os.replace(temp_path, self.file_path)
```

### update/delete 처리 과정
1. 먼저 `get_all()`로 현재 거래 목록을 읽어 메모리에서 수정하거나 삭제 대상이 아닌 항목만 남깁니다.
2. 수정 대상의 ID가 존재하지 않으면 `save_all()`을 호출하지 않고 예외를 발생시켜 원본 파일을 변경하지 않습니다.
3. 삭제 대상의 ID가 존재하지 않으면 `False`를 반환하고 원본 파일을 변경하지 않습니다.
4. 변경할 내용이 확인되면 전체 목록을 임시 파일에 한 줄에 하나의 JSON 객체 형식으로 다시 씁니다.
5. `file.flush()`와 `os.fsync()`로 임시 파일의 버퍼와 디스크 쓰기를 반영합니다.
6. `os.replace()`로 임시 파일을 원본 JSONL 파일 경로에 교체하여 수정 또는 삭제를 완료합니다.

### 원자성 보장과 예외 처리
- `os.replace()`는 임시 파일과 원본을 같은 폴더에 만든 경우 동일한 파일 시스템에서 하나의 교체 작업으로 처리합니다.
- 따라서 원본 파일을 직접 잘라내고 다시 쓰는 동안 발생할 수 있는 중간 손상 상태를 줄일 수 있습니다.
- 교체가 성공하기 전에는 기존 원본 파일이 유지되며, 교체가 성공한 뒤에는 임시 파일의 전체 내용이 원본이 됩니다.
- 임시 파일 생성 또는 저장 과정에서 예외가 발생하면 `temp_path.unlink(missing_ok=True)`로 남은 임시 파일을 삭제하고 예외를 다시 전달합니다.
- 이 방식은 프로세스 비정상 종료 시 임시 파일이 남을 수는 있지만 원본 데이터가 임시 파일 교체 전에는 유지되도록 설계한 원자적 교체 방식입니다.

### 동시성에 대한 제한
- 이 구현은 파일 전체 교체를 통한 원자성을 보장하지만, 여러 프로세스가 동시에 읽기/쓰기를 수행할 때 발생하는 최종 덮어쓰기 경쟁을 막는 파일 잠금까지 제공하지는 않습니다.
- 즉, 개별 파일 교체 작업의 안전성은 높지만 다중 프로세스 동시 업데이트까지 완전히 제어하려면 추가적인 잠금(lock) 또는 직렬화 처리가 필요합니다.

