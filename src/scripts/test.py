"""
Test script for Phase 1:  Embeddings & Vector Store
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import Config
from src.embeddings.embedder import GenshinEmbedder
from src.vector_store.chroma_store import GenshinVectorStore

def main():
    print("=" * 70)
    print("GENSHIN IMPACT CHATBOT - PHASE 1 TEST")
    print("=" * 70)

    # Step 1: Validate configuration
    print("\n[1/5] Validating configuration...")
    Config.validate()

    # Step 2: Create embeddings
    print("\n[2/5] Creating embeddings...")
    embedder = GenshinEmbedder(model_name=Config.EMBEDDING_MODEL)
    texts, embeddings, metadatas = embedder.process_chunks_file(Config.CHUNKS_FILE)

    # Step 3: Initialize vector store
    print("\n[3/5] Initializing vector store...")
    vector_store = GenshinVectorStore(
        persist_directory=Config.CHROMA_DB_DIR,
        collection_name=Config.CHROMA_COLLECTION_NAME,
        embedding_dimension=Config.EMBEDDING_DIMENSION
    )

    # Step 4: Add documents (check if already exists)
    current_count = vector_store.collection.count()
    if current_count == 0:
        print("\n[4/5] Adding documents to vector store...")
        vector_store.add_documents(texts, embeddings, metadatas)
    else:
        print(f"\n[4/5] Vector store already has {current_count} documents.  Skipping...")

    # Step 5: Test retrieval
    print("\n[5/5] Testing retrieval...")
    test_queries = [
        "Who is Klee?",
        "Tell me about Pyro characters",
        "Which characters use claymore?",
        "What is Hu Tao's element?"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        query_embedding = embedder.model.encode(query)
        results = vector_store.similarity_search(query_embedding, k=2)

        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas']), 1):
            print(f"  [{i}] {metadata.get('character', 'Unknown')}: {doc[:100]}...")

    # Final stats
    print("\n" + "=" * 70)
    print("PHASE 1 COMPLETE!")
    print("=" * 70)
    stats = vector_store.get_stats()
    print(f"Final Statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    print("\nPhase 1 testing successful!  Ready for Phase 2!")


if __name__ == "__main__":
    main()