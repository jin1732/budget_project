import sys
from budget_app.cli import BudgetCLI

def main():
    # CLI 인스턴스 생성 및 실행
    # 서비스 생성 및 의존성 주입은 이제 BudgetCLI 내부의 setup_services가 담당합니다.
    cli = BudgetCLI()
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())
