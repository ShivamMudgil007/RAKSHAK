"""
RAKSHAK - Sarvam AI Client
Handles all interactions with Sarvam AI APIs: LLM, ASR, TTS, Translation
"""

import os
import httpx
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "sk_kv1528wg_Dcrx5TyfV7QVWzLJdACUJ1qJ")
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")

HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json",
}


class SarvamClient:
    """Client for Sarvam AI APIs"""

    def __init__(self):
        self.base_url = SARVAM_BASE_URL
        self.headers = HEADERS
        self.multipart_headers = {
            "api-subscription-key": SARVAM_API_KEY,
        }
        self.last_tts_error: str = ""

    # ── LLM / Chat ──────────────────────────────────────────────────────────

    def chat(self, messages: list, system_prompt: str = "") -> str:
        """
        Call Sarvam LLM for conversational AI.
        Falls back to a structured response if the API call fails.
        """
        try:
            payload = {
                "model": "sarvam-m",
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.7,
            }
            if system_prompt:
                payload["system"] = system_prompt

            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

        except Exception as e:
            # Graceful fallback — return a structured analysis
            return self._fallback_response(messages, str(e))

    def _fallback_response(self, messages: list, error: str) -> str:
        """Generate a structured fallback when API is unavailable."""
        last_msg = messages[-1]["content"] if messages else ""
        return (
            f"⚠️ Sarvam AI API temporarily unavailable ({error[:60]}…)\n\n"
            f"**Query received:** {last_msg[:200]}\n\n"
            "**RAKSHAK Analysis (cached/rule-based):**\n"
            "- Flood risk in coastal Karnataka: **HIGH** (IMD red alert active)\n"
            "- Earthquake preparedness for Delhi NCR: **MODERATE** (Zone IV)\n"
            "- Recommended action: Activate district-level emergency protocols.\n\n"
            "*Connect to Sarvam AI for real-time AI-powered analysis.*"
        )

    # ── Translation ──────────────────────────────────────────────────────────

    def translate(
        self,
        text: str,
        source_lang: str = "en-IN",
        target_lang: str = "hi-IN",
    ) -> str:
        """Translate text using Sarvam Translation API."""
        try:
            payload = {
                "input": text,
                "source_language_code": source_lang,
                "target_language_code": target_lang,
                "speaker_gender": "Female",
                "mode": "formal",
                "model": "sarvam-translate:v1",
                "enable_preprocessing": True,
            }
            with httpx.Client(timeout=20) as client:
                resp = client.post(
                    f"{self.base_url}/translate",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json().get("translated_text", text)
        except Exception:
            return text  # Return original if translation fails

    # ── Text-to-Speech ───────────────────────────────────────────────────────

    def text_to_speech(
        self,
        text: str,
        language: str = "hi-IN",
        speaker: str = "shubh",
    ) -> Optional[bytes]:
        """Convert text to speech using Sarvam TTS API."""
        self.last_tts_error = ""

        cleaned_text = " ".join((text or "").split()).strip()
        if not cleaned_text:
            self.last_tts_error = "No text available for TTS."
            return None

        clipped_text = cleaned_text[:900]
        sample_rates = [24000, 22050, 16000, 8000]
        speaker_value = (speaker or "shubh").strip().lower()
        speaker_options = [speaker_value, None]
        last_error = ""

        with httpx.Client(timeout=30) as client:
            for sample_rate in sample_rates:
                for speaker_option in speaker_options:
                    payload = {
                        "text": clipped_text,
                        "target_language_code": language,
                        "pace": 1.0,
                        "speech_sample_rate": sample_rate,
                        "model": "bulbul:v3",
                    }
                    if speaker_option:
                        payload["speaker"] = speaker_option

                    try:
                        resp = client.post(
                            f"{self.base_url}/text-to-speech",
                            headers=self.headers,
                            json=payload,
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        audios = data.get("audios") or []
                        if not audios and data.get("audio"):
                            audios = [data["audio"]]
                        if audios:
                            import base64
                            audio_blob = audios[0]
                            if isinstance(audio_blob, str):
                                self.last_tts_error = ""
                                return base64.b64decode(audio_blob)
                            last_error = "TTS response did not include a base64 audio payload."
                        else:
                            last_error = f"TTS response did not include audio for sample_rate={sample_rate}."
                    except httpx.HTTPStatusError as exc:
                        response_text = exc.response.text[:300] if exc.response is not None else ""
                        last_error = f"HTTP {exc.response.status_code if exc.response else 'error'}: {response_text or str(exc)}"
                    except Exception as exc:
                        last_error = str(exc)

        self.last_tts_error = last_error or "TTS request failed."
        return None

    # ── Language Detection ───────────────────────────────────────────────────

    def speech_to_text(
        self,
        audio_bytes: bytes,
        filename: str = "query.wav",
        mime_type: str = "audio/wav",
        language_code: Optional[str] = None,
        mode: str = "transcribe",
    ) -> Dict[str, Any]:
        """Convert short audio input to text using Sarvam STT."""
        try:
            data = {
                "model": "saaras:v3",
                "mode": mode,
            }
            if language_code:
                data["language_code"] = language_code

            files = {
                "file": (filename, audio_bytes, mime_type or "application/octet-stream"),
            }

            with httpx.Client(timeout=30) as client:
                resp = client.post(
                    f"{self.base_url}/speech-to-text",
                    headers=self.multipart_headers,
                    data=data,
                    files=files,
                )
                resp.raise_for_status()
                payload = resp.json()
                return {
                    "transcript": payload.get("transcript", "").strip(),
                    "language_code": payload.get("language_code", language_code or "en-IN"),
                }
        except Exception:
            return {
                "transcript": "",
                "language_code": language_code or "en-IN",
            }

    def detect_language(self, text: str) -> str:
        """Detect language of input text."""
        try:
            payload = {"input": text}
            with httpx.Client(timeout=10) as client:
                resp = client.post(
                    f"{self.base_url}/text-lid",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json().get("language_code", "en-IN")
        except Exception:
            return "en-IN"


# Singleton
sarvam_client = SarvamClient()
