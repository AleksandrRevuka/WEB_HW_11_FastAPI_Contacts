import logging
import time
from ipaddress import ip_address, ip_network
from typing import Callable

import click
import redis.asyncio as redis_async
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings, init_async_redis
from src.database.db import get_db
from src.routes import addressbook, auth, users

# logger = logging.getLogger("uvicorn")

app = FastAPI()

app.include_router(auth.router, prefix="/api")
app.include_router(addressbook.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.on_event("startup")
async def startup() -> FastAPILimiter:
    """
    The startup function is called when the server starts up.
    It's a good place to initialize things that are needed by your application,
    such as databases and caches.  It can also be used to pre-load data into memory,
    or do other tasks that need to happen before the server begins serving requests.

    :return: A fastapilimiter object
    """
    try:
        r = await init_async_redis()
        await FastAPILimiter.init(r)
    except redis_async.ConnectionError as e:
        click.secho(f"ERROR redis: {e}", bold=True, fg="red", italic=True)
        raise HTTPException(status_code=500, detail="Error connecting to the redis")



@app.middleware("http")
async def custom_midleware(request: Request, call_next) -> Response:
    """
    The custom_midleware function is a custom middleware function that adds the time it took to process the request
    to the response headers. It does this by getting the current time before calling call_next, and then subtracting
    the start_time from it after call_next returns. The result is added to a new header called &quot;performance&quot;.


    :param request: Request: Pass the request to the next middleware
    :param call_next: Call the next middleware in the chain
    :return: A response object with a performance header
    """
    start_time = time.time()
    response = await call_next(request)
    during = time.time() - start_time
    response.headers["performance"] = str(during)
    return response


# @app.middleware("http")
# async def limit_access_by_ip(request: Request, call_next: Callable) -> JSONResponse:
#     """
#     The limit_access_by_ip function is a middleware function that limits access to the API by IP address.
#     It checks if the client's IP address is in a list of allowed addresses, and if not, it returns an error message.

#     :param request: Request: Get the client ip address
#     :param call_next: Callable: Call the next function in the middleware chain
#     :return: A jsonresponse object with a 403 status code and an error message
#     """
#     # Ensure request.client is not None before accessing host
#     if request.client and request.client.host:
#         host = request.client.host
#         ip = ip_address(host)
#         allowed_ips = list(ip_network(f"{settings.allowed_ips}/24"))

#         if ip not in allowed_ips:
#             return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Not allowed IP address"})
#     else:
#         return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": "Invalid client"})

#     response = await call_next(request)
#     return response


# @app.on_event("startup")
# async def on_startup() -> None:
#     """
#     The on_startup function is called when the application starts.
#     It prints a message to the console, so that you know where to go in your browser.

#     :return: None
#     """
#     message = "Open http://127.0.0.1:8000/docs to start api 🚀 🌘 🪐"
#     color_url = click.style("http://127.0.0.1:8000/docs", bold=True, fg="green", italic=True)
#     color_message = f"Open {color_url} to start api 🚀 🌘 🪐"
    # logger.info(message, extra={"color_message": color_message})


@app.get("/api/healthchecker", tags=["healthchecker"])
async def healthchecker(db: AsyncSession = Depends(get_db)) -> dict:
    """
    The healthchecker function is a simple function that checks the database connection.
    It returns a JSON response with the message "Welcome to FastAPI!" if everything is working correctly.

    :param db: Session: Pass the database connection to the function
    :return: A dictionary with a message
    """
    try:
        result = await db.execute(text("SELECT 1"))
        fetched_result = result.fetchone()
        if fetched_result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
