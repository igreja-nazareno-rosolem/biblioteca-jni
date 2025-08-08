import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Loan,
    LoanCreate,
    LoanPublic,
    LoansPublic,
)

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/", response_model=LoansPublic)
def read_loans(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve user loans.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Loan)
        count = session.exec(count_statement).one()
        statement = select(Loan).offset(skip).limit(limit)
        loans = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Loan)
            .where(Loan.user_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Loan)
            .where(Loan.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        loans = session.exec(statement).all()

    return LoansPublic(data=loans, count=count)


@router.get("/{id}", response_model=Loan)
def read_loan(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get loan by ID.
    """
    loan = session.get(Loan, id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not current_user.is_superuser and (loan.user_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return loan


@router.post("/", response_model=Loan)
def create_loan(*, session: SessionDep, current_user: CurrentUser, loan_in: LoanCreate):
    """
    Create a new loan.
    """
    loan = Loan.model_validate(loan_in, update={"user_id": current_user.id})
    session.add(loan)
    session.commit()
    session.refresh(loan)
    return loan


@router.put("/{id}", response_model=LoanPublic)
def close_loan(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
) -> Any:
    """
    Close a loan.
    """
    loan = session.get(Loan, id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if not current_user.is_superuser and (loan.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    loan.closed_at = datetime.now()
    session.commit()
    return loan
