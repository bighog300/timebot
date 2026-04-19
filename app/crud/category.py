from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def create_category(db: Session, obj_in: CategoryCreate, ai_generated: bool = False) -> Category:
    slug = Category.generate_slug(obj_in.name)
    # Ensure unique slug
    base_slug, counter = slug, 1
    while db.query(Category).filter(Category.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    db_obj = Category(
        **obj_in.model_dump(),
        slug=slug,
        ai_generated=ai_generated,
        created_by_user=not ai_generated,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_category(db: Session, id: UUID) -> Optional[Category]:
    return db.query(Category).filter(Category.id == id).first()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    return db.query(Category).filter(Category.name.ilike(name)).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100) -> List[Category]:
    return (
        db.query(Category)
        .order_by(desc(Category.document_count))
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_category(db: Session, db_obj: Category, obj_in: CategoryUpdate) -> Category:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    if "name" in update_data:
        db_obj.slug = Category.generate_slug(update_data["name"])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_category(db: Session, id: UUID) -> Optional[Category]:
    obj = db.query(Category).filter(Category.id == id).first()
    if obj:
        db.delete(obj)
        db.commit()
    return obj
