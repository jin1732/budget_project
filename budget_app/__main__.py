import sys
from budget_app.cli import BudgetCLI


def main():
    cli = BudgetCLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
