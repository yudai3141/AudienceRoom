import asyncio
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.session_message import SessionMessage
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.session_participant_repository import SessionParticipantRepository
from app.services.ai.llm import get_llm_provider
from app.services.ai.tts_service import VOICEVOX_SPEAKERS, TTSService
from app.services.prompts.interview import build_interview_prompt
from app.services.prompts.presentation import build_presentation_prompt

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    """ストリーミング会話用のServer-Sent Event"""

    event_type: str  # "metadata", "text_chunk", "audio_chunk", "complete", "error"
    data: dict


class StreamingConversationService:
    """練習セッションでのストリーミングAI会話を管理するサービス"""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._session_repo = PracticeSessionRepository(db)
        self._message_repo = SessionMessageRepository(db)
        self._participant_repo = SessionParticipantRepository(db)
        self._llm = get_llm_provider()
        self._tts = TTSService()

    async def process_message_stream(
        self,
        session_id: int,
        user_message: str,
        generate_audio: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """ユーザーメッセージを処理し、AI応答を音声付きでストリーミング配信する

        Args:
            session_id: 練習セッションID
            user_message: ユーザーの発話メッセージ
            generate_audio: TTS音声を生成するか

        Yields:
            StreamEvent: ストリームイベント (metadata, text_chunk, audio_chunk, complete, error)

        Raises:
            ValueError: セッションが見つからないまたはアクティブでない場合
        """
        try:
            # セッション検証
            session = self._session_repo.get_by_id(session_id)
            if session is None:
                yield StreamEvent(
                    event_type="error",
                    data={"message": f"Session {session_id} not found"},
                )
                return

            if session.status != "active":
                yield StreamEvent(
                    event_type="error",
                    data={
                        "message": f"Session {session_id} is not active (status: {session.status})"
                    },
                )
                return

            # ユーザーメッセージを保存
            existing_messages = self._message_repo.list_by_session_id(session_id)
            next_seq = len(existing_messages) + 1

            user_msg = SessionMessage(
                session_id=session_id,
                participant_id=None,
                sequence_no=next_seq,
                content=user_message,
            )
            self._message_repo.create(user_msg)

            # 会話履歴を構築
            conversation_history = self._build_conversation_history(existing_messages)
            conversation_history.append({"role": "user", "content": user_message})

            # 発話者を選択
            participants = self._participant_repo.list_by_session_id(session_id)
            speaker = self._pick_random_participant(participants)

            # メタデータを送信
            yield StreamEvent(
                event_type="metadata",
                data={
                    "participant_id": speaker.id if speaker else None,
                    "speaker_id": self._get_speaker_id(speaker),
                },
            )

            # LLM応答をTTS付きでストリーミング
            full_text = ""
            audio_sequence_count = 0

            if generate_audio:
                async for event in self._stream_with_tts(
                    session=session,
                    conversation_history=conversation_history,
                    speaker=speaker,
                ):
                    if event.event_type == "text_chunk":
                        full_text += event.data["text"]
                    elif event.event_type == "audio_chunk":
                        audio_sequence_count += 1
                    yield event
            else:
                async for event in self._stream_text_only(
                    session=session,
                    conversation_history=conversation_history,
                    speaker=speaker,
                ):
                    full_text += event.data["text"]
                    yield event

            # AIメッセージを保存
            ai_msg = SessionMessage(
                session_id=session_id,
                participant_id=speaker.id if speaker else None,
                sequence_no=next_seq + 1,
                content=full_text,
            )
            self._message_repo.create(ai_msg)

            # 完了イベントを送信
            yield StreamEvent(
                event_type="complete",
                data={"text": full_text, "audio_sequence_count": audio_sequence_count},
            )

        except Exception as e:
            logger.exception(f"Error in streaming conversation: {e}")
            yield StreamEvent(event_type="error", data={"message": str(e)})

    async def start_conversation_stream(
        self,
        session_id: int,
        generate_audio: bool = True,
    ) -> AsyncIterator[StreamEvent]:
        """会話を開始し、AIの開始メッセージをストリーミング配信する

        Args:
            session_id: 練習セッションID
            generate_audio: TTS音声を生成するか

        Yields:
            StreamEvent: ストリームイベント
        """
        try:
            session = self._session_repo.get_by_id(session_id)
            if session is None:
                yield StreamEvent(
                    event_type="error",
                    data={"message": f"Session {session_id} not found"},
                )
                return

            # 待機中の場合はセッションをアクティブ化
            if session.status == "waiting":
                session.status = "active"
                session.started_at = datetime.now(timezone.utc)
                self._db.commit()

            participants = self._participant_repo.list_by_session_id(session_id)
            speaker = self._pick_random_participant(participants)

            # メタデータを送信
            yield StreamEvent(
                event_type="metadata",
                data={
                    "participant_id": speaker.id if speaker else None,
                    "speaker_id": self._get_speaker_id(speaker),
                },
            )

            start_message = (
                "プレゼンを始めてください。"
                if session.mode == "presentation"
                else "面接を始めてください。"
            )

            conversation_history = [{"role": "user", "content": start_message}]

            full_text = ""
            audio_sequence_count = 0

            if generate_audio:
                async for event in self._stream_with_tts(
                    session=session,
                    conversation_history=conversation_history,
                    speaker=speaker,
                ):
                    if event.event_type == "text_chunk":
                        full_text += event.data["text"]
                    elif event.event_type == "audio_chunk":
                        audio_sequence_count += 1
                    yield event
            else:
                async for event in self._stream_text_only(
                    session=session,
                    conversation_history=conversation_history,
                    speaker=speaker,
                ):
                    full_text += event.data["text"]
                    yield event

            # AIメッセージを保存
            ai_msg = SessionMessage(
                session_id=session_id,
                participant_id=speaker.id if speaker else None,
                sequence_no=1,
                content=full_text,
            )
            self._message_repo.create(ai_msg)

            yield StreamEvent(
                event_type="complete",
                data={"text": full_text, "audio_sequence_count": audio_sequence_count},
            )

        except Exception as e:
            logger.exception(f"Error in start conversation stream: {e}")
            yield StreamEvent(event_type="error", data={"message": str(e)})

    async def _stream_text_only(
        self,
        session,
        conversation_history: list[dict],
        speaker,
    ) -> AsyncIterator[StreamEvent]:
        """音声なしでLLM応答をストリーミング配信する"""
        prompt = self._build_prompt(session, conversation_history, speaker)

        async for chunk in self._llm.generate_stream(prompt, temperature=0.8):
            if chunk.content:
                yield StreamEvent(event_type="text_chunk", data={"text": chunk.content})

    async def _stream_with_tts(
        self,
        session,
        conversation_history: list[dict],
        speaker,
    ) -> AsyncIterator[StreamEvent]:
        """TTS生成付きでLLM応答をストリーミング配信する"""
        event_queue: asyncio.Queue[StreamEvent | None] = asyncio.Queue()
        prompt = self._build_prompt(session, conversation_history, speaker)
        speaker_id = self._get_speaker_id(speaker)

        async def llm_and_tts_task():
            """LLMストリーミングとTTS生成のバックグラウンドタスク"""
            try:
                accumulated_text = ""
                sentence_buffer = ""
                audio_sequence = 0

                async for chunk in self._llm.generate_stream(prompt, temperature=0.8):
                    if chunk.content:
                        # テキストチャンクを即座に送信
                        await event_queue.put(
                            StreamEvent(event_type="text_chunk", data={"text": chunk.content})
                        )

                        accumulated_text += chunk.content
                        sentence_buffer += chunk.content

                        # 完全な文を抽出
                        sentences = self._extract_sentences(sentence_buffer)
                        if sentences:
                            for sentence in sentences[:-1]:  # 最後（未完成）を除く全て
                                if sentence.strip():
                                    # この文に対してTTSを生成
                                    try:
                                        tts_result = await self._tts.synthesize(
                                            text=sentence.strip(),
                                            speaker_id=speaker_id,
                                            speed_scale=1.3,
                                        )
                                        audio_sequence += 1
                                        await event_queue.put(
                                            StreamEvent(
                                                event_type="audio_chunk",
                                                data={
                                                    "audio_base64": tts_result.audio_base64,
                                                    "sequence": audio_sequence,
                                                    "text": sentence.strip(),
                                                },
                                            )
                                        )
                                    except Exception as e:
                                        logger.warning(f"TTS generation failed for sentence: {e}")

                            # 未完成の文をバッファに保持
                            sentence_buffer = sentences[-1]

                # 残りのテキストを処理
                if sentence_buffer.strip():
                    try:
                        tts_result = await self._tts.synthesize(
                            text=sentence_buffer.strip(),
                            speaker_id=speaker_id,
                            speed_scale=1.3,
                        )
                        audio_sequence += 1
                        await event_queue.put(
                            StreamEvent(
                                event_type="audio_chunk",
                                data={
                                    "audio_base64": tts_result.audio_base64,
                                    "sequence": audio_sequence,
                                    "text": sentence_buffer.strip(),
                                },
                            )
                        )
                    except Exception as e:
                        logger.warning(f"TTS generation failed for final text: {e}")

            except Exception as e:
                logger.exception(f"Error in LLM/TTS task: {e}")
                await event_queue.put(
                    StreamEvent(event_type="error", data={"message": str(e)})
                )
            finally:
                await event_queue.put(None)  # 終了マーカー

        # バックグラウンドタスクを開始
        task = asyncio.create_task(llm_and_tts_task())

        try:
            # キューからイベントを yield
            while True:
                event = await event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            # タスクの完了を保証
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    def _extract_sentences(self, text: str) -> list[str]:
        """日本語テキストから文を抽出する

        文末記号で分割: 。！？!?
        区切り文字を含む文のリストを返す
        """
        # 区切り文字を保持しながら日本語/英語の文末で分割
        parts = re.split(r"([。！？!?])", text)

        sentences = []
        for i in range(0, len(parts) - 1, 2):
            if i + 1 < len(parts):
                sentences.append(parts[i] + parts[i + 1])
            else:
                sentences.append(parts[i])

        # 残りのテキストがあれば追加
        if len(parts) % 2 == 1 and parts[-1]:
            sentences.append(parts[-1])

        return sentences

    def _build_prompt(self, session, conversation_history: list[dict], participant):
        """セッションモードに基づいてLLMプロンプトを構築する"""
        strictness = "normal"
        character_name = "面接官"

        if participant and participant.ai_character:
            strictness = participant.ai_character.strictness or "normal"
            character_name = participant.display_name or participant.ai_character.name

        if session.mode == "interview":
            return build_interview_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
            )
        elif session.mode == "presentation":
            is_qa_phase = len(conversation_history) > 4
            return build_presentation_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
                is_qa_phase=is_qa_phase,
            )
        else:
            # デフォルトは面接モード
            return build_interview_prompt(
                theme=session.theme,
                user_goal=session.user_goal,
                user_concerns=session.user_concerns,
                strictness=strictness,
                character_name=character_name,
                conversation_history=conversation_history,
            )

    def _pick_random_participant(self, participants):
        """リストからランダムに参加者を選択する"""
        if not participants:
            return None
        import random

        return random.choice(participants)

    def _build_conversation_history(
        self, messages: list[SessionMessage]
    ) -> list[dict]:
        """セッションメッセージから会話履歴を構築する"""
        history = []
        for msg in messages:
            role = "assistant" if msg.participant_id else "user"
            history.append({"role": role, "content": msg.content})
        return history

    def _get_speaker_id(self, participant) -> int:
        """参加者のVOICEVOX話者IDを取得する"""
        if participant and participant.ai_character:
            voice_style = participant.ai_character.voice_style
            if voice_style and voice_style in VOICEVOX_SPEAKERS:
                return VOICEVOX_SPEAKERS[voice_style]
        return VOICEVOX_SPEAKERS["ずんだもん"]
