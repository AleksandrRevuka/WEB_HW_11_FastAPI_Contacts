import time

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.routes import birthday, contacts, emails, phones, search

app = FastAPI()


app.include_router(contacts.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(birthday.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(phones.router, prefix="/api")


@app.middleware("http")
async def custom_midleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    during = time.time() - start_time
    response.headers["performance"] = str(during)
    return response


@app.get("/api/healthchecker", tags=["healthchecker"])
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
