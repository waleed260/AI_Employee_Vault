import os
import json
import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional, BinaryIO
from datetime import datetime

logger = logging.getLogger("VoiceService")

LANGUAGES = {
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "es-ES": "Spanish",
    "fr-FR": "French",
    "de-DE": "German",
    "it-IT": "Italian",
    "pt-BR": "Portuguese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
    "ar-SA": "Arabic",
    "hi-IN": "Hindi",
    "ru-RU": "Russian",
    "nl-NL": "Dutch",
    "pl-PL": "Polish",
    "tr-TR": "Turkish",
    "vi-VN": "Vietnamese",
    "th-TH": "Thai",
    "id-ID": "Indonesian",
    "ms-MY": "Malay",
}

TONES = [
    "neutral",
    "happy",
    "sad",
    "excited",
    "calm",
    "authoritative",
    "friendly",
    "apologetic",
]

ACCENTS = [
    "american",
    "british",
    "australian",
    "canadian",
    "indian",
    "irish",
    "scottish",
    "south-african",
]

VOICE_PROFILES = {
    "default_male": {"age": "adult", "gender": "male"},
    "default_female": {"age": "adult", "gender": "female"},
    "young_male": {"age": "young_adult", "gender": "male"},
    "young_female": {"age": "young_adult", "gender": "female"},
    "senior_male": {"age": "senior", "gender": "male"},
    "senior_female": {"age": "senior", "gender": "female"},
}


class VoiceService:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.voice_dir = self.vault_path / "Voice"
        self.voice_dir.mkdir(exist_ok=True)

        self.conversations_dir = self.voice_dir / "Conversations"
        self.conversations_dir.mkdir(exist_ok=True)

        self.voice_profiles_dir = self.voice_dir / "Profiles"
        self.voice_profiles_dir.mkdir(exist_ok=True)

        self.current_language = "en-US"
        self.current_tone = "neutral"
        self.current_accent = "american"
        self.current_profile = "default_female"

        self.conversation_history: List[Dict] = []
        self.max_history = 10000

        logger.info("VoiceService initialized - Silver Tier")

    def speak(
        self,
        text: str,
        language: str = None,
        tone: str = None,
        accent: str = None,
        profile: str = None,
    ) -> Dict:
        language = language or self.current_language
        tone = tone or self.current_tone
        accent = accent or self.current_accent
        profile = profile or self.current_profile

        logger.info(f"Speaking: {text[:50]}... | Lang: {language} | Tone: {tone}")

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "speak",
            "text": text,
            "language": language,
            "tone": tone,
            "accent": accent,
            "profile": profile,
        }

        self._add_to_history(entry)
        self._save_conversation_entry(entry)

        return {
            "status": "success",
            "text": text,
            "language": language,
            "tone": tone,
            "accent": accent,
            "profile": profile,
            "audio_format": "mp3",
        }

    def listen(self, audio_data: BinaryIO = None, language: str = None) -> Dict:
        language = language or self.current_language

        logger.info(f"Listening | Language: {language}")

        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "listen",
            "language": language,
            "audio_received": audio_data is not None,
        }

        self._add_to_history(entry)

        return {
            "status": "success",
            "language": language,
            "transcription": "Sample transcribed text",
            "confidence": 0.95,
        }

    def two_way_conversation(self, user_input: str) -> Dict:
        logger.info(f"Two-way conversation: {user_input[:50]}...")

        listen_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "listen",
            "text": user_input,
            "language": self.current_language,
        }
        self._add_to_history(listen_entry)

        response_text = self._generate_response(user_input)

        speak_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "speak",
            "text": response_text,
            "language": self.current_language,
            "tone": self.current_tone,
            "accent": self.current_accent,
        }
        self._add_to_history(speak_entry)
        self._save_conversation_entry(speak_entry)

        return {
            "status": "success",
            "user_input": user_input,
            "response": response_text,
            "language": self.current_language,
            "tone": self.current_tone,
            "conversation_turns": len(self.conversation_history) // 2,
        }

    def _generate_response(self, user_input: str) -> str:
        return f"Understood: {user_input[:30]}... Processing request."

    def set_language(self, language: str) -> Dict:
        if language not in LANGUAGES:
            return {"status": "error", "message": f"Unsupported language: {language}"}

        old_language = self.current_language
        self.current_language = language

        logger.info(f"Language changed: {old_language} -> {language}")

        return {
            "status": "success",
            "old_language": old_language,
            "new_language": language,
            "language_name": LANGUAGES[language],
        }

    def set_tone(self, tone: str) -> Dict:
        if tone not in TONES:
            return {"status": "error", "message": f"Unsupported tone: {tone}"}

        old_tone = self.current_tone
        self.current_tone = tone

        logger.info(f"Tone changed: {old_tone} -> {tone}")

        return {
            "status": "success",
            "old_tone": old_tone,
            "new_tone": tone,
        }

    def set_accent(self, accent: str) -> Dict:
        if accent not in ACCENTS:
            return {"status": "error", "message": f"Unsupported accent: {accent}"}

        old_accent = self.current_accent
        self.current_accent = accent

        logger.info(f"Accent changed: {old_accent} -> {accent}")

        return {
            "status": "success",
            "old_accent": old_accent,
            "new_accent": accent,
        }

    def set_voice_profile(
        self, profile: str, age: str = None, gender: str = None
    ) -> Dict:
        if profile not in VOICE_PROFILES and profile != "custom":
            return {"status": "error", "message": f"Unknown profile: {profile}"}

        old_profile = self.current_profile
        self.current_profile = profile

        if age:
            VOICE_PROFILES["custom"] = {"age": age, "gender": gender or "neutral"}

        logger.info(f"Voice profile changed: {old_profile} -> {profile}")

        return {
            "status": "success",
            "old_profile": old_profile,
            "new_profile": profile,
            "details": VOICE_PROFILES.get(profile, {}),
        }

    def clone_voice(self, audio_samples: List[BinaryIO], voice_name: str) -> Dict:
        logger.info(f"Cloning voice: {voice_name}")

        profile_path = self.voice_profiles_dir / f"{voice_name}.json"
        profile_data = {
            "name": voice_name,
            "created": datetime.now().isoformat(),
            "samples_count": len(audio_samples),
            "status": "ready",
        }

        profile_path.write_text(json.dumps(profile_data, indent=2))

        return {
            "status": "success",
            "voice_name": voice_name,
            "profile_path": str(profile_path),
        }

    def get_available_languages(self) -> List[Dict]:
        return [{"code": code, "name": name} for code, name in LANGUAGES.items()]

    def get_available_tones(self) -> List[str]:
        return TONES

    def get_available_accents(self) -> List[str]:
        return ACCENTS

    def get_available_profiles(self) -> List[Dict]:
        profiles = []
        for name, details in VOICE_PROFILES.items():
            profiles.append({"name": name, **details})
        return profiles

    def get_conversation_history(self, limit: int = 50) -> List[Dict]:
        return self.conversation_history[-limit:]

    def clear_conversation_history(self) -> Dict:
        count = len(self.conversation_history)
        self.conversation_history = []

        conversation_file = (
            self.conversations_dir
            / f"conversation_{datetime.now().strftime('%Y%m%d')}.json"
        )
        conversation_file.write_text(json.dumps([], indent=2))

        logger.info(f"Cleared {count} conversation entries")

        return {
            "status": "success",
            "cleared_count": count,
        }

    def _add_to_history(self, entry: Dict):
        self.conversation_history.append(entry)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history :]

    def _save_conversation_entry(self, entry: Dict):
        date_str = datetime.now().strftime("%Y%m%d")
        conversation_file = self.conversations_dir / f"conversation_{date_str}.json"

        existing = []
        if conversation_file.exists():
            existing = json.loads(conversation_file.read_text())

        existing.append(entry)
        conversation_file.write_text(json.dumps(existing, indent=2))

    def get_voice_settings(self) -> Dict:
        return {
            "language": self.current_language,
            "language_name": LANGUAGES.get(self.current_language, "Unknown"),
            "tone": self.current_tone,
            "accent": self.current_accent,
            "profile": self.current_profile,
            "profile_details": VOICE_PROFILES.get(self.current_profile, {}),
            "conversation_turns": len(self.conversation_history) // 2,
        }
