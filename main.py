import logging
import time

import click
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.routes import addressbook, auth

logger = logging.getLogger("uvicorn")

app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(addressbook.router, prefix="/api")


@app.middleware("http")
async def custom_midleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    during = time.time() - start_time
    response.headers["performance"] = str(during)
    return response


app.mount("/src", StaticFiles(directory="src/static"), name="static")


@app.on_event("startup")
async def on_startup() -> None:
    message = "Open http://127.0.0.1:8000/docs to start api 🚀 🌘 🪐"
    color_url = click.style(
        "http://127.0.0.1:8000/docs", bold=True, fg="green", italic=True
    )
    color_message = f"Open {color_url} to start api 🚀 🌘 🪐"
    logger.info(message, extra={"color_message": color_message})


@app.get("/api/healthchecker", tags=["healthchecker"])
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
