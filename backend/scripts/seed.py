"""Seeds demo data so a freshly deployed instance isn't empty.
Run with: ./venv/bin/python -m scripts.seed (from the backend/ directory).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.db.base import AsyncSessionLocal
from app.models.account import Account, AccountType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User, UserRole

DEMO_CUSTOMER_EMAIL = "demo.customer@example.com"
DEMO_ADMIN_EMAIL = "demo.admin@example.com"
DEMO_PASSWORD = "DemoPass123!"


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        customer = User(
            email=DEMO_CUSTOMER_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            role=UserRole.CUSTOMER.value,
        )
        admin = User(
            email=DEMO_ADMIN_EMAIL,
            hashed_password=hash_password(DEMO_PASSWORD),
            role=UserRole.ADMIN.value,
        )
        db.add_all([customer, admin])
        await db.flush()

        checking = Account(
            user_id=customer.id,
            account_number="1000000001",
            account_type=AccountType.CHECKING.value,
            balance_cents=250000,
        )
        savings = Account(
            user_id=customer.id,
            account_number="1000000002",
            account_type=AccountType.SAVINGS.value,
            balance_cents=1000000,
        )
        db.add_all([checking, savings])
        await db.flush()

        db.add_all(
            [
                Transaction(
                    account_id=checking.id,
                    type=TransactionType.DEPOSIT.value,
                    amount_cents=250000,
                    balance_after_cents=250000,
                    description="Initial demo deposit",
                ),
                Transaction(
                    account_id=savings.id,
                    type=TransactionType.DEPOSIT.value,
                    amount_cents=1000000,
                    balance_after_cents=1000000,
                    description="Initial demo deposit",
                ),
            ]
        )

        await db.commit()

    print("Seed complete.")
    print(f"  Customer login: {DEMO_CUSTOMER_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Admin login:    {DEMO_ADMIN_EMAIL} / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
