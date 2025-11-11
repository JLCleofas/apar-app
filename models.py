from database import Base
from sqlalchemy import Column, Integer, String, Boolean

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
    po_amount = Column(String)
    invoice_amount = Column(String)
    balance = Column(String)
    fully_paid = Column(Boolean, default=False)