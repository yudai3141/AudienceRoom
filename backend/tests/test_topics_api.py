import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.models.topic import Topic
from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.db.session import get_db
from app.main import app as fastapi_app
import app.db.models  # noqa: F401

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture()
def db_session() -> Session:
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def user(db_session: Session) -> User:
    u = User(
        firebase_uid="topics_api_user",
        email="topics_api@example.com",
        display_name="Topics API User",
    )
    db_session.add(u)
    db_session.flush()
    return u


class TestTopicsAPI:
    def test_create_topic(self, client: TestClient, user: User) -> None:
        res = client.post("/topics", json={"user_id": user.id, "title": "研究内容"})
        assert res.status_code == 201
        body = res.json()
        assert body["title"] == "研究内容"
        assert body["status"] == "active"

    def test_create_empty_title_rejected_by_validation(self, client: TestClient, user: User) -> None:
        res = client.post("/topics", json={"user_id": user.id, "title": ""})
        assert res.status_code == 422  # pydantic min_length

    def test_create_whitespace_title_rejected_by_service(self, client: TestClient, user: User) -> None:
        res = client.post("/topics", json={"user_id": user.id, "title": "   "})
        assert res.status_code == 400  # service strip -> ValueError

    def test_list_topics(self, client: TestClient, user: User) -> None:
        client.post("/topics", json={"user_id": user.id, "title": "A"})
        client.post("/topics", json={"user_id": user.id, "title": "B"})
        res = client.get("/topics", params={"user_id": user.id})
        assert res.status_code == 200
        assert {t["title"] for t in res.json()} == {"A", "B"}

    def test_get_detail_with_graph(self, client: TestClient, db_session: Session, user: User) -> None:
        topic = Topic(user_id=user.id, title="研究内容")
        db_session.add(topic)
        db_session.flush()
        a = TopicNode(topic_id=topic.id, label="手法", coverage="covered")
        b = TopicNode(topic_id=topic.id, label="成果", coverage="weak")
        db_session.add_all([a, b])
        db_session.flush()
        db_session.add(TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to"))
        db_session.flush()

        res = client.get(f"/topics/{topic.id}")
        assert res.status_code == 200
        body = res.json()
        assert {n["label"] for n in body["nodes"]} == {"手法", "成果"}
        assert body["edges"][0]["relation_type"] == "leads_to"

    def test_get_detail_not_found(self, client: TestClient) -> None:
        assert client.get("/topics/999999").status_code == 404

    def test_patch_topic(self, client: TestClient, user: User) -> None:
        created = client.post("/topics", json={"user_id": user.id, "title": "x"}).json()
        res = client.patch(f"/topics/{created['id']}", json={"status": "archived", "title": "研究内容"})
        assert res.status_code == 200
        assert res.json()["status"] == "archived"
        assert res.json()["title"] == "研究内容"

    def test_patch_invalid_status(self, client: TestClient, user: User) -> None:
        created = client.post("/topics", json={"user_id": user.id, "title": "x"}).json()
        res = client.patch(f"/topics/{created['id']}", json={"status": "bogus"})
        assert res.status_code == 400

    def test_patch_not_found(self, client: TestClient) -> None:
        assert client.patch("/topics/999999", json={"title": "x"}).status_code == 404

    def test_delete_topic(self, client: TestClient, user: User) -> None:
        created = client.post("/topics", json={"user_id": user.id, "title": "x"}).json()
        assert client.delete(f"/topics/{created['id']}").status_code == 204
        assert client.get(f"/topics/{created['id']}").status_code == 404

    def test_delete_not_found(self, client: TestClient) -> None:
        assert client.delete("/topics/999999").status_code == 404
