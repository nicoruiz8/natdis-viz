import requests
import re
import csv
import random
from io import BytesIO
from PIL import Image


class Geocode:
    """Methods related to geocoding, reverse geocoding, flag retrieval and coordinate handling."""

    @staticmethod
    def get_code(lat: float, lon: float) -> str:
        """
        Get the ISO3166 alpha-2 code for a country by reverse geocoding the input coordinates.

        :param lat: latitude
        :param lon: longitude

        :return: ISO3166 alpha-2 code

        :note: the reverse geocoding is done with Nominatim OpenStreetMap API.
        """
        geo_url = f"https://nominatim.openstreetmap.org/reverse?format=geocodejson&lat={lat}&lon={lon}&zoom=3"
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ]
        headers = {"User-Agent": random.choice(user_agents)}
        geo = requests.get(geo_url, headers=headers).json()
        if len(geo.keys()) == 1:
            return "un"
        else:
            return geo["features"][0]["properties"]["geocoding"]["country_code"]

    @staticmethod
    def format_code(code: str, toformat: str = "alpha2") -> str:
        """
        Re-format the input ISO3166 code into any of the supported formats.

        :param code: ISO3166 country code in any format
        :param toformat: output format of the code {"alpha2", "alpha3", "numeric"}

        :return: re-fromated country code
        """
        # Initializing needed data
        formats = ["alpha2", "alpha3", "num"]
        with open("modules/country_codes.csv") as file:
            reader = csv.DictReader(file)
            codes = []
            for row in reader:
                codes.append(row)

        # Country data retreiving
        if re.match(r"[a-zA-Z]{2}$", code):
            entry = next(
                (item for item in codes if item["iso2"] == code.upper()), False
            )
        elif re.match(r"[a-zA-Z]{3}$", code):
            entry = next(
                (item for item in codes if item["iso3"] == code.upper()), False
            )
        elif re.match(r"[0-9]{3}$", code):
            entry = next((item for item in codes if item["isonum"] == code), False)
        else:
            entry = False

        # Error handling
        if entry == False:
            raise ValueError("Not a valid code.")
        if toformat not in formats:
            raise ValueError("Not a valid format parameter.")

        # Country-code transformation
        if toformat == "alpha2":
            return entry["iso2"]
        elif toformat == "alpha3":
            return entry["iso3"]
        elif toformat == "num":
            return entry["isonum"]

    @staticmethod
    def get_flag(code: str) -> tuple[Image.Image, float]:
        """
        Retrieve the flag of a country, EU or UN.

        :param code: country code in any ISO3166 format

        :return flag: flag of the country
        :return aspect_ratio: aspect ratio of the flag (height/width)

        :note: flags are obtained from https://flagcdn.com API
        """
        if code == None:
            code = "un"  # If no code (ie, no country) retrieve default UN flag
        flag_url = f"https://flagcdn.com/w2560/{code.lower()}.png"
        flag_response = requests.get(flag_url, stream=True)
        flag = Image.open(BytesIO(flag_response.content))
        aspect_ratio = flag.size[1] / flag.size[0]
        return flag, aspect_ratio

    @staticmethod
    def get_country(code: str) -> str:
        """
        Get the name of the country associated to a ISO3166 code.

        :param code: ISO3166 country code in any of the supported formats {"alpha2", "alpha3", "numeric"}

        :return: country's name
        """
        # Initializing needed data
        formats = ["alpha2", "alpha3", "num"]
        with open("country_codes.csv") as file:
            reader = csv.DictReader(file)
            codes = []
            for row in reader:
                codes.append(row)

        # Country data retreiving
        if re.match(r"[a-zA-Z]{2}$", code):
            entry = next(
                (item for item in codes if item["iso2"] == code.upper()), False
            )
        elif re.match(r"[a-zA-Z]{3}$", code):
            entry = next(
                (item for item in codes if item["iso3"] == code.upper()), False
            )
        elif re.match(r"[0-9]{3}$", code):
            entry = next((item for item in codes if item["isonum"] == code), False)
        else:
            entry = False

        # Error handling
        if entry == False:
            raise ValueError("Not a valid code.")

        # Return country name
        return entry["name"]

    @staticmethod
    def coord_converter(coords: tuple[float, float]) -> tuple[str, str]:
        """
        Coordinate converter from decimal plus/minus format to decimal North/South East/West format.

        :param coords: tuple (latitude, longitude) in decimal plus/minus format {-90<float<+90, -180<float<+180}

        :return: converted latitdue and longitude
        :note: Example: +45 = "45°N", -45 = 45°S, +60 = 60°E, -60 = 60°W
        """
        lat, lon = coords
        if lat < 0:
            lat = f"{lat * -1} °S"
        else:
            lat = f"{lat} °N"
        if lon < 0:
            lon = f"{lon * -1} °W"
        else:
            lon = f"{lon} °E"
        return lat, lon
