from budget_app.cli import BudgetCLI


def main():
    cli = BudgetCLI("transactions.jsonl")
    cli.run()


if __name__ == "__main__":
    main()