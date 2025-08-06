from random import randint

from faker import Faker
from sqlmodel import Session

from app import crud
from app.models import Book, BookCreate
from app.tests.utils.user import create_random_user

faker = Faker()
Faker.seed(0)


def create_random_book(db: Session) -> Book:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    title = faker.sentence(4)
    description = faker.sentence(20)
    author = faker.name()
    qtd = randint(1, 10)
    book_in = BookCreate(
        title=title, description=description, author=author, total_qtd=qtd
    )
    return crud.create_book(session=db, book_in=book_in, owner_id=owner_id)
