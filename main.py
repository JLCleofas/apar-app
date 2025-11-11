from fastapi import FastAPI
from database import Base, engine
from routers import accounts_payable


app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/healthy")
async def health_check():
    return {'status': 'healthy'}

app.include_router(accounts_payable.router)