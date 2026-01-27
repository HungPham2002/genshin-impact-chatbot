"""
Test Google Gemini API connectivity
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()


def test_gemini_connection():
    """Test basic Gemini API connection"""

    print("=" * 60)
    print("Testing Google Gemini API")
    print("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env file!")
        print("Please add: GOOGLE_API_KEY=your_key_here")
        return False

    print(f"API Key found: {api_key[:10]}...{api_key[-5:]}")

    try:
        genai.configure(api_key=api_key)

        print("\nAvailable Gemini Models:")
        models = genai.list_models()

        gemini_models = [m for m in models if 'gemini' in m.name.lower()]

        for i, model in enumerate(gemini_models[:5], 1):
            print(f"  {i}. {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"     Methods: {model.supported_generation_methods}")

        print("\nTesting text generation...")
        model = genai.GenerativeModel('gemini-2.5-flash')

        response = model.generate_content("Say 'Hello from Gemini!' in one sentence.")

        print(f"Response: {response.text}")

        print("\n" + "=" * 60)
        print("Google Gemini API is working!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nPossible issues:")
        print("  1. Invalid API key")
        print("  2. API quota exceeded")
        print("  3. Network connection problem")
        return False


if __name__ == "__main__":
    test_gemini_connection()