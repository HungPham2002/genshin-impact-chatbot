"""
Configuration management for Genshin Impact Chatbot
"""

from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"
    CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"

    # Data files
    CHUNKS_FILE = PROCESSED_DATA_DIR / "characters_chunks_v3.json"

    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

    # Embedding settings
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions, fast
    EMBEDDING_DIMENSION = 384

    # ChromaDB settings
    CHROMA_COLLECTION_NAME = "genshin_characters"

    # LLM settings
    LLM_PROVIDER = "gemini"
    GEMINI_MODEL = "gemini-2.5-flash"
    LLM_TEMPERATURE = 0.7
    LLM_MAX_TOKENS = 512


    # RAG settings
    RETRIEVAL_TOP_K = 3  # Number of chunks to retrieve

    @classmethod
    def validate(cls):
        """Validate required configurations"""
        if not cls.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment variables. "
                "Please set it in . env file"
            )

        if not cls.CHUNKS_FILE.exists():
            raise FileNotFoundError(
                f"Chunks file not found:  {cls.CHUNKS_FILE}"
            )

        # Create directories if not exist
        cls.CHROMA_DB_DIR.mkdir(exist_ok=True, parents=True)

        print("Configuration validated successfully!")
        return True


if __name__ == "__main__":
    # Test configuration
    Config.validate()
    print(f"Project Root: {Config.PROJECT_ROOT}")
    print(f"Chunks File: {Config.CHUNKS_FILE}")
    print(f"Chroma DB:  {Config.CHROMA_DB_DIR}")
    print(f"LLM Model: {Config.GEMINI_MODEL}")