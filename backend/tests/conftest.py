import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["GROQ_API_KEY"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402
from langchain_core.outputs import ChatGeneration, ChatResult  # noqa: E402

from app import llm as llm_mod  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


class ScriptedChat(BaseChatModel):
    """A chat model that replays a fixed list of AI messages (including tool calls)."""
    script: list[AIMessage]
    pos: int = 0

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self.script[min(self.pos, len(self.script) - 1)]
        self.pos += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    @property
    def _llm_type(self) -> str:
        return "scripted"


class FakeLLM:
    available = True

    def __init__(self, script):
        self.chat = ScriptedChat(script=script)

    async def structured(self, schema, system, user):
        raise RuntimeError("not used")

    async def complete(self, system, user):
        return ""


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    llm_mod.set_llm(llm_mod.NullLLM())
    app.state.limiter.reset()
    with TestClient(app) as c:
        yield c


def login(client, email, pw="rep12345") -> dict:
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def rep1(client):
    return login(client, "rep1@crm.dev")


@pytest.fixture()
def rep2(client):
    return login(client, "rep2@crm.dev")


@pytest.fixture()
def manager(client):
    return login(client, "manager@crm.dev", "manager123")
