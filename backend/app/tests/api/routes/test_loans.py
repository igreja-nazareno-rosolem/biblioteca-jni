import uuid
from datetime import datetime

from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.book import create_random_book
from app.tests.utils.loan import create_random_loan


def test_create_loan(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    data = {"book_id": str(book.id)}
    response = client.post(
        f"{settings.API_V1_STR}/loans/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["book_id"] == data["book_id"]
    assert "id" in content
    assert "user_id" in content
    assert "created_at" in content


def test_read_loan(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    loan = create_random_loan(db)
    response = client.get(
        f"{settings.API_V1_STR}/loans/{loan.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["book_id"] == str(loan.book_id)
    assert content["user_id"] == str(loan.user_id)
    assert content["id"] == str(loan.id)
    assert "created_at" in content


def test_read_loan_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/loans/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Loan not found"


def test_read_loan_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    loan = create_random_loan(db)
    response = client.get(
        f"{settings.API_V1_STR}/loans/{loan.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_loans(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_loan(db)
    create_random_loan(db)
    response = client.get(
        f"{settings.API_V1_STR}/loans/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_close_loan(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    loan = create_random_loan(db)
    with freeze_time(datetime(2025, 1, 1)):
        response = client.put(
            f"{settings.API_V1_STR}/loans/{loan.id}",
            headers=superuser_token_headers,
        )
    assert response.status_code == 200
    content = response.json()
    assert content["book_id"] == str(loan.book_id)
    assert content["user_id"] == str(loan.user_id)
    assert content["id"] == str(loan.id)
    assert "created_at" in content
    assert content["closed_at"] == "2025-01-01T00:00:00"
