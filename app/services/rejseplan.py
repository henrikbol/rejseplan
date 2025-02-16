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

    def get_departure_board(
        self,
        station_id: str = "",
        date: str = "",
        time: str = "",
        lang: str = "da",
        duration: int = 60,
        max_journeys: int = -1,
        **kwargs,
    ) -> pd.DataFrame:
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
            pd.DataFrame: A DataFrame containing the departure information with columns ["name", "direction", "time", "rtTime"].

        Raises:
            requests.exceptions.HTTPError: If an HTTP error occurs.
            requests.exceptions.JSONDecodeError: If a JSON decode error occurs.
            Exception: For any other exceptions that occur.
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
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            df = pd.json_normalize(data["Departure"])
            df = df[df["ProductAtStop.catOut"].isin(prods)][
                ["stop", "name", "direction", "time", "rtTime"]
            ]
            return df
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.JSONDecodeError as json_err:
            logging.error("JSON decode error:", json_err)
        except Exception as err:
            logging.error(f"An error occurred: {err}")

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
