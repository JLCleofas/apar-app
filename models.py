from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column


class BaseModel(Base):
    __abstract__ = True
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    # created_at = Column(Date, default=None)
    # updated_at = Column(Date, default=None)

class APProject(BaseModel):
    __tablename__  = 'ap_projects'

    client = Column(String(100), nullable=False)
    quotation = Column(String(20), index=True)
    acceptance = Column(String(14), index=True)
    currency = Column(String(3))
    total_po_amount = Column(Numeric(10, 2))
    total_paid = Column(Numeric(10, 2), nullable=True)
    balance = Column(Numeric(10, 2))

    invoices: Mapped[list['Invoice']] = relationship(back_populates="project")
    transactions: Mapped[list['TransactionLog']] = relationship(back_populates="project", order_by=lambda: TransactionLog.date_paid)
    po_to_vendor: Mapped[list['POToVendor']] = relationship(back_populates="project")
# TODO: Add table for PO to vendor
# TODO: Remove vendor, vendor_po from Invoice
class POToVendor(BaseModel):
    __tablename__ = 'po_to_vendor'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    vendor = Column(String(50), nullable=False)
    po_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)

    project: Mapped['APProject'] = relationship(back_populates="po_to_vendor")
class Invoice(BaseModel):
    __tablename__ = 'invoices'
    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    vendor_po_id = Mapped[int] = mapped_column(ForeignKey('po_to_vendor.id'), nullable=True)
    invoice_type = Column(String(20), nullable=True)
    invoice_number = Column(String(30), nullable=True)
    invoice_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)

    project: Mapped['APProject'] = relationship(back_populates="invoices")
    transactions: Mapped[list['TransactionLog']] = relationship(back_populates="invoice")
    vendor_po: Mapped['POToVendor'] = relationship(back_populates="project")

class TransactionLog(BaseModel):
    __tablename__ = 'transaction_logs'

    project_id: Mapped[int] = mapped_column(ForeignKey('ap_projects.id'), nullable=False)
    invoice_id: Mapped[int] = mapped_column(ForeignKey('invoices.id'), nullable=False)

    document_type = Column(String(20), nullable=True)
    transaction_amount = Column(Numeric(10, 2), nullable=False)
    date_paid = Column(Date, nullable=False)
    dv_reference = Column(String(11), nullable=True)

    invoice: Mapped['Invoice'] = relationship(back_populates="transactions")
    project: Mapped['APProject'] = relationship(back_populates="transactions")
