from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Date, ForeignKey

class AccountsPayable(Base):
    __tablename__  = 'accountspayable'

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(100), nullable=False)
    quotation = Column(String(20), index=True)
    acceptance = Column(String(14), index=True)
    vendor_po = Column(String(14), index=True)
    supplier = Column(String(50))
    invoice_number = Column(String(30), nullable=True)
    currency = Column(String(3))
    po_amount = Column(Numeric(10, 2))
    invoice_amount = Column(Numeric(10, 2), nullable=True)
    balance = Column(Numeric(10, 2))
    fully_paid = Column(Boolean, default=False)

    ## TODO: Create a separate column for transaction amounts.
    ## Make invoice_amount column the sum of ALL transaction amounts.

## TODO: Create a separate table for transaction history for logging purposes.
## Add a foreign key from the AccountsPayable table ID.
class TransactionLogs(Base):
    __tablename__ = 'transaction_logs'

    transaction_id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String(20), nullable=True)
    transaction_amount = Column(Numeric(10, 2), nullable=False)
    date_paid = Column(Date, nullable=False)
    dv_reference = Column(String(11), nullable=True)
    project_id = Column(Integer, ForeignKey('accountspayable.id'), nullable=False)
