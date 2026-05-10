from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin   = Column(Boolean, default=False, nullable=False)
    orders     = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    description = Column(String)
    price       = Column(Float, nullable=False)
    stock       = Column(Integer, default=0)
    orders      = relationship("Order", back_populates="product")

class Order(Base):
    __tablename__ = "orders"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity   = Column(Integer, nullable=False)
    notes      = Column(Text, nullable=True)
    user       = relationship("User", back_populates="orders")
    product    = relationship("Product", back_populates="orders")
