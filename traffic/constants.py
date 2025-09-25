"""Shared constants for the TrafficApp quick-start pipeline."""

DEPOT_NAME = "FAMO HQ"
DEPOT_ADDRESS = "Stuttgarter Str. 33, 01189 Dresden"
# Approximate coordinates for the depot location.
DEPOT_LATITUDE = 51.026544
DEPOT_LONGITUDE = 13.702202

# Default planning parameters
DEFAULT_TOUR_LIMIT_MINUTES = 60
DEFAULT_TRAVEL_SPEED_KMH = 35  # realistic city speed incl. traffic buffers
DEFAULT_SERVICE_BUFFER_MINUTES = 5  # minimal handling buffer per stop

# Visualization colours used for up to ten tours.
TOUR_COLOURS = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#56B4E9",
    "#F0E442",
    "#E69F00",
    "#000000",
    "#999999",
    "#882255",
]
