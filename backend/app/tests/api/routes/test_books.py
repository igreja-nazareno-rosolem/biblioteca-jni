import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.book import create_random_book


def test_create_book(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Foo",
        "description": "Fighters",
        "author": "John Doe",
        "total_qtd": 10,
    }
    response = client.post(
        f"{settings.API_V1_STR}/books/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["author"] == data["author"]
    assert content["total_qtd"] == data["total_qtd"]
    assert content["available_qtd"] == data["total_qtd"]
    assert "id" in content
    assert "owner_id" in content


def test_read_book(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    response = client.get(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == book.title
    assert content["description"] == book.description
    assert content["author"] == book.author
    assert content["total_qtd"] == book.total_qtd
    assert content["id"] == str(book.id)
    assert content["owner_id"] == str(book.owner_id)


def test_read_book_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/books/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Book not found"


def test_read_book_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    response = client.get(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_books(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_book(db)
    create_random_book(db)
    response = client.get(
        f"{settings.API_V1_STR}/books/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_update_book(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    data = {
        "title": "Updated title",
        "description": "Updated description",
        "author": "Updated Author",
        "total_qtd": 11,
    }
    response = client.put(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["author"] == data["author"]
    assert content["total_qtd"] == data["total_qtd"]
    assert content["id"] == str(book.id)
    assert content["owner_id"] == str(book.owner_id)
    assert content["available_qtd"] == data["total_qtd"]


def test_update_book_when_some_fields_are_null(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    data = {
        "title": "Updated title",
    }
    response = client.put(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == str(book.description)
    assert content["author"] == str(book.author)
    assert content["id"] == str(book.id)
    assert content["total_qtd"] == book.total_qtd
    assert content["owner_id"] == str(book.owner_id)
    assert content["available_qtd"] == book.available_qtd


def test_update_book_when_total_qtd_is_updated_and_book_is_borrowed(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    previous_total_qtd = book.total_qtd
    num_books_to_add = 10
    book.available_qtd -= 1
    db.commit()
    data = {"total_qtd": previous_total_qtd + num_books_to_add}
    response = client.put(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == str(book.title)
    assert content["description"] == str(book.description)
    assert content["author"] == str(book.author)
    assert content["id"] == str(book.id)
    assert content["owner_id"] == str(book.owner_id)
    assert content["total_qtd"] == previous_total_qtd + num_books_to_add
    assert content["available_qtd"] == previous_total_qtd + num_books_to_add - 1


def test_update_book_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {
        "title": "Updated title",
    }
    response = client.put(
        f"{settings.API_V1_STR}/books/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Book not found"


def test_update_book_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    data = {
        "title": "Updated title",
        "description": "Updated description",
    }
    response = client.put(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_book(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    response = client.delete(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Book deleted successfully"


def test_delete_book_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/books/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Book not found"


def test_delete_book_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    book = create_random_book(db)
    response = client.delete(
        f"{settings.API_V1_STR}/books/{book.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"
