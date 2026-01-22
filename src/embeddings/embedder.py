"""
Embeddings generator for Genshin Impact character data
Uses SentenceTransformers for text embeddings
"""

import json
from typing import List, Dict, Tuple
from tqdm import tqdm
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np


class GenshinEmbedder:
    """Generate embeddings from character chunks"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedder

        Args:
            model_name: SentenceTransformer model name
                       - all-MiniLM-L6-v2: Fast, 384 dim
                       - paraphrase-multilingual-MiniLM-L12-v2: Multilingual
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        print(f"Model loaded!  Embedding dimension: {self.model.get_sentence_embedding_dimension()}")

    def load_chunks(self, chunks_file: Path) -> List[Dict]:
        """
        Load character chunks from JSON file

        Args:
            chunks_file: Path to characters_chunks_v2.json

        Returns:
            List of chunk dictionaries
        """
        print(f"Loading chunks from: {chunks_file}")

        if not chunks_file.exists():
            raise FileNotFoundError(f"Chunks file not found: {chunks_file}")

        with open(chunks_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)

        print(f"Loaded {len(chunks)} chunks")
        return chunks

    def prepare_texts(self, chunks: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Prepare texts and metadata from chunks

        Args:
            chunks: List of chunk dictionaries

        Returns:
            Tuple of (texts, metadatas)
        """
        texts = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            # Combine character name + section + content for better context
            character = chunk.get('character', 'Unknown')
            section = chunk.get('section', '')
            content = chunk.get('content', '')

            # Create rich text for embedding
            if content:
                text = f"Character: {character}\n{content}"
            else:
                text = f"Character: {character}\n{section}"

            texts.append(text)

            # Prepare metadata
            metadata = chunk.get('metadata', {})
            metadata['character'] = character
            metadata['section'] = section
            metadata['chunk_id'] = i

            metadatas.append(metadata)

        return texts, metadatas

    def create_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Create embeddings for texts

        Args:
            texts: List of text strings
            batch_size: Batch size for encoding

        Returns:
            Numpy array of embeddings (n_texts, embedding_dim)
        """
        print(f"Creating embeddings for {len(texts)} texts...")

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        print(f"Created embeddings with shape: {embeddings.shape}")
        return embeddings

    def process_chunks_file(
            self,
            chunks_file: Path,
            batch_size: int = 32
    ) -> Tuple[List[str], np.ndarray, List[Dict]]:
        """
        Complete pipeline:  Load chunks -> Create embeddings

        Args:
            chunks_file: Path to chunks JSON file
            batch_size:  Batch size for embedding generation

        Returns:
            Tuple of (texts, embeddings, metadatas)
        """
        # Load chunks
        chunks = self.load_chunks(chunks_file)

        # Prepare texts and metadata
        texts, metadatas = self.prepare_texts(chunks)

        # Create embeddings
        embeddings = self.create_embeddings(texts, batch_size)

        print(f"\nSummary:")
        print(f"  - Total chunks: {len(chunks)}")
        print(f"  - Texts prepared: {len(texts)}")
        print(f"  - Embeddings shape: {embeddings.shape}")
        print(f"  - Metadata entries: {len(metadatas)}")

        return texts, embeddings, metadatas

    def save_embeddings(
            self,
            embeddings: np.ndarray,
            texts: List[str],
            metadatas: List[Dict],
            output_file: Path
    ):
        """
        Save embeddings to file for later use

        Args:
            embeddings: Numpy array of embeddings
            texts: List of texts
            metadatas: List of metadata dicts
            output_file: Output file path
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'model': self.model_name,
            'embeddings': embeddings.tolist(),
            'texts': texts,
            'metadatas': metadatas
        }

        print(f"Saving embeddings to:  {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Embeddings saved!")


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    # Initialize embedder
    embedder = GenshinEmbedder(model_name="all-MiniLM-L6-v2")

    # Process chunks file
    chunks_file = Path("data/processed/characters_chunks_v3.json")
    texts, embeddings, metadatas = embedder.process_chunks_file(chunks_file)

    # Show sample
    print("\nSample:")
    print(f"Text: {texts[0][: 200]}...")
    print(f"Embedding:  {embeddings[0][:5]}...  (first 5 dims)")
    print(f"Metadata: {metadatas[0]}")