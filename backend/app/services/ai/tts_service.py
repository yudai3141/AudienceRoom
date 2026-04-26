import base64
import logging
from dataclasses import dataclass

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


VOICEVOX_SPEAKERS = {
    "ずんだもん": 3,
    "四国めたん": 2,
    "春日部つむぎ": 8,
    "雨晴はう": 10,
    "波音リツ": 9,
    "玄野武宏": 11,
    "白上虎太郎": 12,
    "青山龍星": 13,
    "冥鳴ひまり": 14,
    "九州そら": 16,
}


@dataclass
class TTSResult:
    audio_data: bytes
    audio_base64: str
    speaker_id: int


class TTSService:
    """Text-to-Speech service using VOICEVOX."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        self.host = host or settings.VOICEVOX_HOST
        self.port = port or settings.VOICEVOX_PORT
        scheme = "https" if self.port == 443 else "http"
        if self.port in (80, 443):
            self.base_url = f"{scheme}://{self.host}"
        else:
            self.base_url = f"{scheme}://{self.host}:{self.port}"

    async def synthesize(
        self,
        text: str,
        speaker_id: int = 3,
        speed_scale: float = 1.0,
        pitch_scale: float = 0.0,
    ) -> TTSResult:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            speaker_id: VOICEVOX speaker ID
            speed_scale: Speech speed (0.5 - 2.0)
            pitch_scale: Pitch adjustment (-0.15 - 0.15)

        Returns:
            TTSResult with audio data

        Raises:
            ValueError: If synthesis fails
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            query_response = await client.post(
                f"{self.base_url}/audio_query",
                params={"text": text, "speaker": speaker_id},
            )

            if query_response.status_code != 200:
                logger.error(f"VOICEVOX audio_query failed: {query_response.text}")
                raise ValueError(f"Failed to create audio query: {query_response.text}")

            query = query_response.json()
            query["speedScale"] = speed_scale
            query["pitchScale"] = pitch_scale

            synthesis_response = await client.post(
                f"{self.base_url}/synthesis",
                params={"speaker": speaker_id},
                json=query,
            )

            if synthesis_response.status_code != 200:
                logger.error(f"VOICEVOX synthesis failed: {synthesis_response.text}")
                raise ValueError(f"Failed to synthesize audio: {synthesis_response.text}")

            audio_data = synthesis_response.content
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            return TTSResult(
                audio_data=audio_data,
                audio_base64=audio_base64,
                speaker_id=speaker_id,
            )

    async def synthesize_by_character(
        self,
        text: str,
        character_name: str,
        speed_scale: float = 1.0,
    ) -> TTSResult:
        """Synthesize speech using character name.

        Args:
            text: Text to synthesize
            character_name: VOICEVOX character name
            speed_scale: Speech speed

        Returns:
            TTSResult with audio data
        """
        speaker_id = VOICEVOX_SPEAKERS.get(character_name, 3)
        return await self.synthesize(text, speaker_id=speaker_id, speed_scale=speed_scale)

    async def get_speakers(self) -> list[dict]:
        """Get list of available speakers.

        Returns:
            List of speaker info dictionaries
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/speakers")
            if response.status_code != 200:
                raise ValueError(f"Failed to get speakers: {response.text}")
            return response.json()

    async def health_check(self) -> bool:
        """Check if VOICEVOX service is available.

        Returns:
            True if service is available
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/version")
                return response.status_code == 200
        except Exception:
            return False
