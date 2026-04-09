"""Intelligent Universal Summarizer - Works for all content types"""

import os
import re
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables automatically
load_dotenv()

LANGUAGE_LABELS = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "ur": "Urdu",
}

OPENAI_MODEL = "gpt-4o-mini"
GROQ_MODEL = "llama-3.1-8b-instant"

SCRIPT_RULES = {
    "en": "Use only English written in the Latin script.",
    "hi": "Use only Hindi written in Devanagari script. Never use Urdu or Perso-Arabic script.",
    "mr": "Use only Marathi written in Devanagari script.",
    "ta": "Use only Tamil written in Tamil script.",
    "ur": "Use only Urdu written in Perso-Arabic script.",
}

TARGET_LANGUAGE_RULES = {
    "en": "Return only English.",
    "hi": "Return only Hindi in Devanagari script. Never use Urdu or Perso-Arabic script.",
    "mr": "Return only Marathi in Devanagari script.",
    "ta": "Return only Tamil in Tamil script. Never use English except unavoidable proper nouns.",
    "ur": "Return only Urdu in Perso-Arabic script.",
}


class SummaryEngine:
    def __init__(self, api_key=None):
        groq_api_key = os.getenv("GROQ_API_KEY")
        openai_api_key = api_key or os.getenv("OPENAI_API_KEY")

        self.provider = "local"
        self.model_name = OPENAI_MODEL

        if groq_api_key:
            self.api_key = groq_api_key
            self.provider = "groq"
            self.model_name = os.getenv("GROQ_MODEL", GROQ_MODEL)
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.groq.com/openai/v1",
            )
            self.use_ai = True
            print("Using Groq API for intelligent summaries")
        elif openai_api_key:
            self.api_key = openai_api_key
            self.provider = "openai"
            self.model_name = os.getenv("OPENAI_MODEL", OPENAI_MODEL)
            self.client = OpenAI(api_key=self.api_key)
            self.use_ai = True
            print("Using OpenAI API for intelligent summaries")
        else:
            self.api_key = None
            self.client = None
            self.use_ai = False
            print("Using local summarizer (add OPENAI_API_KEY to .env for AI)")

    def generate_summary(
        self, text: str, style: str = "detailed", target_language: str = "en"
    ) -> Dict:
        """Generate summary and keep it in the target language."""
        if self.use_ai:
            return self._ai_smart_summary(text, style, target_language)
        return self._with_metadata(
            self._local_smart_summary(text, style, target_language),
            ai_used=False,
            fallback_reason="AI provider unavailable",
        )

    def _with_metadata(
        self,
        result: Dict,
        ai_used: bool,
        fallback_reason: str = "",
    ) -> Dict:
        result["ai_provider"] = self.provider
        result["ai_model"] = self.model_name
        result["ai_used"] = ai_used
        result["fallback_reason"] = fallback_reason
        return result

    def _contains_arabic_script(self, text: str) -> bool:
        return bool(re.search(r"[\u0600-\u06FF]", text))

    def _contains_devanagari_script(self, text: str) -> bool:
        return bool(re.search(r"[\u0900-\u097F]", text))

    def _contains_tamil_script(self, text: str) -> bool:
        return bool(re.search(r"[\u0B80-\u0BFF]", text))

    def _contains_latin_script(self, text: str) -> bool:
        return bool(re.search(r"[A-Za-z]", text))

    def _enforce_target_script(self, text: str, target_language: str) -> str:
        if not text or not self.use_ai:
            return text

        needs_fix = False
        if target_language == "hi" and self._contains_arabic_script(text):
            needs_fix = True
        elif target_language == "mr" and self._contains_arabic_script(text):
            needs_fix = True
        elif target_language == "ta" and self._contains_latin_script(text):
            needs_fix = True
        elif target_language == "ur" and self._contains_devanagari_script(text):
            needs_fix = True

        if not needs_fix:
            return text

        target_language_name = LANGUAGE_LABELS.get(target_language, "English")
        script_rule = SCRIPT_RULES.get(target_language, "")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the text in the correct target script without changing meaning. "
                            f"Return only {target_language_name}. {script_rule}"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0,
                max_tokens=1200,
            )
            repaired_text = (response.choices[0].message.content or "").strip()
            return repaired_text or text
        except Exception as e:
            print(f"Script enforcement error: {e}, using original text")
            return text

    def _translate_to_target_language(self, text: str, target_language: str) -> str:
        if not text or not self.use_ai or target_language == "en":
            return text

        target_language_name = LANGUAGE_LABELS.get(target_language, "English")
        language_rule = TARGET_LANGUAGE_RULES.get(target_language, "")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Translate the text into the requested language while preserving meaning and tone. "
                            f"Return only {target_language_name}. {language_rule}"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                temperature=0,
                max_tokens=1200,
            )
            translated_text = (response.choices[0].message.content or "").strip()
            return translated_text or text
        except Exception as e:
            print(f"Translation error: {e}, using original text")
            return text

    def normalize_transcript(
        self, text: str, target_language: str = "en"
    ) -> Dict[str, str]:
        """Normalize transcript text into the target language/script when AI is available."""
        cleaned_text = text.strip()
        if not cleaned_text:
            return {"text": "", "language": target_language}

        if not self.use_ai:
            return {"text": cleaned_text, "language": target_language}

        target_language_name = LANGUAGE_LABELS.get(target_language, "English")
        script_rule = SCRIPT_RULES.get(target_language, "")

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You normalize transcripts. Preserve meaning, names, and sentence order. "
                            f"Return only the corrected transcript in {target_language_name}. "
                            f"{script_rule} "
                            "Do not summarize. Do not explain. Do not add bullets or labels."
                        ),
                    },
                    {"role": "user", "content": cleaned_text},
                ],
                temperature=0.1,
                max_tokens=1200,
            )
            normalized_text = (response.choices[0].message.content or "").strip()
            normalized_text = self._translate_to_target_language(
                normalized_text,
                target_language,
            )
            normalized_text = self._enforce_target_script(normalized_text, target_language)
            return {"text": normalized_text, "language": target_language}
        except Exception as e:
            print(f"Normalization Error: {e}, using original transcript")
            return {"text": cleaned_text, "language": target_language}

    def _detect_content_type(self, text: str) -> str:
        """Automatically detect what kind of content this is."""
        text_lower = text.lower()

        meeting_words = [
            "meeting",
            "discuss",
            "agenda",
            "team",
            "project",
            "deadline",
            "client",
        ]
        if any(word in text_lower for word in meeting_words):
            return "meeting"

        story_words = ["woke up", "felt", "realized", "happened", "morning", "night", "later"]
        if any(word in text_lower for word in story_words):
            return "story"

        action_words = ["need to", "should", "must", "todo", "task", "action"]
        if any(word in text_lower for word in action_words):
            return "action"

        return "general"

    def _coerce_text(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            parts = [self._coerce_text(item) for item in value]
            return " ".join(part for part in parts if part).strip()
        if isinstance(value, dict):
            parts = [self._coerce_text(item) for item in value.values()]
            return " ".join(part for part in parts if part).strip()
        return str(value).strip()

    def _coerce_text_list(self, value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            items = [self._coerce_text(item) for item in value]
        else:
            items = [self._coerce_text(value)]
        return [item for item in items if item]

    def _normalize_result_shape(self, result: Dict) -> Dict:
        normalized = {
            "summary": self._coerce_text(result.get("summary", "")),
            "key_points": self._coerce_text_list(result.get("key_points", [])),
            "action_items": self._coerce_text_list(result.get("action_items", [])),
            "deadlines": self._coerce_text_list(result.get("deadlines", [])),
            "decisions": self._coerce_text_list(result.get("decisions", [])),
            "content_type": result.get("content_type", "general"),
            "language": result.get("language", "en"),
        }
        return normalized

    def _ai_smart_summary(
        self, text: str, style: str, target_language: str = "en"
    ) -> Dict:
        """AI summary that adapts to content type."""
        content_type = self._detect_content_type(text)
        target_language_name = LANGUAGE_LABELS.get(target_language, "English")
        script_rule = SCRIPT_RULES.get(target_language, "")

        prompts = {
            "story": f"""This is a personal story or narrative. Create a natural, engaging summary.

Story: {text}

Please provide:
1. SUMMARY: A flowing 2-3 sentence overview of what happened
2. KEY MOMENTS: The main events in chronological order
3. EMOTIONS OR REFLECTIONS: Any feelings or realizations""",
            "meeting": f"""This is a meeting or professional discussion. Extract key information.

Meeting Notes: {text}

Please provide:
1. SUMMARY: What was accomplished or discussed in 2-3 sentences
2. DECISIONS: What was decided
3. ACTION ITEMS: Who needs to do what by when
4. NEXT STEPS: What happens next""",
            "action": f"""This contains tasks and action items. Extract clearly.

Content: {text}

Please provide:
1. SUMMARY: Overview of what needs to be done
2. ACTION ITEMS: List each task with who and when
3. PRIORITIES: What is most important or urgent""",
            "general": f"""Summarize this content clearly and concisely.

Content: {text}

Please provide:
1. SUMMARY: Main points in 2-3 sentences
2. KEY DETAILS: Important supporting information
3. KEY TAKEAWAYS: What to remember""",
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are an expert summarizer. The content type is: {content_type}. "
                            f"Create natural, useful summaries. Always respond in {target_language_name}. "
                            f"{script_rule} "
                            "Do not switch to another language unless the source text requires a name or quote. "
                            "Return plain text in exactly this structure:\n"
                            "SUMMARY: <2-3 sentence summary>\n"
                            "KEY POINTS:\n- <point>\n"
                            "ACTION ITEMS:\n- <item>\n"
                            "DEADLINES:\n- <deadline>\n"
                            "DECISIONS:\n- <decision>\n"
                            "If a section has nothing useful, still include the header and write '- None'."
                        ),
                    },
                    {"role": "user", "content": prompts[content_type]},
                ],
                temperature=0.3,
                max_tokens=700,
            )

            ai_text = response.choices[0].message.content or ""
            result = self._normalize_result_shape(self._parse_ai_response(ai_text))
            result["summary"] = self._enforce_target_script(
                self._translate_to_target_language(result["summary"], target_language),
                target_language,
            )
            result["key_points"] = [
                self._enforce_target_script(
                    self._translate_to_target_language(item, target_language),
                    target_language,
                )
                for item in result["key_points"]
            ]
            result["action_items"] = [
                self._enforce_target_script(
                    self._translate_to_target_language(item, target_language),
                    target_language,
                )
                for item in result["action_items"]
            ]
            result["deadlines"] = [
                self._enforce_target_script(
                    self._translate_to_target_language(item, target_language),
                    target_language,
                )
                for item in result["deadlines"]
            ]
            result["decisions"] = [
                self._enforce_target_script(
                    self._translate_to_target_language(item, target_language),
                    target_language,
                )
                for item in result["decisions"]
            ]
            result["content_type"] = content_type
            result["language"] = target_language
            print(
                f"AI summary succeeded via provider={self.provider} model={self.model_name}"
            )
            return self._with_metadata(result, ai_used=True)

        except Exception as e:
            fallback_reason = str(e)
            print(
                f"AI Error via provider={self.provider} model={self.model_name}: "
                f"{fallback_reason}. Falling back to local summary."
            )
            return self._with_metadata(
                self._local_smart_summary(text, style, target_language),
                ai_used=False,
                fallback_reason=fallback_reason,
            )

    def _local_smart_summary(
        self, text: str, style: str, target_language: str = "en"
    ) -> Dict:
        """Local summarizer that adapts to content type."""
        content_type = self._detect_content_type(text)
        sentences = self._split_sentences(text)

        if not sentences:
            return self._empty_result()

        if content_type == "story":
            result = self._summarize_story(sentences, text)
        elif content_type == "meeting":
            result = self._summarize_meeting(sentences, text)
        elif content_type == "action":
            result = self._summarize_actions(sentences, text)
        else:
            result = self._summarize_general(sentences, text)

        result["language"] = target_language
        return result

    def _summarize_story(self, sentences: List[str], full_text: str) -> Dict:
        if len(sentences) <= 2:
            summary = " ".join(sentences)
        else:
            intro = sentences[0]
            middle = " ".join(sentences[1:-1])
            conclusion = sentences[-1]
            summary = f"{intro} Then, {middle.lower()} Finally, {conclusion.lower()}"

        key_points = []
        for sent in sentences:
            if any(word in sent.lower() for word in ["found", "realized", "discovered", "happened"]):
                key_points.append(sent)
            elif len(key_points) < 3 and sent not in key_points:
                key_points.append(sent)

        return {
            "summary": summary[:400],
            "key_points": key_points[:4],
            "action_items": self._extract_action_items(full_text),
            "deadlines": [],
            "decisions": self._extract_decisions(full_text),
            "content_type": "story",
        }

    def _summarize_meeting(self, sentences: List[str], full_text: str) -> Dict:
        if len(sentences) <= 2:
            summary = " ".join(sentences)
        else:
            summary = (
                f"The discussion covered: {sentences[0]}. "
                f"Key outcomes: {sentences[1] if len(sentences) > 1 else ''}"
            )

        return {
            "summary": summary[:400],
            "key_points": sentences[:4],
            "action_items": self._extract_action_items(full_text),
            "deadlines": self._extract_deadlines(full_text),
            "decisions": self._extract_decisions(full_text),
            "content_type": "meeting",
        }

    def _summarize_actions(self, sentences: List[str], full_text: str) -> Dict:
        action_items = self._extract_action_items(full_text)

        if action_items:
            summary = (
                f"Action items identified: {len(action_items)} tasks. "
                f"Main tasks: {'. '.join(action_items[:2])}"
            )
        else:
            summary = "No clear action items identified."

        return {
            "summary": summary,
            "key_points": sentences[:3],
            "action_items": action_items,
            "deadlines": self._extract_deadlines(full_text),
            "decisions": self._extract_decisions(full_text),
            "content_type": "action",
        }

    def _summarize_general(self, sentences: List[str], full_text: str) -> Dict:
        if len(sentences) <= 3:
            summary = " ".join(sentences)
        else:
            summary = f"{sentences[0]} {sentences[1]} {sentences[-1]}"

        return {
            "summary": summary[:400],
            "key_points": sentences[:4],
            "action_items": self._extract_action_items(full_text),
            "deadlines": self._extract_deadlines(full_text),
            "decisions": self._extract_decisions(full_text),
            "content_type": "general",
        }

    def _empty_result(self) -> Dict:
        return {
            "summary": "No content to summarize",
            "key_points": [],
            "action_items": [],
            "deadlines": [],
            "decisions": [],
            "content_type": "unknown",
        }

    def _parse_ai_response(self, ai_text: str) -> Dict:
        sections = {
            "summary": "",
            "key_points": [],
            "action_items": [],
            "deadlines": [],
            "decisions": [],
        }

        lines = ai_text.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            lower_line = line.lower()

            if "summary" in lower_line and ":" in line:
                parts = line.split(":", 1)
                sections["summary"] = parts[1].strip() if len(parts) > 1 else ""
                current_section = "summary"
            elif any(word in lower_line for word in ["key moments", "key points", "main events"]):
                current_section = "key_points"
            elif any(word in lower_line for word in ["action items", "tasks", "to-do"]):
                current_section = "action_items"
            elif any(word in lower_line for word in ["deadlines", "due", "by when"]):
                current_section = "deadlines"
            elif any(word in lower_line for word in ["decisions", "conclusions", "agreed"]):
                current_section = "decisions"
            elif line.startswith(("-", "*", "1.", "2.", "3.")):
                clean_line = line.lstrip("- *123456789.").strip()
                if clean_line and current_section and current_section in sections:
                    if isinstance(sections[current_section], list):
                        sections[current_section].append(clean_line)
            elif current_section == "summary" and sections["summary"]:
                sections["summary"] += " " + line
            elif current_section == "summary" and not sections["summary"]:
                sections["summary"] = line

        for key in ("key_points", "action_items", "deadlines", "decisions"):
            cleaned_items = []
            for item in sections[key]:
                normalized_item = self._coerce_text(item)
                if normalized_item and normalized_item.lower() != "none":
                    cleaned_items.append(normalized_item)
            sections[key] = cleaned_items

        if sections["summary"].lower() == "none":
            sections["summary"] = ""

        return sections

    def _split_sentences(self, text: str) -> List[str]:
        text = text.replace("Mr.", "Mr").replace("Mrs.", "Mrs").replace("Dr.", "Dr")
        text = text.replace("i.e.", "ie").replace("e.g.", "eg")

        sentences = []
        for sent in re.split(r"[.!?]+", text):
            sent = sent.strip()
            if len(sent) > 10:
                if sent and sent[0].islower():
                    sent = sent[0].upper() + sent[1:]
                sentences.append(sent)

        return sentences

    def _extract_action_items(self, text: str) -> List[str]:
        action_phrases = [
            "need to",
            "should",
            "must",
            "have to",
            "will",
            "going to",
            "please",
            "action item",
            "todo",
            "task",
            "remind",
            "don't forget",
            "remember to",
        ]

        sentences = self._split_sentences(text)
        actions = []

        for sent in sentences:
            lower_sent = sent.lower()
            if any(phrase in lower_sent for phrase in action_phrases):
                if len(sent) > 15:
                    actions.append(sent)

        seen = set()
        return [a for a in actions if not (a in seen or seen.add(a))][:5]

    def _extract_deadlines(self, text: str) -> List[str]:
        deadline_keywords = ["by", "due", "deadline", "before", "until", "tomorrow", "next"]
        deadlines = []

        sentences = self._split_sentences(text)
        for sent in sentences:
            if any(word in sent.lower() for word in deadline_keywords):
                deadlines.append(sent)

        return deadlines[:3]

    def _extract_decisions(self, text: str) -> List[str]:
        decision_keywords = ["decided", "agreed", "realized", "noticed", "concluded", "understood"]
        decisions = []

        sentences = self._split_sentences(text)
        for sent in sentences:
            if any(word in sent.lower() for word in decision_keywords):
                decisions.append(sent)

        return decisions[:3]
