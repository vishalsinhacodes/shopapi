from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from schemas import CartItemCreate, CartItemResponse, CartResponse
from auth.dependencies import get_current_user
from database import get_db


import models

router = APIRouter(prefix="/cart", tags=["Cart"])

# ------ View Cart -----------------------------------------------------------------------
@router.get("/", response_model=CartResponse)
async def get_cart(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # joinedload prevents N+1 query problem
    items = db.query(models.CartItem).options(
        joinedload(models.CartItem.product)
    ).filter(
        models.CartItem.user_id == current_user.id
    ).all()
    
    total = sum(item.product.price * item.quantity for item in items)
    
    return {
        "items": items,
        "total": round(total, 2)
    }
    
# ------ Add to Cart ---------------------------------------------------------------------
@router.post("/", response_model=CartItemResponse)
async def add_to_cart(
    item: CartItemCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check product exists and is active
    product = db.query(models.Product).filter(
        models.Product.id == item.product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check stock available
    if product.stock < item.quantity:   # type: ignore
        raise HTTPException(
            status_code=400,
            detail=f"Only {product.stock} items in stock"
        )
        
    # If product is already in cart - increase quantity
    existing = db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id,
        models.CartItem.product_id == item.product_id
    ).first()
    
    if existing:
        new_quantity = int(str(existing.quantity)) + item.quantity
        
        if new_quantity > product.stock:    # type: ignore
            raise HTTPException(
                status_code=400,
                detail=f"Only {product.stock} items in stock"
            )
            
        setattr(existing, "quantity", new_quantity)
        db.commit()
        db.refresh(existing)
        
        return existing
    
    # Otherwise create new cart item
    cart_item = models.CartItem(
        user_id = current_user.id,
        product_id = item.product_id,
        quantity = item.quantity
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    # Reload with product relationship
    return db.query(models.CartItem).options(
        joinedload(models.CartItem.product)
    ).filter(models.CartItem.id == cart_item.id).first()
    
# ------ Update quantity -----------------------------------------------------------------
@router.put("/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: int,
    quantity: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if quantity < 1:
        raise HTTPException(status_code=400, detail="Quantity must be at least 1")
    
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    # Check stock
    if cart_item.product.stock < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Only {cart_item.product.stock} items in stock"
        )
        
    setattr(cart_item, "quantity", quantity)
    db.commit()
    db.refresh(cart_item)
    
    return cart_item

# ------ Clear entire Cart ---------------------------------------------------------------
@router.delete("/")
async def clear_cart(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return {"message": "Cart cleared"}

# ------ Remove from Cart ----------------------------------------------------------------
@router.delete("/{item_id}")
async def remove_from_cart(
    item_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": "Item removed from cart"}
    
    
    