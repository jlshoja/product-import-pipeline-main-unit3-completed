import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

logger = logging.getLogger('standardizer.gemini')


class GeminiTranslator:
    """Batch translator for unknown colors and product names using Gemini API."""

    def __init__(self, api_key='', enabled=True):
        self.enabled = enabled and HAS_GEMINI and bool(api_key)
        self.model = None

        if self.enabled:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                logger.info("Gemini translator initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")
                self.enabled = False

    def translate_colors(self, colors):
        """Batch translate Persian color names to English.

        Args:
            colors: list of Persian color strings

        Returns:
            dict mapping Persian color -> English translation
        """
        if not self.enabled or not colors:
            return {}

        prompt = (
            "Translate the following Persian color names to English. "
            "Return ONLY a valid JSON object mapping each Persian color to its English translation. "
            "Keep it simple - one or two words per color.\n\n"
            f"Colors: {json.dumps(colors, ensure_ascii=False)}\n\n"
            "Response format: {\"فارسی\": \"english\", ...}"
        )

        return self._call_gemini(prompt, colors)

    def translate_product_names(self, names):
        """Batch translate Persian product names to English.

        Args:
            names: list of English product name strings that need Persian translation

        Returns:
            dict mapping English name -> Persian translation
        """
        if not self.enabled or not names:
            return {}

        prompt = (
            "Translate the following English product-related words/phrases to Persian (Farsi). "
            "These are bag and accessory related terms. "
            "Return ONLY a valid JSON object mapping each English word to its Persian translation.\n\n"
            f"Words: {json.dumps(names, ensure_ascii=False)}\n\n"
            "Response format: {\"english\": \"فارسی\", ...}"
        )

        return self._call_gemini(prompt, names)

    def _call_gemini(self, prompt, items):
        """Make a Gemini API call and parse JSON response."""
        if not self.model:
            return {}

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            if text.startswith('```'):
                text = text.split('\n', 1)[1] if '\n' in text else text[3:]
                if text.endswith('```'):
                    text = text[:-3]
                text = text.strip()

            result = json.loads(text)
            if isinstance(result, dict):
                logger.info(f"Gemini translated {len(result)} items")
                return result

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini response as JSON: {e}")
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}")

        return {}
