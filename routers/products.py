from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import uuid
import os

from database import get_db
from auth.dependencies import get_current_user, get_admin_user
from schemas import ProductCreate, ProductUpdate, ProductResponse

import models

router = APIRouter(prefix="/products", tags=["Products"])

# ----- Browse products (public) ---------------------------------------------------------
@router.get("/", response_model=list[ProductResponse])
async def get_products(
    search: Optional[str] = Query(None, min_length=1),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock: Optional[bool] = Query(None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(
        models.Product.is_active == True
    )
    
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
        
    if min_price:
        query = query.filter(models.Product.price >= min_price)
        
    if max_price:
        query = query.filter(models.Product.price <= max_price)
        
    if in_stock is not None:
        query = query.filter(models.Product.stock > 0)
        
    return query.offset(skip).limit(limit).all()

# ----- Get single product (public) ------------------------------------------------------
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

# ----- Create product (Admin only) ------------------------------------------------------
@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product

# ----- Update product (Admin only) ------------------------------------------------------
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    updates: ProductUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
        
    db.commit()
    db.refresh(product)
    
    return product

# ----- Delete product (Admin only) ------------------------------------------------------
@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Soft delete - never delete real data
    setattr(product, "is_active", False)
    db.commit()
    
    return {
        "message": f"Product {product_id} deleted"
    }
    
# ----- Upload product image (Admin only) ------------------------------------------------
@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Use JPEG, PNG or WebP"
        )
        
    # Validate file size (max 2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large - max 2MB")
    
    # Find product
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is missing")
    
    # Save with unique filename - prevents overwriting
    os.makedirs("uploads", exist_ok=True)
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"uploads/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(contents)
        
    # Save URL to DB
    setattr(product, "image_url", f"/uploads/{filename}")
    db.commit()
    db.refresh(product)
    
    return product