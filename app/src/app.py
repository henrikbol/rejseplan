from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from datetime import datetime, timezone
import pytz

import rjpl

import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="static/")
app.mount("/static", StaticFiles(directory="static"), name="static")

tz = pytz.timezone('Europe/Copenhagen')

@app.get("/{board_id}")
def return_board(request: Request, board_id: int = 8600675):
    dep = rjpl.departureBoard(board_id, useBus=False)  # Lyngby
    df = pd.json_normalize(dep)
    dep_board = df.loc[0, "stop"]
    current_time = datetime.now(tz).strftime("%H:%M")

    df = df[df["type"].isin(["S", "M", "REG", "IC"])][
        [
            "name",
            "finalStop",
            "time",
        ]
    ]
    return templates.TemplateResponse(
        "form.html",
        context={
            "request": request,
            "board": dep_board,
            "time": current_time,
            "result": df.to_html(index=False, header=False),
        },
    )
