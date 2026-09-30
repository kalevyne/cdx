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

from collections.abc import Iterable
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

SUBSYSTEM_SUBFOLDERS: tuple[str, ...] = ("CAD", "Design Reviews")

_SLUG_BY_FOLDER_NAME = {s.name.casefold(): s.slug for s in SUBSYSTEMS}


def subsystem_for_folder_path(folder_names: Iterable[str]) -> str | None:
    """Return the subsystem slug for a Box folder, given the names of the folder
    and its ancestors (any order), or None if it isn't inside a subsystem folder."""
    for name in folder_names:
        slug = _SLUG_BY_FOLDER_NAME.get(name.casefold())
        if slug:
            return slug
    return None
