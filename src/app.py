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

def cal_time_dif_min(timea: str, timeb:str) -> str:
    return str(abs(int((datetime.strptime(timea, "%H:%M") - datetime.strptime(timeb, "%H:%M")).total_seconds()/60)))

def cal_new_time(time:str, rtTime:str) -> str:
    if isinstance(rtTime, str):
        return f'{time} (+{cal_time_dif_min(time, rtTime)})'
    else:
        return f'{time}'

@app.get("/{board_id}")
def return_board(request: Request, board_id: int = 8600675):
    dep = rjpl.departureBoard(board_id, useBus=False, useMetro=False, useTrain=True)  # Lyngby
    df = pd.json_normalize(dep)
    dep_board = df.loc[0, "stop"]
    current_time = datetime.now(tz).strftime("%H:%M")
    if "rtTime" in df.columns:
        df["time"] = df.apply(lambda x: cal_new_time(x["time"], x["rtTime"]), axis=1)

    df = df[df["type"].isin(["S", "REG", "IC"])][
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
