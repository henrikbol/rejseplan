import logging
import os
from datetime import datetime

import pandas as pd
import pytz
import requests

tz = pytz.timezone("Europe/Copenhagen")


class RejsePlan:
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
        """
        Fetches the departure board for a given station.

        Args:
            station_id (str): The ID of the station. Defaults to an empty string.
            date (str): The date for which to fetch the departure board. Defaults to an empty string.
            time (str): The time for which to fetch the departure board. Defaults to an empty string.
            lang (str): The language for the response. Defaults to "da".
            duration (int): The duration in minutes for which to fetch departures. Defaults to 60.
            max_journeys (int): The maximum number of journeys to fetch. Defaults to -1.
            **kwargs: Additional parameters to include in the request.

        Returns:
            tuple[pd.DataFrame, str | None]: A tuple containing:
                - DataFrame with departure information (columns: ["name", "direction", "time", "rtTime"])
                - Error message string if an error occurred, None otherwise
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
                ["stop", "name", "direction", "time", "rtTime"]
            ]
            return df, None
        except requests.exceptions.Timeout:
            error_msg = "API request timed out. Please try again."
            logging.error(error_msg)
            return pd.DataFrame(), error_msg
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"Could not fetch departures (HTTP {http_err.response.status_code})"
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

    @staticmethod
    def cal_time_dif_min(timea: str, timeb: str) -> str:
        return str(
            abs(
                int(
                    (
                        datetime.strptime(timea, "%H:%M:%S") - datetime.strptime(timeb, "%H:%M:%S")
                    ).total_seconds()
                    / 60
                )
            )
        )

    @staticmethod
    def cal_new_time(time: str, rtTime: str | None) -> str:
        if isinstance(rtTime, str):
            return f"{time[:5]} (+{RejsePlan.cal_time_dif_min(time, rtTime)})"
        else:
            return f"{time[:5]}"
