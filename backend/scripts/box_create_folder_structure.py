"""Create the Box folder layout the dashboard owns, under BOX_DASHBOARD_ROOT_FOLDER_ID.

    python -m scripts.box_create_folder_structure "<Vehicle name>"

Creates <root>/<Vehicle>/<Subsystem>/{CAD, Design Reviews} for every subsystem
in app/subsystems.py. Idempotent: existing folders are reused, so re-running it
(e.g. after adding a subsystem) only fills in what's missing. Requires the Box
connection from scripts/box_oauth_setup.py.
"""

from __future__ import annotations

import argparse

from app.config import get_settings
from app.services.box_client import get_box_service
from app.services.folder_layout import ensure_vehicle_layout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vehicle", help="Vehicle folder name, e.g. the car's name or year")
    args = parser.parse_args()

    root_id = get_settings().require_dashboard_root_folder_id()
    layout = ensure_vehicle_layout(get_box_service(), root_id, args.vehicle)

    print(f"{args.vehicle}/")
    for folders in layout.values():
        print(f"  {folders.subsystem.name}/  ({folders.folder_id})")
        print(f"    CAD/  ({folders.cad_folder_id})")
        print(f"    Design Reviews/  ({folders.design_reviews_folder_id})")


if __name__ == "__main__":
    main()
