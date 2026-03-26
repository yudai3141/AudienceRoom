import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models.session_message import SessionMessage
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.session_participant_repository import SessionParticipantRepository
from app.services.ai.llm import get_llm_provider
from app.services.ai.tts_service import TTSService, VOICEVOX_SPEAKERS
from app.services.prompts.interview import build_interview_prompt
from app.services.prompts.presentation import build_presentation_prompt

logger = logging.getLogger(__name__)


@dataclass
class ConversationResponse:
    text: str
    audio_base64: str | None
    speaker_id: int | None
    participant_id: int | None


class ConversationService:
    """Service for managing AI conversations in practice sessions."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._session_repo = PracticeSessionRepository(db)
        self._message_repo = SessionMessageRepository(db)
        self._participant_repo = SessionParticipantRepository(db)
        self._llm = get_llm_provider()
        self._tts = TTSService()

    async def process_message(
        self,
        session_id: int,
        user_message: str,
        generate_audio: bool = True,
    ) -> ConversationResponse:
        """Process user message and generate AI response.

        Args:
            session_id: Practice session ID
            user_message: User's spoken message
            generate_audio: Whether to generate TTS audio

        Returns:
            ConversationResponse with AI response and optional audio

        Raises:
            ValueError: If session not found or not active
        """
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        if session.status != "active":
            raise ValueError(
                f"Session {session_id} is not active (status: {session.status})"
            )

        existing_messages = self._message_repo.list_by_session_id(session_id)
        next_seq = len(existing_messages) + 1

        user_msg = SessionMessage(
            session_id=session_id,
            participant_id=None,
            sequence_no=next_seq,
            content=user_message,
        )
        self._message_repo.create(user_msg)

        conversation_history = self._build_conversation_history(existing_messages)
        conversation_history.append({"role": "user", "content": user_message})

        participants = self._participant_repo.list_by_session_id(session_id)
        host_participant = next(
            (p for p in participants if p.role == "host"),
            participants[0] if participants else None,
        )

        ai_response = await self._generate_response(
            session=session,
            conversation_history=conversation_history,
            participant=host_participant,
        )

        ai_msg = SessionMessage(
            session_id=session_id,
            participant_id=host_participant.id if host_participant else None,
            sequence_no=next_seq + 1,
            content=ai_response,
        )
        self._message_repo.create(ai_msg)

        audio_base64 = None
        speaker_id = None

        if generate_audio:
            try:
                character_name = self._get_character_voice(host_participant)
                speaker_id = VOICEVOX_SPEAKERS.get(character_name, 3)
                tts_result = await self._tts.synthesize(
                    text=ai_response,
                    speaker_id=speaker_id,
                )
                audio_base64 = tts_result.audio_base64
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")

        return ConversationResponse(
            text=ai_response,
            audio_base64=audio_base64,
            speaker_id=speaker_id,
            participant_id=host_participant.id if host_participant else None,
        )

    async def start_conversation(
        self,
        session_id: int,
        generate_audio: bool = True,
    ) -> ConversationResponse:
        """Start a conversation by generating the AI's opening message.

        Args:
            session_id: Practice session ID
            generate_audio: Whether to generate TTS audio

        Returns:
            ConversationResponse with AI's opening message
        """
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        participants = self._participant_repo.list_by_session_id(session_id)
        host_participant = next(
            (p for p in participants if p.role == "host"),
            participants[0] if participants else None,
        )

        ai_response = await self._generate_response(
            session=session,
            conversation_history=[],
            participant=host_participant,
        )

        ai_msg = SessionMessage(
            session_id=session_id,
            participant_id=host_participant.id if host_participant else None,
            sequence_no=1,
            content=ai_response,
        )
        self._message_repo.create(ai_msg)

        audio_base64 = None
        speaker_id = None

        if generate_audio:
            try:
                character_name = self._get_character_voice(host_participant)
                speaker_id = VOICEVOX_SPEAKERS.get(character_name, 3)
                tts_result = await self._tts.synthesize(
                    text=ai_response,
                    speaker_id=speaker_id,
                )
                audio_base64 = tts_result.audio_base64
            except Exception as e:
                logger.warning(f"TTS generation failed: {e}")

        return ConversationResponse(
            text=ai_response,
            audio_base64=audio_base64,
            speaker_id=speaker_id,
            participant_id=host_participant.id if host_participant else None,
        )

    def _build_conversation_history(
        self, messages: list[SessionMessage]
    ) -> list[dict]:
        """Build conversation history from session messages."""
        history = []
        for msg in messages:
            role = "assistant" if msg.participant_id else "user"
            history.append({"role": role, "content": msg.content})
        return history

    async def _generate_response(
        self,
        session,
        conversation_history: list[dict],
        participant,
    ) -> str:
        """Generate AI response using LLM."""
        strictness = "normal"
        character_name = "面接官"

        if participant and participant.ai_character:
            strictness = participant.ai_character.strictness or "normal"
            character_name = participant.display_name or participant.ai_character.name

        if session.mode == "interview":
            prompt = build_interview_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
            )
        elif session.mode == "presentation":
            is_qa_phase = len(conversation_history) > 4
            prompt = build_presentation_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
                is_qa_phase=is_qa_phase,
            )
        else:
            prompt = build_interview_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
            )

        response = await self._llm.generate(prompt, temperature=0.8)
        return response.content

    def _get_character_voice(self, participant) -> str:
        """Get VOICEVOX character name for participant."""
        if participant and participant.ai_character:
            voice_style = participant.ai_character.voice_style
            if voice_style and voice_style in VOICEVOX_SPEAKERS:
                return voice_style
        return "ずんだもん"
