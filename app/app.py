import html as html_module
import os
from datetime import datetime

import pytz
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.rejseplan import RejsePlan

tz = pytz.timezone("Europe/Copenhagen")

# Station configuration
STATIONS = [
    {"id": "8600675", "name": "Lyngby", "lat": 55.768088, "lon": 12.503105},
    {"id": "8600626", "name": "Kbh H", "lat": 55.673063, "lon": 12.565562},
    {"id": "8600646", "name": "Nørreport", "lat": 55.683455, "lon": 12.571801},
    {"id": "8600642", "name": "Nørrebro", "lat": 55.700849, "lon": 12.537804},
    {"id": "8600655", "name": "Hellerup", "lat": 55.731026, "lon": 12.567657},
    {"id": "8600645", "name": "Vesterport", "lat": 55.676012, "lon": 12.562083},
    {"id": "8600650", "name": "Østerport", "lat": 55.692498, "lon": 12.587784},
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
        raise HTTPException(
            status_code=400, detail="Invalid board_id: must be 7 digits"
        )


def get_delay_class(time: str, rtTime: str | None) -> str:
    """Return CSS class based on delay amount."""
    if not isinstance(rtTime, str):
        return "on-time"

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


@app.get("/api/position")
def get_position(journey_ref: str = Query(...)):
    pos = rjpl.get_journey_position(journey_ref)
    if pos is None:
        raise HTTPException(status_code=404, detail="Position not available")
    lat, lon = pos
    return JSONResponse({"lat": lat, "lon": lon})


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
        # Stash journey refs before dropping them, and line names
        journey_refs = df["JourneyDetailRef.ref"].tolist()
        line_names = df["name"].tolist()
        # Calculate delay status before modifying time column
        df["delay_class"] = df.apply(
            lambda x: get_delay_class(x["time"], x["rtTime"]), axis=1
        )
        df["time"] = df.apply(
            lambda x: rjpl.cal_new_time(x["time"], x["rtTime"]), axis=1
        )
        df = df.drop(columns=["stop", "rtTime", "JourneyDetailRef.ref"])
        # Rename columns to Danish labels
        df = df.rename(columns={"name": "Linje", "direction": "Retning", "time": "Tid"})

        # Convert to HTML with custom row classes and journey ref data attributes
        result_html = df.to_html(
            index=False, header=True, escape=False, classes="dataframe"
        )
        # Split at </thead> to avoid replacing the header row
        thead_part, tbody_part = result_html.split("</thead>", 1)
        for journey_ref, line_name, delay_class in zip(
            journey_refs, line_names, df["delay_class"]
        ):
            safe_ref = html_module.escape(journey_ref, quote=True)
            safe_name = html_module.escape(line_name, quote=True)
            tbody_part = tbody_part.replace(
                "<tr>",
                f'<tr class="{delay_class}" data-journey-ref="{safe_ref}" data-line-name="{safe_name}" style="cursor:pointer">',
                1,
            )
        result_html = thead_part + "</thead>" + tbody_part

        # Remove delay_class column from display
        result_html = result_html.replace("<th>delay_class</th>", "")
        for delay_class in ["on-time", "delayed", "very-delayed"]:
            result_html = result_html.replace(f"<td>{delay_class}</td>", "")

    current_station = next((s for s in STATIONS if s["id"] == board_id), None)
    return templates.TemplateResponse(
        "form.html",
        context={
            "request": request,
            "board": dep_board,
            "time": current_time,
            "result": result_html,
            "stations": STATIONS,
            "current_board_id": board_id,
            "stadia_api_key": os.environ.get("STADIA_API_KEY", ""),
            "station_lat": current_station["lat"] if current_station else None,
            "station_lon": current_station["lon"] if current_station else None,
        },
    )
