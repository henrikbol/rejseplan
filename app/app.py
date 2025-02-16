from datetime import datetime

import pytz
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.rejseplan import RejsePlan

tz = pytz.timezone("Europe/Copenhagen")

app = FastAPI()
templates = Jinja2Templates(directory="static/")
app.mount("/static", StaticFiles(directory="static"), name="static")

rjpl = RejsePlan()


@app.get("/{board_id}")
def return_board(request: Request, board_id: int = 8600675):
    df = rjpl.get_departure_board(station_id=board_id, max_journeys=30)  # Lyngby

    dep_board = df.iloc[0, 0]  # Get first station name
    current_time = datetime.now(tz).strftime("%H:%M")
    df["time"] = df.apply(lambda x: rjpl.cal_new_time(x["time"], x["rtTime"]), axis=1)
    df.drop(columns=["stop", "rtTime"], inplace=True)

    return templates.TemplateResponse(
        "form.html",
        context={
            "request": request,
            "board": dep_board,
            "time": current_time,
            "result": df.to_html(index=False, header=False),
        },
    )
