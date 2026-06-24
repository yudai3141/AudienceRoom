"""Topic 系リポジトリのテスト (Plan B Phase B-1)。"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.topic import Topic
from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.repositories.topic_edge_repository import TopicEdgeRepository
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository


def _create_user(db: Session, suffix: str = "") -> User:
    user = User(
        firebase_uid=f"topic_repo_user{suffix}",
        email=f"topic_repo{suffix}@example.com",
        display_name="Topic Repo User",
    )
    db.add(user)
    db.flush()
    return user


def _make_node(topic_id: int, label: str, coverage: str = "gap", order: int = 0) -> TopicNode:
    return TopicNode(topic_id=topic_id, label=label, coverage=coverage, sort_order=order)


class TestTopicRepository:
    def test_create_and_get(self, db: Session) -> None:
        user = _create_user(db)
        repo = TopicRepository(db)
        created = repo.create(Topic(user_id=user.id, title="研究内容"))

        assert created.id is not None
        found = repo.get_by_id(created.id)
        assert found is not None and found.title == "研究内容"

    def test_get_by_id_not_found(self, db: Session) -> None:
        assert TopicRepository(db).get_by_id(999999) is None

    def test_soft_deleted_excluded(self, db: Session) -> None:
        user = _create_user(db)
        repo = TopicRepository(db)
        topic = repo.create(Topic(user_id=user.id, title="x"))
        topic.deleted_at = datetime.now(timezone.utc)
        repo.update(topic)
        assert repo.get_by_id(topic.id) is None

    def test_list_by_user_id(self, db: Session) -> None:
        user = _create_user(db)
        repo = TopicRepository(db)
        repo.create(Topic(user_id=user.id, title="A"))
        repo.create(Topic(user_id=user.id, title="B"))
        topics = repo.list_by_user_id(user.id)
        assert {t.title for t in topics} == {"A", "B"}

    def test_update_completeness(self, db: Session) -> None:
        user = _create_user(db)
        repo = TopicRepository(db)
        topic = repo.create(Topic(user_id=user.id, title="x"))
        topic.completeness_score = 65
        topic.current_summary = "設計意図は説明できている"
        updated = repo.update(topic)
        assert updated.completeness_score == 65
        assert updated.current_summary == "設計意図は説明できている"


class TestTopicNodeRepository:
    def test_bulk_create_and_list_ordered(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        repo = TopicNodeRepository(db)
        repo.bulk_create([
            _make_node(topic.id, "second", order=2),
            _make_node(topic.id, "first", order=1),
        ])
        nodes = repo.list_by_topic_id(topic.id)
        assert [n.label for n in nodes] == ["first", "second"]

    def test_count_weak(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        repo = TopicNodeRepository(db)
        repo.bulk_create([
            _make_node(topic.id, "covered", coverage="covered"),
            _make_node(topic.id, "weak", coverage="weak"),
            _make_node(topic.id, "gap", coverage="gap"),
        ])
        assert repo.count_weak_by_topic_id(topic.id) == 2

    def test_candidate_nodes_include_weak_and_contradictions(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        node_repo = TopicNodeRepository(db)
        edge_repo = TopicEdgeRepository(db)

        covered_in_conflict = node_repo.create(_make_node(topic.id, "主導した", coverage="covered"))
        covered_other = node_repo.create(_make_node(topic.id, "チームで決めた", coverage="covered"))
        weak = node_repo.create(_make_node(topic.id, "評価方法", coverage="weak"))
        calm_covered = node_repo.create(_make_node(topic.id, "研究テーマ", coverage="covered"))

        edge_repo.create(TopicEdge(
            topic_id=topic.id,
            source_node_id=covered_in_conflict.id,
            target_node_id=covered_other.id,
            relation_type="contradicts",
        ))

        labels = {n.label for n in node_repo.list_candidate_nodes(topic.id)}
        # 弱点 + 矛盾に関与する covered ノードは候補に含まれる
        assert "評価方法" in labels
        assert "主導した" in labels
        assert "チームで決めた" in labels
        # 矛盾と無関係な covered ノードは含まれない
        assert "研究テーマ" not in labels

    def test_update_coverage(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        repo = TopicNodeRepository(db)
        node = repo.create(_make_node(topic.id, "x", coverage="weak"))
        node.coverage = "covered"
        assert repo.update(node).coverage == "covered"


class TestTopicEdgeRepository:
    def test_list_by_topic_and_node(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        node_repo = TopicNodeRepository(db)
        edge_repo = TopicEdgeRepository(db)
        a = node_repo.create(_make_node(topic.id, "手法"))
        b = node_repo.create(_make_node(topic.id, "成果"))
        c = node_repo.create(_make_node(topic.id, "学び"))
        edge_repo.create(TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to"))
        edge_repo.create(TopicEdge(topic_id=topic.id, source_node_id=b.id, target_node_id=c.id, relation_type="leads_to"))

        assert len(edge_repo.list_by_topic_id(topic.id)) == 2
        # b は 2 本のエッジに登場する
        assert len(edge_repo.list_by_node_id(b.id)) == 2
        assert len(edge_repo.list_by_node_id(a.id)) == 1

    def test_find_existing_edge(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicRepository(db).create(Topic(user_id=user.id, title="t"))
        node_repo = TopicNodeRepository(db)
        edge_repo = TopicEdgeRepository(db)
        a = node_repo.create(_make_node(topic.id, "a"))
        b = node_repo.create(_make_node(topic.id, "b"))
        edge_repo.create(TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to"))

        assert edge_repo.find(a.id, b.id, "leads_to") is not None
        assert edge_repo.find(a.id, b.id, "contradicts") is None
