from app.subsystems import SUBSYSTEMS, subsystem_for_folder_path


def test_subsystem_slugs_are_unique():
    slugs = [s.slug for s in SUBSYSTEMS]
    assert len(slugs) == len(set(slugs))


def test_subsystem_for_folder_path_matches_ancestor_case_insensitively():
    assert subsystem_for_folder_path(["All Files", "CDX", "Zephyr", "battery", "CAD"]) == "battery"


def test_subsystem_for_folder_path_outside_subsystem_folders():
    assert subsystem_for_folder_path(["All Files", "CDX", "Zephyr"]) is None
