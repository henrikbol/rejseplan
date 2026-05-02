import logging
import os
from datetime import datetime

import pandas as pd
import pytz
import requests

tz = pytz.timezone("Europe/Copenhagen")


class RejsePlan:
    """HTTP client for the Rejseplan public API (API 2.0).

    Attributes:
        access_id: API key read from the ``RPL_ACCESS_ID`` environment variable.
        base_url: Root URL for all API endpoints.
        session: Shared ``requests.Session`` with Accept: application/json header.
    """

    def __init__(self):
        self.access_id = os.environ.get("RPL_ACCESS_ID")
        self.base_url = "https://www.rejseplanen.dk/api/"
        self.headers = {"Accept": "application/json"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_departure_board(
        self,
        station_id: str = "",
        date: str = "",
        time: str = "",
        lang: str = "da",
        duration: int = 60,
        max_journeys: int = -1,
        **kwargs,
    ) -> tuple[pd.DataFrame, str | None]:
        """Fetch upcoming departures from a station, filtered to S-Tog, Re, and IC trains.

        Results are sorted by transport mode (S-Tog → Re → IC) then by scheduled time.

        Args:
            station_id: Rejseplan stop ID (e.g. ``"8600675"`` for Lyngby).
            date: Departure date in ``DD.MM.YY`` format; defaults to today when empty.
            time: Departure time in ``HH:MM`` format; defaults to now when empty.
            lang: Response language code. Defaults to ``"da"``.
            duration: Look-ahead window in minutes. Defaults to ``60``.
            max_journeys: Maximum number of departures to return; ``-1`` means no limit.
            **kwargs: Extra query parameters forwarded verbatim to the API.

        Returns:
            A ``(DataFrame, error)`` pair. On success, ``error`` is ``None`` and the
            DataFrame has columns ``stop``, ``name``, ``direction``, ``time``,
            ``rtTime``, and ``JourneyDetailRef.ref``. On failure, the DataFrame is
            empty and ``error`` contains a human-readable message.
        """
        url = f"{self.base_url}departureBoard"

        params = {
            "accessId": self.access_id,
            "id": station_id,
            "date": date,
            "time": time,
            "lang": lang,
            "duration": duration,
            "maxJourneys": max_journeys,
            "type": "DEP",
            **kwargs,
        }

        prods = ["S-Tog", "Re", "IC"]

        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if there are any departures
            if "Departure" not in data or not data["Departure"]:
                return pd.DataFrame(), None

            df = pd.json_normalize(data["Departure"])
            df = df[df["ProductAtStop.catOut"].isin(prods)][
                ["stop", "name", "direction", "time", "rtTime", "JourneyDetailRef.ref", "ProductAtStop.catOut"]
            ]
            df["sort_order"] = df["ProductAtStop.catOut"].map({prod: i for i, prod in enumerate(prods)})
            df = df.sort_values(["sort_order", "time"]).drop(columns=["sort_order", "ProductAtStop.catOut"])

            return df, None
        except requests.exceptions.Timeout:
            error_msg = "API request timed out. Please try again."
            logging.error(error_msg)
            return pd.DataFrame(), error_msg
        except requests.exceptions.HTTPError as http_err:
            error_msg = (
                f"Could not fetch departures (HTTP {http_err.response.status_code})"
            )
            logging.error(f"HTTP error occurred: {http_err}")
            return pd.DataFrame(), error_msg
        except requests.exceptions.JSONDecodeError as json_err:
            error_msg = "Invalid response from API"
            logging.error(f"JSON decode error: {json_err}")
            return pd.DataFrame(), error_msg
        except KeyError as key_err:
            error_msg = "Unexpected API response format"
            logging.error(f"Key error: {key_err}")
            return pd.DataFrame(), error_msg
        except Exception as err:
            error_msg = "An unexpected error occurred"
            logging.error(f"An error occurred: {err}")
            return pd.DataFrame(), error_msg

    def get_journey_position(self, journey_ref: str) -> tuple[float, float] | None:
        """Return the last known GPS position of a vehicle journey.

        Args:
            journey_ref: Opaque journey reference from a ``JourneyDetailRef.ref``
                field in a departure-board response.

        Returns:
            ``(lat, lon)`` as floats, or ``None`` if the position is unavailable
            or the API call fails.
        """
        url = f"{self.base_url}journeyDetail"
        params = {"accessId": self.access_id, "id": journey_ref}
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            pos = data.get("lastPos")
            if pos and "lat" in pos and "lon" in pos:
                return float(pos["lat"]), float(pos["lon"])
            return None
        except Exception as err:
            logging.error(f"Journey position error: {err}")
            return None

    @staticmethod
    def cal_time_dif_min(timea: str, timeb: str) -> str:
        """Compute the absolute difference between two ``HH:MM:SS`` times in whole minutes.

        Args:
            timea: First time string in ``HH:MM:SS`` format.
            timeb: Second time string in ``HH:MM:SS`` format.

        Returns:
            Absolute difference in minutes as a string (e.g. ``"5"``).
        """
        return str(
            abs(
                int(
                    (
                        datetime.strptime(timea, "%H:%M:%S")
                        - datetime.strptime(timeb, "%H:%M:%S")
                    ).total_seconds()
                    / 60
                )
            )
        )

    @staticmethod
    def cal_new_time(time: str, rtTime: str | None) -> str:
        """Format a departure time, appending a delay suffix when the train is late.

        Args:
            time: Scheduled departure in ``HH:MM:SS`` format.
            rtTime: Real-time departure in ``HH:MM:SS`` format, or ``None`` if on time.

        Returns:
            ``"HH:MM"`` when on time, or ``"HH:MM (+N)"`` when delayed by N minutes.
        """
        if isinstance(rtTime, str):
            return f"{time[:5]} (+{RejsePlan.cal_time_dif_min(time, rtTime)})"
        else:
            return f"{time[:5]}"
