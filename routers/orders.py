from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session, joinedload

from database import get_db
from auth.dependencies import get_current_user, get_admin_user
from schemas import OrderResponse

import models

router = APIRouter(prefix="/orders", tags=["Orders"])

# Valid transactions map
VALID_TRANSITIONS = {
    models.OrderStatus.pending: [models.OrderStatus.confirmed, models.OrderStatus.cancelled],
    models.OrderStatus.confirmed: [models.OrderStatus.shipped, models.OrderStatus.cancelled],
    models.OrderStatus.shipped: [models.OrderStatus.delivered],
    models.OrderStatus.delivered: [],
    models.OrderStatus.cancelled: [],
}

# ----- Background task - send order confirmation ----------------------------------------
def send_order_confirmation(email: str, order_id: int, total: float):
    # In production: integrate SendGrid, SES, etc.
    print(f"Sending Confirmation to {email}")
    print(f"Order #{order_id} confirmed - total: ${total:.2f}")
    
# ---- Place order -----------------------------------------------------------------------
@router.post("/", response_model=OrderResponse)
async def place_order(
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    #1. Get cart items with products
    cart_items = db.query(models.CartItem).options(
        joinedload(models.CartItem.product)
    ).filter(
        models.CartItem.user_id == current_user.id
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # 2. Validate stock for ALL items before touching anything
    for item in cart_items:
        if not item.product.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"Product '{item.product.name}' is no longer available"
            )
            
        if item.product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{item.product.name}'"
                       f" - only {item.product.stock} left"
            )
            
    # 3. Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    # 4. Create order
    order = models.Order(
        user_id=current_user.id,
        total=round(total, 2)
    )
    db.add(order)
    db.flush()  # <- gets order.id without committing yet
    
    # 5. Create order items + reduce stock
    for item in cart_items:
        order_item = models.OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=float(str(item.product.price))    # snapshot price
        )
        db.add(order_item)
        
        # Reduce stock
        new_stock = int(str(item.product.stock)) - item.quantity
        setattr(item.product, "stock", new_stock)
        
    # 6. Clear cart
    db.query(models.CartItem).filter(
        models.CartItem.user_id == current_user.id
    ).delete()
    
    # 7. Commit everything at once - all or nothing
    db.commit()
    db.refresh(order)
    
    # 8. Send confirmation email in the background
    background_tasks.add_task(
        send_order_confirmation,
        email=str(current_user.email),
        order_id=order.id,  # type: ignore
        total=order.total  # type: ignore
    )
    
    # 9. Return order with items
    return db.query(models.Order).options(
        joinedload(models.Order.order_items).joinedload(
            models.OrderItem.product
        )
    ).filter(models.Order.id == order.id).first()
    
# ----- Get single order -----------------------------------------------------------------
@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).options(
        joinedload(models.Order.order_items).joinedload(
            models.OrderItem.product
        )
    ).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

# ----- Cancel order ---------------------------------------------------------------------
@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    order = db.query(models.Order).options(
        joinedload(models.Order.order_items).joinedload(
            models.OrderItem.product
        )
    ).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status not in [
        models.OrderStatus.pending,
        models.OrderStatus.confirmed
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.status}'"
        )
        
    # Restore stock for each item
    for order_item in order.order_items:
        new_stock = int(str(order_item.product.stock)) + int(str(order_item.quantity))
        setattr(order_item.product, "stock", new_stock)
        
    setattr(order, "status", models.OrderStatus.cancelled)
    db.commit()
    db.refresh(order)
    return order

# ----- Update order status (admin only) -------------------------------------------------
@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    status: models.OrderStatus,
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_admin_user)
):
    order = db.query(models.Order).options(
        joinedload(models.Order.order_items).joinedload(
            models.OrderItem.product
        )
    ).filter(models.Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Ensure the status is a plain string before using it as a key
    current_status = models.OrderStatus(order.status)

    # Use a default empty list if the status isn't found in your map
    allowed = VALID_TRANSITIONS.get(current_status, [])

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot move order from '{order.status}' to '{status}'"
        )
    
    setattr(order, "status", status)
    db.commit()
    db.refresh(order)
    return order