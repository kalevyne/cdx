from app.subsystems import SUBSYSTEMS, subsystem_for_folder_name


def test_subsystem_slugs_are_unique():
    slugs = [s.slug for s in SUBSYSTEMS]
    assert len(slugs) == len(set(slugs))


def test_subsystem_for_folder_name_is_case_insensitive():
    assert subsystem_for_folder_name("battery") == "battery"
    assert subsystem_for_folder_name("BizOps") == "bizops"


def test_subsystem_for_folder_name_outside_subsystems():
    assert subsystem_for_folder_name("Zephyr") is None
