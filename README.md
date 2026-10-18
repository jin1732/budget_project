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
