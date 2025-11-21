from core.services.project_service import ProjectService

def test_get_or_create_default_project(temp_db):
    svc = ProjectService(temp_db)
    proj = svc.get_or_create_default()
    assert proj == "default"

def test_create_named_project(temp_db):
    svc = ProjectService(temp_db)
    name = "research"
    proj = svc.get_or_create(name)
    assert proj == name
