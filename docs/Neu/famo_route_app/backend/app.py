"""
Flask backend for the FAMO traffic routing app.

This simple backend accepts a CSV upload, parses customer information,
applies basic normalisation and deduplication, and performs a simple
clustering and route ordering using heuristics defined in util.py.

The resulting tours are returned as JSON for consumption by the
frontend. Note that this backend does not perform real geocoding or
traffic-aware travel time computation; instead, it uses the Haversine
formula and a constant average speed to estimate travel time. Users
should supply latitude and longitude in the CSV for accurate results.
"""

import os
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename

from . import util

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
ALLOWED_EXTENSIONS = {"csv", "txt"}

# Coordinates of the FAMO depot (approx. Dresden center)
FAMO_COORDS = (51.050407, 13.737262)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/", methods=["GET"])
    def index():
        # Serve the frontend index file
        return send_from_directory(
            os.path.abspath(os.path.join(app.root_path, "../frontend")), "index.html"
        )

    @app.route("/static/<path:filename>")
    def static_files(filename):
        # Serve static files from frontend directory
        return send_from_directory(
            os.path.abspath(os.path.join(app.root_path, "../frontend")), filename
        )

    @app.route("/upload", methods=["POST"])
    def upload_file():
        # Handle file upload and tour computation
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(save_path)
            try:
                customers = util.parse_csv(save_path)
            except Exception as e:
                return jsonify({"error": f"Failed to parse CSV: {e}"}), 500
            # Normalise addresses and deduplicate
            for cust in customers:
                cust["street"] = util.normalise_address(cust["street"])
                cust["city"] = util.normalise_address(cust["city"])
            customers = util.deduplicate_customers(customers)
            # Ensure lat/lon
            for cust in customers:
                if cust["lat"] is None or cust["lon"] is None:
                    # Fallback: assign dummy coordinates; these should be updated later
                    # For demonstration, we place them at depot; this will cluster them into first tour
                    cust["lat"] = FAMO_COORDS[0]
                    cust["lon"] = FAMO_COORDS[1]
            # Build clusters
            clusters = util.cluster_customers(
                FAMO_COORDS, customers, service_time_min=2.0, max_route_time_min=60.0
            )
            # Order clusters
            tours = []
            for cluster in clusters:
                order = util.nearest_neighbor_order(FAMO_COORDS, customers, cluster)
                tours.append(order)
            # Build response structure
            resp = {
                "num_customers": len(customers),
                "num_tours": len(tours),
                "tours": [],
            }
            for idx, tour in enumerate(tours):
                tour_data = {
                    "tour_index": idx + 1,
                    "customers": [],
                }
                for pos, cust_idx in enumerate(tour):
                    cust = customers[cust_idx]
                    tour_data["customers"].append(
                        {
                            "order": pos + 1,
                            "kdnr": cust["kdnr"],
                            "name": cust["name"],
                            "street": cust["street"],
                            "plz": cust["plz"],
                            "city": cust["city"],
                            "lat": cust["lat"],
                            "lon": cust["lon"],
                            "bar": cust["bar"],
                        }
                    )
                resp["tours"].append(tour_data)
            return jsonify(resp)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

    return app


if __name__ == "__main__":
    # Running directly for development
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)