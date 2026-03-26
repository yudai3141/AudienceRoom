import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.feedback_metric import FeedbackMetric
from app.db.models.practice_session import PracticeSession
from app.db.models.session_feedback import SessionFeedback
from app.repositories.feedback_metric_repository import FeedbackMetricRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_feedback_repository import SessionFeedbackRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.services.ai.llm import get_llm_provider
from app.services.prompts.feedback import build_feedback_prompt

logger = logging.getLogger(__name__)


@dataclass
class FeedbackResult:
    feedback: SessionFeedback
    metrics: list[FeedbackMetric]
    overall_score: int


class FeedbackGenerator:
    """Service for generating AI feedback for practice sessions."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._session_repo = PracticeSessionRepository(db)
        self._message_repo = SessionMessageRepository(db)
        self._feedback_repo = SessionFeedbackRepository(db)
        self._metric_repo = FeedbackMetricRepository(db)
        self._llm = get_llm_provider()

    async def generate_feedback(self, session_id: int) -> FeedbackResult:
        """Generate feedback for a completed practice session.

        Args:
            session_id: ID of the practice session

        Returns:
            FeedbackResult containing feedback, metrics, and overall score

        Raises:
            ValueError: If session not found, not completed, or feedback exists
        """
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        if session.status != "completed":
            raise ValueError(
                f"Session {session_id} is not completed (status: {session.status})"
            )

        existing_feedback = self._feedback_repo.get_by_session_id(session_id)
        if existing_feedback is not None:
            raise ValueError(f"Feedback for session {session_id} already exists")

        messages = self._message_repo.list_by_session_id(session_id)
        if not messages:
            raise ValueError(f"No messages found for session {session_id}")

        conversation_log = self._build_conversation_log(session, messages)
        feedback_data = await self._call_llm(session, conversation_log)

        return self._save_feedback(session, feedback_data)

    def _build_conversation_log(
        self, session: PracticeSession, messages: list
    ) -> list[dict]:
        """Build conversation log from session messages."""
        conversation = []
        for msg in messages:
            role = "assistant" if msg.participant_id else "user"
            conversation.append({"role": role, "content": msg.content})
        return conversation

    async def _call_llm(
        self, session: PracticeSession, conversation_log: list[dict]
    ) -> dict:
        """Call LLM to generate feedback."""
        prompt = build_feedback_prompt(
            mode=session.mode,
            theme=session.theme,
            user_goal=session.user_goal,
            user_concerns=session.user_concerns,
            conversation_log=conversation_log,
        )

        try:
            response = await self._llm.generate_json(prompt, temperature=0.7)
            return self._validate_feedback_response(response)
        except Exception as e:
            logger.error(f"LLM feedback generation failed: {e}")
            raise ValueError(f"Failed to generate feedback: {e}") from e

    def _validate_feedback_response(self, response: dict) -> dict:
        """Validate and normalize LLM response."""
        required_fields = [
            "summary_title",
            "positive_points",
            "improvement_points",
            "overall_score",
        ]
        for field in required_fields:
            if field not in response:
                raise ValueError(f"Missing required field: {field}")

        score = response.get("overall_score", 50)
        if not isinstance(score, int):
            score = int(score)
        response["overall_score"] = max(0, min(100, score))

        if not isinstance(response.get("positive_points"), list):
            response["positive_points"] = [response.get("positive_points", "")]

        if not isinstance(response.get("improvement_points"), list):
            response["improvement_points"] = [response.get("improvement_points", "")]

        return response

    def _save_feedback(
        self, session: PracticeSession, feedback_data: dict
    ) -> FeedbackResult:
        """Save feedback and metrics to database."""
        feedback = SessionFeedback(
            session_id=session.id,
            user_id=session.user_id,
            summary_title=feedback_data["summary_title"],
            short_comment=feedback_data.get("short_comment"),
            positive_points=feedback_data["positive_points"],
            improvement_points=feedback_data["improvement_points"],
            closing_message=feedback_data.get("closing_message"),
        )
        feedback = self._feedback_repo.create(feedback)

        metrics = []
        for metric_data in feedback_data.get("metrics", []):
            metric = FeedbackMetric(
                feedback_id=feedback.id,
                metric_key=metric_data.get("key", "unknown"),
                metric_value=metric_data.get("value", 0),
                metric_label=metric_data.get("label"),
                metric_unit=metric_data.get("unit"),
            )
            metric = self._metric_repo.create(metric)
            metrics.append(metric)

        overall_score = feedback_data["overall_score"]
        session.overall_score = overall_score
        session.feedback_summary = feedback_data.get("short_comment")
        self._session_repo.update(session)

        return FeedbackResult(
            feedback=feedback,
            metrics=metrics,
            overall_score=overall_score,
        )
