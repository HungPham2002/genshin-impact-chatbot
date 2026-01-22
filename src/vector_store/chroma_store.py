"""
ChromaDB Vector Store for Genshin Impact data
Persistent local vector database for efficient similarity search
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import numpy as np
from pathlib import Path


class GenshinVectorStore:
    """Vector store using ChromaDB for character information retrieval"""

    def __init__(
            self,
            persist_directory: Path,
            collection_name: str = "genshin_characters",
            embedding_dimension: int = 384
    ):
        """
        Initialize ChromaDB vector store

        Args:
            persist_directory:  Directory to persist ChromaDB data
            collection_name: Name of the collection
            embedding_dimension: Dimension of embeddings (384 for MiniLM-L6)
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension

        # Create persist directory
        persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        print(f"🗄️  Initializing ChromaDB at: {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=str(persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self._get_or_create_collection()
        print(f"✅ Collection '{collection_name}' ready!")

    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name
            )
            count = collection.count()
            print(f"📚 Found existing collection with {count} documents")
            return collection
        except:
            print(f"📝 Creating new collection:  {self.collection_name}")
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )

    def add_documents(
            self,
            texts: List[str],
            embeddings: np.ndarray,
            metadatas: List[Dict],
            ids: Optional[List[str]] = None
    ):
        """
        Add documents to vector store

        Args:
            texts: List of text content
            embeddings: Numpy array of embeddings
            metadatas: List of metadata dictionaries
            ids: Optional list of document IDs
        """
        n_docs = len(texts)

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(n_docs)]

        # Convert embeddings to list
        embeddings_list = embeddings.tolist()

        print(f"📥 Adding {n_docs} documents to vector store...")

        # Add in batches to avoid memory issues
        batch_size = 100
        for i in range(0, n_docs, batch_size):
            end_idx = min(i + batch_size, n_docs)

            self.collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings_list[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )

            print(f"  Added batch {i // batch_size + 1}:  {i}-{end_idx}")

        print(f"✅ Successfully added {n_docs} documents!")
        print(f"📊 Total documents in collection: {self.collection.count()}")

    def similarity_search(
            self,
            query_embedding: np.ndarray,
            k: int = 3,
            filter_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Search for similar documents

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {'element': 'Pyro'})

        Returns:
            Dictionary with ids, documents, metadatas, distances
        """
        # Convert to list if numpy array
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        # Build where clause for metadata filtering
        where = filter_metadata if filter_metadata else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where
        )

        return {
            'ids': results['ids'][0],
            'documents': results['documents'][0],
            'metadatas': results['metadatas'][0],
            'distances': results['distances'][0]
        }

    def get_stats(self) -> Dict:
        """Get collection statistics"""
        count = self.collection.count()

        # Get sample to analyze
        sample = self.collection.peek(limit=10)

        # Count unique characters
        characters = set()
        if sample['metadatas']:
            for metadata in sample['metadatas']:
                if 'character' in metadata:
                    characters.add(metadata['character'])

        return {
            'total_documents': count,
            'collection_name': self.collection_name,
            'sample_characters': list(characters)
        }

    def reset_collection(self):
        """Delete and recreate collection (use with caution!)"""
        print(f"⚠️  Resetting collection:  {self.collection_name}")
        self.client.delete_collection(name=self.collection_name)
        self.collection = self._get_or_create_collection()
        print(f"✅ Collection reset complete!")

    def as_retriever(self, k: int = 3):
        """
        Get a retriever interface for LangChain

        Args:
            k: Number of documents to retrieve

        Returns:
            Retriever object compatible with LangChain
        """
        # This will be implemented in Phase 3 for LangChain integration
        pass


# Example usage and testing
if __name__ == "__main__":
    from pathlib import Path
    from src.embeddings.embedder import GenshinEmbedder
    from src.utils.config import Config

    # Validate config
    Config.validate()

    # Initialize embedder
    print("\n" + "=" * 60)
    print("STEP 1: Create Embeddings")
    print("=" * 60)
    embedder = GenshinEmbedder(model_name=Config.EMBEDDING_MODEL)
    texts, embeddings, metadatas = embedder.process_chunks_file(Config.CHUNKS_FILE)

    # Initialize vector store
    print("\n" + "=" * 60)
    print("STEP 2: Setup Vector Store")
    print("=" * 60)
    vector_store = GenshinVectorStore(
        persist_directory=Config.CHROMA_DB_DIR,
        collection_name=Config.CHROMA_COLLECTION_NAME,
        embedding_dimension=Config.EMBEDDING_DIMENSION
    )

    # Add documents
    print("\n" + "=" * 60)
    print("STEP 3: Add Documents to Vector Store")
    print("=" * 60)
    vector_store.add_documents(
        texts=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    # Show stats
    print("\n" + "=" * 60)
    print("STEP 4: Vector Store Statistics")
    print("=" * 60)
    stats = vector_store.get_stats()
    print(f"📊 Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # Test similarity search
    print("\n" + "=" * 60)
    print("STEP 5: Test Similarity Search")
    print("=" * 60)
    query = "Who is Diluc?"
    query_embedding = embedder.model.encode(query)

    results = vector_store.similarity_search(query_embedding, k=3)

    print(f"\n🔍 Query: '{query}'")
    print(f"📄 Top 3 Results:")
    for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['distances']
    ), 1):
        print(f"\n  Result {i}:")
        print(f"    Character: {metadata.get('character', 'N/A')}")
        print(f"    Distance: {distance:.4f}")
        print(f"    Content: {doc[: 150]}...")