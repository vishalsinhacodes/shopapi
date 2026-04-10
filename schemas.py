from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

from datetime import datetime
from models import OrderStatus

#------ User Schemas----------------------------------------------------------------------
class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str
    
class UserCreate(UserBase):
    password: str = Field(min_length=8)
    
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None    
    
#------ Token Schemas---------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str
    
#------ Product Schemas-------------------------------------------------------------------
class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    
class ProductCreate(ProductBase):
    pass 

class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    
class ProductResponse(ProductBase):
    id: int
    image_url: str | None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)      
    
#------ Cart Schemas----------------------------------------------------------------------
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1)
    
class CartItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    
    model_config = ConfigDict(from_attributes=True)
    
class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total: float
    
#------ Order Schemas---------------------------------------------------------------------
class OrderItemResponse(BaseModel):
    id: int
    product: ProductResponse
    quantity: int
    price: float
    
    model_config = ConfigDict(from_attributes=True)
    
class OrderResponse(BaseModel):
    id: int
    status: OrderStatus
    total: float
    created_at: datetime
    order_items: list[OrderItemResponse]
    
    model_config = ConfigDict(from_attributes=True)       
    