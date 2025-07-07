"""Assorted functions for manipulating location/geographic data"""

from typing import Optional, Tuple
from math import isnan
from utils.io import yaml_to_dict
from geopy.geocoders import Nominatim


def location_name(
    latlon: Tuple[float, float],
    loc_part: str,
):
    """Given a tuple a location's latitutde and longitude, returns location descripton
    Args:
        latlon: two-member tuple with latitude (in degrees N) and longitude (in degrees E
        loc_part: desired part of location description (e.g., 'town','county','state','country','postcode')
    Returns:
        String corresponding to the desired component of the geolocated address
    """
    error_string = "Argument latlon must be a two-member tuple of floats of the form (latitude [degrees N],longitude [degrees E])"
    if not isinstance(latlon, tuple):
        raise ValueError(error_string)
    if len(latlon) != 2:
        raise ValueError(error_string)
    if (not isinstance(latlon[0], float)) | (not isinstance(latlon[1], float)):
        raise ValueError(error_string)
    if (isnan(latlon[0])) | (isnan(latlon[1])):
        return "Provided latitude and/or longitude are NaN"

    # Set up geolocator and get the location object the given lat-lon tuple
    geolocator = Nominatim(user_agent="http")
    try:
        location = geolocator.reverse(latlon)
    except:
        raise Exception(
            f"Unable to get location object for lat={latlon[0]}, lon={latlon[1]}"
        )
    else:
        # Parse the location object
        if "address" not in location.raw:
            return "Address information not found in location object"
        if loc_part not in location.raw["address"]:
            loc_descriptors = list(location.raw["address"].keys())
            exception_string = f"For location ({latlon[0]},{latlon[1]}), descriptor 'loc_part' argument must be one of {*loc_descriptors,}"
            raise Exception(exception_string)
        return location.raw["address"][loc_part]


def get_state_fips(
    state_name: str, yamlpath="/Users/lindseygulden/dev/leg-up-private/data/fips.yml"
):

    fips_dict = yaml_to_dict(yamlpath)
    if state_name in fips_dict["state_fips"]:
        return fips_dict["state_fips"][state_name]
    return None


def city_lat_lon(
    city: Optional[str] = None,
    state: Optional[str] = None,
    zipcode: Optional[str] = None,
    country: Optional[str] = None,
):
    """Returns (lat, lon) coordinates for a string descriptor of a location
    Args:
        city: string specifying city, if available
        state: string specifying state, if available
        zipcode: string specfiying zip code (US) if available
        country: sptring specifying country, if available
    Returns:
        tuple with the latitude and longitude coordinates (in degrees N and E)
    """
    if city is None and state is None and zipcode is None and country is None:
        raise ValueError(
            "At least one of the following keyword arguments must be present: city, state, zipcode, country"
        )
    location_string = " ".join(
        [x for x in [city, state, zipcode, country] if x is not None]
    )
    geolocator = Nominatim(user_agent="myapplication")

    location = geolocator.geocode(location_string)
    return (float(location.raw["lat"]), float(location.raw["lon"]))
