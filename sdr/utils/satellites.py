from datetime import datetime
from django.utils import timezone
from monitor.settings import SATELLITES_CACHE_DIR
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
        self.__days = 7
        self.__min_visibility = 10
        self.__logger = logging.getLogger("Satellites")
        self.__logger.info(f"init, latitude: {latitude}, longitude: {longitude}, altitude:{altitude}, use_cache: {use_cache}")

    def __get_satellites_flights_from_api(self, sat_id):
        url = (
            f"https://api.n2yo.com/rest/v1/satellite/visualpasses/"
            f"{sat_id}/{self.__latitude}/{self.__longitude}/{self.__altitude}/{self.__days}/{self.__min_visibility}/&apiKey={self.__api_key}"
        )
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        self.__logger.info(f"get satellite flights from API, id: {sat_id} ")
        try:
            return response.json()["passes"]
        except:
            return []

    def __get_satellites_flights(self, sat_id):
        if self.__use_cache:
            now = timezone.now()
            os.makedirs(SATELLITES_CACHE_DIR, exist_ok=True)
            filename = f"{SATELLITES_CACHE_DIR}/{now.strftime("%Y%m%d%H")}_{sat_id}_{self.__latitude}_{self.__longitude}_{self.__altitude}.json"
            if os.path.isfile(filename):
                with open(filename, "r") as file:
                    return json.load(file)
            flights = self.__get_satellites_flights_from_api(sat_id)
            with open(filename, "w") as file:
                json.dump(flights, file)
            return flights
        else:
            return self.__get_satellites_flights_from_api(sat_id)

    def __get_visible_satellites_flights(self, satellite, use_raw_format):
        self.__logger.info(f"processing satellite, id: {satellite['id']}, name: {satellite['name']}, raw: {use_raw_format}")
        results = []
        for i, flight in enumerate(self.__get_satellites_flights(satellite["id"])):
            begin = datetime.fromtimestamp(flight["startUTC"]).astimezone()
            end = datetime.fromtimestamp(flight["endUTC"]).astimezone()
            magnitude = flight["mag"] if "mag" in flight else 0.0
            duration = end - begin
            elevation = flight["maxEl"]
            self.__logger.info(f"flight: #{i+1}, begin: {begin}, end: {end}, elevation: {elevation}, magnitude: {magnitude}, time: {duration}")
            _begin = int(begin.timestamp()) if use_raw_format else begin
            _end = int(end.timestamp()) if use_raw_format else end
            results.append(
                {
                    "id": satellite["id"],
                    "name": satellite["name"],
                    "begin": _begin,
                    "end": _end,
                    "duration": _end - _begin,
                    "elevation": elevation,
                    "magnitude": magnitude,
                    "frequency": satellite["frequency"],
                    "bandwidth": satellite["bandwidth"],
                }
            )
        return results

    def get_visible_satellites_flights(self, satellites, use_raw_format):
        results = []
        for satellite in satellites:
            results.extend(self.__get_visible_satellites_flights(satellite, use_raw_format))
        return sorted(results, key=lambda value: value["begin"])
