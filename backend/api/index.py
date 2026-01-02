import os, sys, pathlib
sys.path.append(pathlib.Path(__file__).resolve().parents[1].as_posix())

from app.main import app  # exports FastAPI instance named `app`