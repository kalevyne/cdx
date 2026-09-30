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
from app.subsystems import SUBSYSTEM_SUBFOLDERS, SUBSYSTEMS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("vehicle", help="Vehicle folder name, e.g. the car's name or year")
    args = parser.parse_args()

    box = get_box_service()
    root_id = get_settings().require_dashboard_root_folder_id()

    vehicle_id = box.ensure_folder(root_id, args.vehicle)
    print(f"{args.vehicle}/  ({vehicle_id})")
    for subsystem in SUBSYSTEMS:
        subsystem_id = box.ensure_folder(vehicle_id, subsystem.name)
        print(f"  {subsystem.name}/  ({subsystem_id})")
        for subfolder in SUBSYSTEM_SUBFOLDERS:
            print(f"    {subfolder}/  ({box.ensure_folder(subsystem_id, subfolder)})")


if __name__ == "__main__":
    main()
