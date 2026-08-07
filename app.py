import json

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from loop import run
from rules import apply_rules

app = FastAPI()


@app.post("/run")
def run_loop():
    return run()


@app.get("/categorise")
def categorise(narration: str):
    """Uses the saved rulebook. No model call. Zero tokens."""
    try:
        with open("rulebook.json") as f:
            rules = json.load(f)
    except FileNotFoundError:
        return {"category": None, "note": "Run the loop first."}
    return {"category": apply_rules(rules, narration)}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")