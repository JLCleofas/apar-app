from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(Date, default=None)
    updated_at = Column(Date, default=None)

class APProject(BaseModel):
    __tablename__  = 'ap_projects'

    client = Column(String(100), nullable=False)
    quotation = Column(String(20), index=True)
    acceptance = Column(String(14), index=True)
    currency = Column(String(3))
    total_po_amount = Column(Numeric(10, 2))
    total_paid = Column(Numeric(10, 2), nullable=True)
    balance = Column(Numeric(10, 2))
    is_paid = Column(Boolean, default=False)

    invoice: Mapped[list['Invoice']] = relationship(back_populates="project")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="project", order_by=lambda: Transaction.date_paid)
    vendor_po: Mapped[list['POToVendor']] = relationship(back_populates="project")
# TODO: Add table for PO to vendor
# TODO: Remove vendor, vendor_po from Invoice
class POToVendor(BaseModel):
    __tablename__ = 'po_to_vendor'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    vendor_po = Column(String(14), nullable=False, unique=True)
    vendor = Column(String(50), nullable=False)
    po_amount = Column(Numeric(10, 2), nullable=False)
    balance = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    is_paid = Column(Boolean, default=False)

    project: Mapped['APProject'] = relationship(back_populates="vendor_po")
    invoice: Mapped['Invoice'] = relationship(back_populates="vendor_po")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="vendor_po")
class Invoice(BaseModel):
    __tablename__ = 'invoices'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    vendor_po_id: Mapped[int] = mapped_column(ForeignKey('po_to_vendor.id'), nullable=True)
    invoice_type = Column(String(20), nullable=True)
    invoice_number = Column(String(30), nullable=True)
    invoice_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    is_paid = Column(Boolean, default=False)

    project: Mapped['APProject'] = relationship(back_populates="invoice")
    transaction: Mapped[list['Transaction']] = relationship(back_populates="invoice")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="invoice")

class Transaction(BaseModel):
    __tablename__ = 'transactions'

    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), nullable=False)
    vendor_po_id: Mapped[int] = mapped_column(ForeignKey('po_to_vendor.id'), nullable=True)

    transaction_amount = Column(Numeric(10, 2), nullable=False)
    date_paid = Column(Date, nullable=False)
    dv_reference = Column(String(11), nullable=True)

    invoice: Mapped['Invoice'] = relationship(back_populates="transaction")
    project: Mapped['APProject'] = relationship(back_populates="transaction")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="transaction")
