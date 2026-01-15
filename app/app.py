from datetime import datetime

import pytz
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.rejseplan import RejsePlan

tz = pytz.timezone("Europe/Copenhagen")

# Station configuration
STATIONS = [
    {"id": "8600675", "name": "Lyngby"},
    {"id": "8600626", "name": "Kbh H"},
    {"id": "8600646", "name": "Nørreport"},
    {"id": "8600642", "name": "Nørrebro"},
    {"id": "8600655", "name": "Hellerup"},
]

app = FastAPI()
templates = Jinja2Templates(directory="static/")
app.mount("/static", StaticFiles(directory="static"), name="static")

rjpl = RejsePlan()


def validate_board_id(board_id: str) -> None:
    """Validate board_id is a valid station ID format."""
    if not board_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid board_id: must be numeric")
    if len(board_id) != 7:
        raise HTTPException(status_code=400, detail="Invalid board_id: must be 7 digits")


def get_delay_class(time: str, rtTime: str | None) -> str:
    """Return CSS class based on delay amount."""
    if not isinstance(rtTime, str):
        return "on-time"

    # Calculate delay in minutes
    from datetime import datetime
    try:
        time_obj = datetime.strptime(time, "%H:%M:%S")
        rtTime_obj = datetime.strptime(rtTime, "%H:%M:%S")
        delay_minutes = abs((rtTime_obj - time_obj).total_seconds() / 60)

        if delay_minutes == 0:
            return "on-time"
        elif delay_minutes < 5:
            return "delayed"
        else:
            return "very-delayed"
    except ValueError:
        return "on-time"


@app.get("/")
@app.get("/{board_id}")
def return_board(request: Request, board_id: str = "8600675"):
    validate_board_id(board_id)
    df, error = rjpl.get_departure_board(station_id=board_id, max_journeys=45)
    current_time = datetime.now(tz).strftime("%H:%M")
    dep_board = "Unknown"
    result_html = ""

    if error:
        result_html = f'<div class="error-message">⚠️ {error}</div>'
    elif df.empty:
        result_html = '<div class="info-message">Ingen afgange fundet</div>'
    else:
        dep_board = df.iloc[0, 0]  # Get first station name
        # Calculate delay status before modifying time column
        df["delay_class"] = df.apply(lambda x: get_delay_class(x["time"], x["rtTime"]), axis=1)
        df["time"] = df.apply(lambda x: rjpl.cal_new_time(x["time"], x["rtTime"]), axis=1)
        df = df.drop(columns=["stop", "rtTime"])
        # Rename columns to Danish labels
        df = df.rename(columns={"name": "Linje", "direction": "Retning", "time": "Tid"})

        # Convert to HTML with custom row classes
        result_html = df.to_html(index=False, header=True, escape=False, classes="dataframe")
        # Add delay classes to rows (simple find/replace approach)
        for idx, delay_class in enumerate(df["delay_class"]):
            if delay_class:
                result_html = result_html.replace("<tr>", f'<tr class="{delay_class}">', 1)

        # Remove delay_class column from display
        result_html = result_html.replace("<th>delay_class</th>", "")
        for delay_class in ["on-time", "delayed", "very-delayed"]:
            result_html = result_html.replace(f"<td>{delay_class}</td>", "")

    return templates.TemplateResponse(
        "form.html",
        context={
            "request": request,
            "board": dep_board,
            "time": current_time,
            "result": result_html,
            "stations": STATIONS,
            "current_board_id": board_id,
        },
    )
