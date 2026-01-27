"""
LLM Provider abstraction layer
Supports multiple LLM backends: Gemini, HuggingFace, Local models
"""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

# Google Gemini
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI

# Configuration
from src.utils.config import Config


class BaseLLM(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    def get_llm(self):
        """Return LangChain-compatible LLM instance"""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if LLM is accessible"""
        pass


class GeminiLLM(BaseLLM):
    """Google Gemini LLM provider"""

    def __init__(
            self,
            model_name: str = "gemini-1.5-flash",
            temperature: float = 0.7,
            max_tokens: int = 512,
            api_key: Optional[str] = None
    ):
        """
        Initialize Gemini LLM

        Args:
            model_name: Gemini model name
                       - gemini-2.5-flash: Fast, cost-effective
                       - gemini-2.5-pro: More capable but slower
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response
            api_key: Google API key (defaults to env var)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Get API key
        self.api_key = api_key or Config.GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError(
                "Google API key not found! "
                "Set GOOGLE_API_KEY in .env file"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        print(f"Initializing Gemini LLM: {model_name}")

        # Create LangChain LLM instance
        self._llm = None

    def get_llm(self):
        """Get LangChain-compatible Gemini LLM"""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                google_api_key=self.api_key,
                convert_system_message_to_human=True  # Compatibility
            )
            print(f"Gemini LLM ready: {self.model_name}")

        return self._llm

    def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            print("Testing Gemini connection...")

            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content("Say 'OK' if you can hear me.")

            print(f"Connection successful! Response: {response.text[:50]}")
            return True

        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get LLM configuration info"""
        return {
            'provider': 'Google Gemini',
            'model': self.model_name,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'api_key_set': bool(self.api_key)
        }


class LLMProvider:
    """
    Factory class for creating LLM instances
    Supports multiple providers
    """

    @staticmethod
    def create_llm(
            provider: str = "gemini",
            **kwargs
    ) -> BaseLLM:
        """
        Create LLM instance based on provider

        Args:
            provider: LLM provider name
                     - 'gemini': Google Gemini (default)
                     - 'huggingface': HuggingFace models (future)
                     - 'local': Local models (future)
            **kwargs: Additional arguments for LLM initialization

        Returns:
            BaseLLM instance
        """
        provider = provider.lower()

        if provider == "gemini":
            model_name = kwargs.get('model_name', Config.GEMINI_MODEL)
            temperature = kwargs.get('temperature', Config.LLM_TEMPERATURE)
            max_tokens = kwargs.get('max_tokens', Config.LLM_MAX_TOKENS)

            return GeminiLLM(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )

        elif provider == "huggingface":
            # TODO: Implement HuggingFace provider
            raise NotImplementedError(
                "HuggingFace provider coming soon! Use 'gemini' for now."
            )

        elif provider == "local":
            # TODO: Implement local model provider
            raise NotImplementedError(
                "Local model provider coming soon! Use 'gemini' for now."
            )

        else:
            raise ValueError(
                f"Unknown provider: {provider}."
                f"Supported: gemini, huggingface (coming soon), local (coming soon)"
            )


# Convenience function
def get_default_llm():
    """Get default LLM from config"""
    provider = LLMProvider.create_llm(provider=Config.LLM_PROVIDER)
    return provider.get_llm()


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Testing LLM Provider")
    print("=" * 60)

    # Test 1: Create Gemini LLM
    print("\n[Test 1] Creating Gemini LLM...")
    gemini_provider = LLMProvider.create_llm(provider="gemini")

    # Show info
    info = gemini_provider.get_info()
    print(f"\nLLM Info:")
    for key, value in info.items():
        print(f"  - {key}: {value}")

    # Test 2: Test connection
    print("\n[Test 2] Testing connection...")
    gemini_provider.test_connection()

    # Test 3: Get LangChain LLM
    print("\n[Test 3] Getting LangChain LLM instance...")
    llm = gemini_provider.get_llm()
    print(f"LLM instance: {type(llm)}")

    # Test 4: Simple invoke
    print("\n[Test 4] Testing LLM invoke...")
    try:
        from langchain_core.messages import HumanMessage

        messages = [
            HumanMessage(content="Say 'Hello from LangChain + Gemini!' in one short sentence.")
        ]

        response = llm.invoke(messages)
        print(f"Response: {response.content}")

    except Exception as e:
        print(f"Error: {e}")
