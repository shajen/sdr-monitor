from datetime import datetime
import json
import logging
import os
import requests


class SatellitesFlightReader:
    def __init__(self, api_key, latitude, longitude, altitude, use_cache):
        self.__api_key = api_key
        self.__latitude = latitude
        self.__longitude = longitude
        self.__altitude = altitude
        self.__use_cache = use_cache
        self.__days = 10
        self.__min_visibility = 10
        self.__logger = logging.getLogger("Satellites")

    def __get_satellites_flights_from_api(self, sat_id):
        url = (
            f"https://api.n2yo.com/rest/v1/satellite/visualpasses/"
            f"{sat_id}/{self.__latitude}/{self.__longitude}/{self.__altitude}/{self.__days}/{self.__min_visibility}/&apiKey={self.__api_key}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        self.__logger.info(f"get satellite flights from API, id: {sat_id} ")
        return response.json()["passes"]

    def __get_satellites_flights(self, sat_id):
        if self.__use_cache:
            filename = f"sat_{sat_id}.json"
            if os.path.isfile(filename):
                with open(filename, "r") as file:
                    return json.load(file)
            flights = self.__get_satellites_flights_from_api(sat_id)
            with open(filename, "w") as file:
                json.dump(flights, file)
            return flights
        else:
            return self.__get_satellites_flights_from_api(sat_id)

    def __get_visible_satellites_flights(self, satellite):
        self.__logger.info(f"processing satellite, id: {satellite['id']}, name: {satellite['name']}")
        results = []
        for i, flight in enumerate(self.__get_satellites_flights(satellite["id"])):
            start = datetime.fromtimestamp(flight["startVisibility"] if "startVisibility" in flight else flight["startUTC"]).astimezone()
            end = datetime.fromtimestamp(flight["endUTC"]).astimezone()
            mag = flight["mag"] if "mag" in flight else 0.0
            duration = end - start
            elevetion = flight["maxEl"]
            self.__logger.info(f"flight: #{i+1}, start: {start}, end: {end}, elevation: {elevetion}, mag: {mag}, time: {duration}")
            results.append(
                {
                    "id": satellite["id"],
                    "name": satellite["name"],
                    "start": int(start.timestamp()),
                    "end": int(end.timestamp()),
                    "frequency": satellite["frequency"],
                    "bandwidth": satellite["bandwidth"],
                }
            )
        return results

    def get_visible_satellites_flights(self, satellites):
        results = []
        for satellite in satellites:
            results.extend(self.__get_visible_satellites_flights(satellite))
        return sorted(results, key=lambda value: value["start"])
