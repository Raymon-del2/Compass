import os, sys, pathlib, traceback
sys.path.append(pathlib.Path(__file__).resolve().parents[1].as_posix())

try:
    from app.main import app
except Exception as e:
    # Return error as JSON so we can see it in the browser
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    app = FastAPI()
    @app.middleware("http")
    async def error_middleware(request: Request, call_next):
        return JSONResponse(
            status_code=500,
            content={
                "error": "StartupError",
                "detail": str(e),
                "traceback": traceback.format_exc()
            }
        )