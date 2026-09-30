"""Creates the Box folder layout the dashboard owns (see app/subsystems.py)."""

from dataclasses import dataclass

from app.services.box_client import BoxService
from app.subsystems import CAD_FOLDER, DESIGN_REVIEWS_FOLDER, SUBSYSTEMS, Subsystem


@dataclass(frozen=True)
class SubsystemFolders:
    subsystem: Subsystem
    folder_id: str
    cad_folder_id: str
    design_reviews_folder_id: str


def ensure_vehicle_layout(
    box: BoxService, root_folder_id: str, vehicle: str
) -> dict[str, SubsystemFolders]:
    """Create <root>/<vehicle>/<Subsystem>/{CAD, Design Reviews} for every
    subsystem, reusing folders that already exist. Returns them by slug."""
    vehicle_id = box.ensure_folder(root_folder_id, vehicle)
    layout = {}
    for subsystem in SUBSYSTEMS:
        folder_id = box.ensure_folder(vehicle_id, subsystem.name)
        layout[subsystem.slug] = SubsystemFolders(
            subsystem=subsystem,
            folder_id=folder_id,
            cad_folder_id=box.ensure_folder(folder_id, CAD_FOLDER),
            design_reviews_folder_id=box.ensure_folder(folder_id, DESIGN_REVIEWS_FOLDER),
        )
    return layout
