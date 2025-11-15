"""
Generate a markdown file listing all tours with customer numbers (KdNr).

This script builds on the parsing logic implemented in `parse_w7.py`.  It
reads the provided tour plan CSV, assembles the list of tours, and
writes a Markdown report (`all_tours_with_kdnr.md`) that contains a
section for each tour.  Within each section, a table enumerates the
stops with their customer number, name, street, postal code, locality
and whether the stop originated from a BAR tour.

To run:

    python3 parse_all_tours.py

The script expects to find the CSV `Tourenplan 21.08.2025.csv` in
the current working directory.  If you wish to target a different
file, adjust the `csv_file` variable in `main()`.
"""

from pathlib import Path
from parse_w7 import parse_tour_plan  # reuse parsing logic


def main() -> None:
    csv_file = Path("Tourenplan 21.08.2025.csv")
    tours = parse_tour_plan(csv_file)
    output_path = Path("all_tours_with_kdnr.md")
    with open(output_path, "w") as md:
        md.write("# Alle Touren mit Kundennummern\n\n")
        for tour_name, stops in tours.items():
            # Write tour header
            md.write(f"## {tour_name}\n\n")
            # Table header
            md.write("| KdNr | Name | Straße | PLZ | Ort | Bar |\n")
            md.write("|---|---|---|---|---|---|\n")
            seen = set()
            for s in stops:
                key = (s["kdnr"], s["name"], s["street"], s["plz"], s["ort"], s["bar"])
                if key in seen:
                    continue
                seen.add(key)
                md.write(
                    f"| {s['kdnr']} | {s['name']} | {s['street']} | {s['plz']} | {s['ort']} | {'yes' if s['bar'] else 'no'} |\n"
                )
            md.write("\n\n")
    print(f"Markdown file created: {output_path}")


if __name__ == "__main__":
    main()