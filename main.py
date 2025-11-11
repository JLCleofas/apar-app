from fastapi import FastAPI, Request, status
from database import Base, engine
from routers import accounts_payable
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse


app = FastAPI()

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="./templates")

app.mount("/static", StaticFiles(directory="./static"), name="static")

@app.get("/")
def render_projects(request: Request):
    return RedirectResponse(url="/ap/projects", status_code=status.HTTP_302_FOUND)

@app.get("/healthy")
async def health_check():
    return {'status': 'healthy'}

app.include_router(accounts_payable.router)