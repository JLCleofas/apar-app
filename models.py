from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date

class AccountsPayable(Base):
    __tablename__  = 'accountspayable'

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(100), nullable=False)
    quotation = Column(String(20), index=True)
    acceptance = Column(String(14), index=True)
    vendor_po = Column(String(14), index=True)
    supplier = Column(String(50))
    document_type = Column(String(20), nullable=True)
    invoice_number = Column(String(30), nullable=True)
    date_paid = Column(Date, nullable=True)
    dv_reference = Column(String(11), nullable=True)
    currency = Column(String(3))
    po_amount = Column(Numeric(10, 2))
    invoice_amount = Column(Numeric(10, 2), nullable=True)
    balance = Column(Numeric(10, 2))
    fully_paid = Column(Boolean, default=False)