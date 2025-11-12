from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Numeric

class AccountsPayable(Base):
    __tablename__  = 'accountspayable'

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String)
    quotation = Column(String)
    acceptance = Column(String)
    vendor_po = Column(String)
    supplier = Column(String)
    document_type = Column(String)
    invoice_number = Column(String)
    date_paid = Column(String)
    dv_reference = Column(String)
    currency = Column(String)
    po_amount = Column(Numeric(10, 2))
    invoice_amount = Column(Numeric(10, 2))
    balance = Column(Numeric(10, 2))
    fully_paid = Column(Boolean, default=False)