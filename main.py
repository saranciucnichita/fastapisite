from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from app.pages.router import router as router_pages

app = FastAPI(title="EveryHere")

app.mount("/images", StaticFiles(directory="app/images"), name="images")

app.include_router(router_pages)
