from faker import Faker
from sqlmodel import Session

from app import crud
from app.models import Book, LoanCreate
from app.tests.utils.book import create_random_book
from app.tests.utils.user import create_random_user

faker = Faker()
Faker.seed(0)


def create_random_loan(db: Session) -> Book:
    user = create_random_user(db)
    user_id = user.id
    assert user_id is not None
    book = create_random_book(db)
    book_id = book.id
    assert book_id is not None

    loan_in = LoanCreate(book_id=book_id)
    return crud.create_loan(session=db, loan_in=loan_in, user_id=user_id)
