from core.services.project_service import ProjectService
from core.services.chat_service import ChatService

def test_first_chat_creation(temp_db):
    psvc = ProjectService(temp_db)
    csvc = ChatService(temp_db)

    project = psvc.get_or_create_default()
    chat_id = csvc.get_or_create_first(project)

    assert isinstance(chat_id, str)
    assert len(chat_id) > 5

def test_reset_chat(temp_db):
    psvc = ProjectService(temp_db)
    csvc = ChatService(temp_db)

    project = psvc.get_or_create_default()
    chat_id = csvc.get_or_create_first(project)

    csvc.reset_chat(chat_id)

    msgs = csvc.get_messages(chat_id)
    assert msgs == []
