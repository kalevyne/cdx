"""CalSol's subteams — the single source of truth for subsystem slugs and names.

The Box folder layout (`scripts/box_create_folder_structure.py`), subsystem
detection for CDX commits, and the dashboard cards all read from here, so adding
a subteam means editing this file only.

Box layout the dashboard owns (see docs/PROJECT-SUMMARY.md):

    <Dashboard root>/
        <Vehicle>/
            <Subsystem name>/      one per entry in SUBSYSTEMS
                CAD/
                Design Reviews/
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Subsystem:
    slug: str
    name: str  # Also the Box folder name.


SUBSYSTEMS: tuple[Subsystem, ...] = (
    Subsystem("battery", "Battery"),
    Subsystem("chassis", "Chassis"),
    Subsystem("dynamics", "Dynamics"),
    Subsystem("electrical", "Electrical"),
    Subsystem("shell", "Shell"),
    Subsystem("solar", "Solar"),
    Subsystem("strategy", "Strategy"),
    Subsystem("bizops", "BizOps"),
)

CAD_FOLDER = "CAD"
DESIGN_REVIEWS_FOLDER = "Design Reviews"
SUBSYSTEM_SUBFOLDERS: tuple[str, ...] = (CAD_FOLDER, DESIGN_REVIEWS_FOLDER)

_SLUG_BY_FOLDER_NAME = {s.name.casefold(): s.slug for s in SUBSYSTEMS}


def subsystem_for_folder_name(name: str) -> str | None:
    """The slug of the subsystem whose Box folder is called `name`, if any."""
    return _SLUG_BY_FOLDER_NAME.get(name.casefold())
