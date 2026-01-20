from database import Base
from sqlalchemy import Integer, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class APProject(BaseModel):
    __tablename__  = 'ap_projects'

    created_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    modified_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    client: Mapped[str] = mapped_column(String(100), nullable=False)
    quotation: Mapped[str] = mapped_column(String(20), index=True)
    acceptance: Mapped[str] = mapped_column(String(14), index=True)
    currency: Mapped[str] = mapped_column(String(3))
    total_po_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    total_paid: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    balance: Mapped[float] = mapped_column(Numeric(10, 2))
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    invoice: Mapped[list['Invoice']] = relationship(back_populates="project")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="project", order_by=lambda: Transaction.date_paid)
    vendor_po: Mapped[list['POToVendor']] = relationship(back_populates="project")
    creator: Mapped['User'] = relationship("User", foreign_keys=[created_by_id])
    modifier: Mapped['User'] = relationship("User", foreign_keys=[modified_by_id])

class POToVendor(BaseModel):
    __tablename__ = 'po_to_vendor'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    modified_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    vendor_po: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    vendor: Mapped[str] = mapped_column(String(50), nullable=False)
    po_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped['APProject'] = relationship(back_populates="vendor_po")
    invoice: Mapped['Invoice'] = relationship(back_populates="vendor_po")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="vendor_po")
    user: Mapped['User'] = relationship(back_populates="vendor_po")

class Invoice(BaseModel):
    __tablename__ = 'invoices'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    vendor_po_id: Mapped[int] = mapped_column(ForeignKey('po_to_vendor.id'), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    modified_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False
                                             )
    invoice_type: Mapped[str] = mapped_column(String(20), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(30), nullable=True)
    invoice_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    project: Mapped['APProject'] = relationship(back_populates="invoice")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="invoice")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="invoice")
    user: Mapped['User'] = relationship(back_populates="invoice")

class Transaction(BaseModel):
    __tablename__ = 'transactions'

    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), nullable=False)
    vendor_po_id: Mapped[int] = mapped_column(ForeignKey('po_to_vendor.id'), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    transaction_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    date_paid: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dv_reference: Mapped[str] = mapped_column(String(11), nullable=True)

    invoice: Mapped['Invoice'] = relationship(back_populates="transaction")
    project: Mapped['APProject'] = relationship(back_populates="transaction")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="transaction")
    user: Mapped['User'] = relationship(back_populates="transaction")


class User(BaseModel):
    __tablename__ = 'users'
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    team: Mapped[str] = mapped_column(String(50), nullable=False)

    invoice: Mapped['Invoice'] = relationship(back_populates="user")
    project: Mapped['APProject'] = relationship(back_populates="user")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="user")
    transaction: Mapped['Transaction'] = relationship(back_populates="user")
