import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Book,
    BookCreate,
    BookPublic,
    BooksPublic,
    BookUpdate,
    Message,
)

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/", response_model=BooksPublic)
def read_books(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve books.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Book)
        count = session.exec(count_statement).one()
        statement = select(Book).offset(skip).limit(limit)
        books = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Book)
            .where(Book.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Book)
            .where(Book.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        books = session.exec(statement).all()

    return BooksPublic(data=books, count=count)


@router.get("/{id}", response_model=Book)
def read_book(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get book by ID.
    """
    book = session.get(Book, id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not current_user.is_superuser and (book.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return book


@router.post("/", response_model=Book)
def create_book(*, session: SessionDep, current_user: CurrentUser, book_in: BookCreate):
    """
    Create a new book.
    """
    book = Book.model_validate(
        book_in,
        update={"owner_id": current_user.id, "available_qtd": book_in.total_qtd},
    )
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.put("/{id}", response_model=BookPublic)
def update_book(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    book_in: BookUpdate,
) -> Any:
    """
    Update a book.
    """
    book = session.get(Book, id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not current_user.is_superuser and (book.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = book_in.model_dump(exclude_unset=True)
    if "total_qtd" in update_dict:
        borrowed_qtd = book.total_qtd - book.available_qtd
        if update_dict["total_qtd"] < borrowed_qtd:
            raise HTTPException(
                status_code=400,
                detail="Total quantity cannot be less than borrowed quantity",
            )
        update_dict["available_qtd"] = update_dict["total_qtd"] - borrowed_qtd
    book.sqlmodel_update(update_dict)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete("/{id}")
def delete_book(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an book.
    """
    book = session.get(Book, id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not current_user.is_superuser and (book.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(book)
    session.commit()
    return Message(message="Book deleted successfully")
