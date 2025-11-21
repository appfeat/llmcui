from core.services.project_service import ProjectService
from core.services.chat_service import ChatService
from core.services.message_service import MessageService

def test_add_and_fetch_messages(temp_db):
    psvc = ProjectService(temp_db)
    csvc = ChatService(temp_db)
    msvc = MessageService(temp_db)

    project = psvc.get_or_create_default()
    chat_id = csvc.get_or_create_first(project)

    msvc.add_message(chat_id, "user", "hello world")

    msgs = msvc.get_messages(chat_id)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "hello world"
