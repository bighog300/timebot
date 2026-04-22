from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import category as crud_category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=List[CategoryResponse])
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_category.get_categories(db, skip=skip, limit=limit)


@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(category_in: CategoryCreate, db: Session = Depends(get_db)):
    if crud_category.get_category_by_name(db, name=category_in.name):
        raise HTTPException(status_code=400, detail="Category name already exists")
    return crud_category.create_category(db, obj_in=category_in, ai_generated=False)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: UUID, db: Session = Depends(get_db)):
    category = crud_category.get_category(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: UUID, category_in: CategoryUpdate, db: Session = Depends(get_db)
):
    category = crud_category.get_category(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return crud_category.update_category(db, db_obj=category, obj_in=category_in)


@router.delete("/{category_id}")
def delete_category(category_id: UUID, db: Session = Depends(get_db)):
    category = crud_category.get_category(db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    crud_category.delete_category(db, id=category_id)
    return {"message": "Category deleted", "id": str(category_id)}


@router.get("/{category_id}/documents")
def get_category_documents(
    category_id: UUID, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    from app.crud.document import get_documents_by_category
    from app.schemas.document import DocumentResponse

    docs = get_documents_by_category(db, user=current_user, category_id=category_id, skip=skip, limit=limit)
    return [DocumentResponse.model_validate(d) for d in docs]
