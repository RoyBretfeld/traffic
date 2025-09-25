"""Lightweight Leaflet map renderer without external Python dependencies."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Iterable

from . import constants
from .models import Tour


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"de\">
<head>
  <meta charset=\"utf-8\" />
  <title>TrafficApp Tourenkarte</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <link
    rel=\"stylesheet\"
    href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"
    integrity=\"sha256-sA+e2atf3M8dLsyQbXt2GmQ0Db6FdF0HqS2u2Hc+g3c=\"
    crossorigin=\"\"
  />
  <style>
    html, body, #map { height: 100%; margin: 0; }
    .tour-legend { position: absolute; top: 10px; right: 10px; background: white; padding: 8px; border-radius: 4px; box-shadow: 0 0 6px rgba(0,0,0,0.2); }
    .tour-legend div { margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
    .tour-legend span { display: inline-block; width: 12px; height: 12px; border-radius: 6px; }
  </style>
</head>
<body>
  <div id=\"map\"></div>
  <div class=\"tour-legend\" id=\"legend\"></div>
  <script
    src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"
    integrity=\"sha256-o9N1j7kGSts2euM6XV5g92QHH6lBHFpMd8gP0i0wMcE=\"
    crossorigin=\"\"
  ></script>
  <script>
    const data = __TOUR_DATA__;
    const map = L.map('map').setView([data.center[0], data.center[1]], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap-Mitwirkende'
    }).addTo(map);

    const depotMarker = L.marker([data.depot.lat, data.depot.lon], {title: 'Depot'}).addTo(map);
    depotMarker.bindPopup(data.depot.label);

    const legend = document.getElementById('legend');

    data.tours.forEach((tour) => {
      const colour = tour.colour;
      const legendItem = document.createElement('div');
      const colourBox = document.createElement('span');
      colourBox.style.backgroundColor = colour;
      legendItem.appendChild(colourBox);
      legendItem.appendChild(document.createTextNode(`${tour.tour_id} (${tour.num_stops} Stops)`));
      legend.appendChild(legendItem);

      const points = [];
      tour.stops.forEach((stop) => {
        if (stop.latitude === null || stop.longitude === null) {
          return;
        }
        const marker = L.circleMarker([stop.latitude, stop.longitude], {
          radius: 6,
          color: colour,
          fillColor: colour,
          fillOpacity: 0.85,
        }).addTo(map);
        let popup = `<b>${stop.name}</b><br>${stop.address}<br>Dienst: ${stop.service_minutes} min`;
        if (stop.time_window) {
          popup += `<br>Fenster: ${stop.time_window.start}–${stop.time_window.end}`;
        }
        marker.bindPopup(popup);
        points.push([stop.latitude, stop.longitude]);
      });
      if (points.length) {
        const route = [[data.depot.lat, data.depot.lon], ...points, [data.depot.lat, data.depot.lon]];
        L.polyline(route, {color: colour, weight: 3, opacity: 0.8}).addTo(map);
      }
    });
  </script>
</body>
</html>
"""


class MapRenderer:
    """Render tours onto an interactive Leaflet map."""

    def __init__(self, depot_lat: float, depot_lon: float) -> None:
        self.depot_lat = depot_lat
        self.depot_lon = depot_lon

    def render(self, tours: Iterable[Tour], output_file: Path) -> None:
        tours = list(tours)
        if not tours:
            raise ValueError("At least one tour is required to render a map.")

        lats = [self.depot_lat]
        lons = [self.depot_lon]
        for tour in tours:
            for customer in tour.customers:
                if customer.location is None:
                    continue
                lats.append(customer.location.latitude)
                lons.append(customer.location.longitude)

        map_center = (mean(lats), mean(lons))
        serialised_tours = []
        for idx, tour in enumerate(tours):
            colour = constants.TOUR_COLOURS[idx % len(constants.TOUR_COLOURS)]
            serialised_tours.append(
                {
                    "tour_id": tour.identifier,
                    "num_stops": tour.num_stops,
                    "colour": colour,
                    "stops": [
                        {
                            "name": customer.name,
                            "address": customer.address,
                            "latitude": customer.location.latitude if customer.location else None,
                            "longitude": customer.location.longitude if customer.location else None,
                            "service_minutes": customer.service_minutes,
                            "time_window": (
                                {
                                    "start": customer.time_window.start.strftime("%H:%M"),
                                    "end": customer.time_window.end.strftime("%H:%M"),
                                }
                                if customer.time_window
                                else None
                            ),
                        }
                        for customer in tour.customers
                    ],
                }
            )

        payload = {
            "center": map_center,
            "depot": {
                "lat": self.depot_lat,
                "lon": self.depot_lon,
                "label": f"Depot: {constants.DEPOT_ADDRESS}",
            },
            "tours": serialised_tours,
        }

        html = HTML_TEMPLATE.replace("__TOUR_DATA__", json.dumps(payload, ensure_ascii=False))
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html, encoding="utf-8")
