import json
import os
import tempfile
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Iterator, Generator, List


from budget_app.models import Transaction, Category, Budget


class TransactionRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def get_all(self) -> List[Transaction]:
        """파일에서 데이터를 읽어 Transaction 객체 리스트로 반환합니다."""
        if not self.file_path.exists():
            return []
        
        transactions = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip() # 공백 제거
                if not line: # 빈 줄은 건너뜀
                    continue
                try:
                    data = json.loads(line)
                    # ID가 문자열로 저장되어 있을 경우를 대비해 숫자로 변환
                    if data.get("id") is not None:
                        data["id"] = str(data["id"])
                    transactions.append(Transaction(**data))
                except (json.JSONDecodeError, ValueError):
                    continue # 잘못된 형식의 줄은 무시
        return transactions

    def _read_lines_reverse(self, chunk_size: int = 4096) -> Generator[str, None, None]:
        """
        파일 전체를 메모리에 올리지 않고,
        파일 끝에서부터 한 줄씩 읽어 반환합니다.
        """
        if not self.file_path.exists():
            return

        with open(self.file_path, "rb") as f:
            f.seek(0, 2)  # 파일 끝으로 이동
            position = f.tell()
            buffer = b""

            while position > 0:
                read_size = min(chunk_size, position)
                position -= read_size
                f.seek(position)

                chunk = f.read(read_size)
                buffer = chunk + buffer
                lines = buffer.split(b"\n")

                # 첫 조각은 잘린 줄일 수 있으므로 buffer에 보관
                buffer = lines[0]

                # 완성된 줄들은 뒤에서부터 반환
                for line in reversed(lines[1:]):
                    line = line.strip()
                    if line:
                        yield line.decode("utf-8")

            # 파일 맨 앞에 남은 한 줄 처리
            buffer = buffer.strip()
            if buffer:
                yield buffer.decode("utf-8")


    def iter_transactions_reverse(self) -> Generator[Transaction, None, None]:
        """
        최신순으로 Transaction을 하나씩 반환합니다.
        JSONL 파일을 뒤에서부터 읽는 스트리밍 방식입니다.
        """
        for line in self._read_lines_reverse():
            try:
                data = json.loads(line)

                if data.get("id") is not None:
                    data["id"] = str(data["id"])

                yield Transaction(**data)

            except (json.JSONDecodeError, TypeError, ValueError) as e:
                raise ValueError(f"거래 데이터 형식이 올바르지 않습니다: {e}")

    def save(self, transaction: Transaction) -> str:
        """거래를 저장하고 생성된 ID를 반환합니다."""
        if not transaction.id:
            transaction.id = str(uuid.uuid4())[:8]
        else:
            transaction.id = str(transaction.id)

        with open(self.file_path, "a", encoding="utf-8") as f:
            json_str = json.dumps(asdict(transaction), ensure_ascii=False)
            f.write(json_str + "\n")

        return transaction.id

    def iter_transactions(self) -> Iterator[Transaction]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Transaction(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"거래 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def update_transaction(self, updated_transaction):
        transactions = list(self.get_all())

        found = False

        for index, transaction in enumerate(transactions):
            if str(transaction.id) == str(updated_transaction.id):
                transactions[index] = updated_transaction
                found = True
                break

        if not found:
            raise ValueError("수정할 거래를 찾을 수 없습니다.")

        self.save_all(transactions)

    def delete_transaction(self, transaction_id):
        transactions = list(self.get_all())

        filtered = [
            transaction
            for transaction in transactions
            if str(transaction.id) != str(transaction_id)
        ]

        if len(filtered) == len(transactions):
            return False

        self.save_all(filtered)
        return True

    def save_all(self, transactions):
        temp_path = None
        try:
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
                    data = asdict(transaction)
                    file.write(json.dumps(data, ensure_ascii=False) + "\n")
                file.flush()
                os.fsync(file.fileno())

            os.replace(temp_path, self.file_path)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise

class CategoryRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, category: Category) -> None:
        """카테고리를 저장합니다."""
        with open(self.file_path, "a", encoding="utf-8") as f:
            json_str = json.dumps(
                {
                    "name": category.name,
                    "type": category.type
                },
                ensure_ascii=False
            )
            f.write(json_str + "\n")

    def iter_categories(self) -> Iterator[Category]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Category(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"카테고리 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def get_all(self) -> List[Category]:
        return list(self.iter_categories())

    def exists(self, name: str, type_: str) -> bool:
        normalized_name = name.strip().lower()
        normalized_type = type_.strip().lower()

        for category in self.iter_categories():
            if (
                category.name.strip().lower() == normalized_name
                and category.type.strip().lower() == normalized_type
            ):
                return True
        return False

    def delete(self, name: str, type_: str) -> bool:
        categories = self.get_all()

        normalized_name = name.strip().lower()
        normalized_type = type_.strip().lower()

        original_count = len(categories)
        remaining = [
            category
            for category in categories
            if not (
                category.name.strip().lower() == normalized_name
                and category.type.strip().lower() == normalized_type
            )
        ]

        if len(remaining) == original_count:
            return False

        with open(self.file_path, "w", encoding="utf-8") as f:
            for category in remaining:
                data = {
                    "name": category.name,
                    "type": category.type
                }
                json_str = json.dumps(data, ensure_ascii=False)
                f.write(json_str + "\n")

        return True

class BudgetRepository:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.touch()

    def save(self, budget: Budget) -> None:
        """같은 월 예산이 있으면 덮어쓰고, 없으면 새로 추가합니다."""
        budgets = self.get_all()
        normalized_month = budget.month.strip()

        updated = False
        new_budgets: list[Budget] = []

        for existing_budget in budgets:
            if existing_budget.month.strip() == normalized_month:
                new_budgets.append(Budget(month=normalized_month, amount=budget.amount))
                updated = True
            else:
                new_budgets.append(existing_budget)

        if not updated:
            new_budgets.append(Budget(month=normalized_month, amount=budget.amount))

        self._write_all(new_budgets)

    def _write_all(self, budgets: List[Budget]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            for budget in budgets:
                f.write(json.dumps(asdict(budget), ensure_ascii=False) + "\n")

    def iter_budgets(self) -> Iterator[Budget]:
        if not self.file_path.exists():
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    yield Budget(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    raise ValueError(
                        f"예산 데이터 파일의 {line_no}번째 줄이 올바르지 않습니다: {e}"
                    )

    def get_all(self) -> List[Budget]:
        return list(self.iter_budgets())