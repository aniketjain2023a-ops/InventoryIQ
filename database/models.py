from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean
)

from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True)
    name = Column(String)
    category = Column(String)
    unit_price = Column(Float)
    quantity = Column(Float, default=0.0)
    reorder_level = Column(Integer)

    supplier_name = Column(String)
    supplier_email = Column(String)
    supplier_phone = Column(String)
    lead_time_days = Column(Integer, default=0)

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    transactions = relationship("Transaction", back_populates="product")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, default=0.0)
    product = relationship("Product", back_populates="inventory")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    transaction_type = Column(String)
    quantity = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    product = relationship("Product", back_populates="transactions")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True)
    po_number = Column(String, unique=True)

    product_id = Column(Integer, ForeignKey("products.id"))
    supplier_name = Column(String)
    supplier_email = Column(String)
    supplier_phone = Column(String)
    lead_time_days = Column(Integer, default=0)

    quantity = Column(Float)
    unit_price = Column(Float, default=0.0)
    status = Column(String, default="Draft")

    created_at = Column(DateTime, default=datetime.utcnow)
    is_closed = Column(Boolean, default=False)

    product = relationship("Product")
