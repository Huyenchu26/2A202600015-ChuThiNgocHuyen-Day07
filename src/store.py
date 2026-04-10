from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Initialize chromadb client + collection
            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        embedding = self._embedding_fn(doc.content)
        return {
            "id": self._next_index,
            "doc_id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": doc.metadata or {}
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records:
            return []
        
        query_embedding = self._embedding_fn(query)
        
        # Compute dot product similarity for each record
        scored_records = []
        for record in records:
            similarity = _dot(query_embedding, record["embedding"])
            scored_records.append((similarity, record))
        
        # Sort by similarity (descending) and return top_k
        scored_records.sort(key=lambda x: x[0], reverse=True)
        
        # Return records with score included
        result = []
        for score, record in scored_records[:top_k]:
            result_record = {
                "id": record["id"],
                "doc_id": record["doc_id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score
            }
            result.append(result_record)
        return result

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            
            if self._use_chroma and self._collection:
                # Add to ChromaDB
                self._collection.add(
                    ids=[str(record["id"])],
                    documents=[record["content"]],
                    embeddings=[record["embedding"]],
                    metadatas=[{"doc_id": record["doc_id"], **record["metadata"]}]
                )
            else:
                # Add to in-memory store
                self._store.append(record)
            
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection:
            # Search using ChromaDB
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                include=["embeddings", "documents", "metadatas", "distances"]
            )
            # Convert ChromaDB results to our dict format
            output = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distances, convert to similarity (1 - distance for cosine)
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    score = 1 - distance if results.get("distances") else 0
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    output.append({
                        "id": int(doc_id),
                        "doc_id": metadata.get("doc_id", ""),
                        "content": results["documents"][0][i],
                        "metadata": {k: v for k, v in metadata.items() if k != "doc_id"},
                        "score": score
                    })
            return output
        else:
            # Search in-memory store
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            metadata_filter = {}
        
        if self._use_chroma and self._collection:
            # Use ChromaDB's where clause for filtering
            where_clause = None
            if metadata_filter:
                # Convert dict to ChromaDB where clause
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append({key: {"$eq": value}})
                if conditions:
                    where_clause = {"$and": conditions} if len(conditions) > 1 else conditions[0]
            
            results = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=where_clause,
                include=["embeddings", "documents", "metadatas", "distances"]
            )
            output = []
            if results and results["ids"] and len(results["ids"]) > 0:
                for i, doc_id in enumerate(results["ids"][0]):
                    # ChromaDB returns distances, convert to similarity (1 - distance for cosine)
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    score = 1 - distance if results.get("distances") else 0
                    
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    output.append({
                        "id": int(doc_id),
                        "doc_id": metadata.get("doc_id", ""),
                        "content": results["documents"][0][i],
                        "metadata": {k: v for k, v in metadata.items() if k != "doc_id"},
                        "score": score
                    })
            return output
        else:
            # Filter in-memory store by metadata
            filtered_records = []
            for record in self._store:
                if all(record["metadata"].get(k) == v for k, v in metadata_filter.items()):
                    filtered_records.append(record)
            
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection:
            # Delete from ChromaDB using where clause
            try:
                self._collection.delete(where={"doc_id": {"$eq": doc_id}})
                return True
            except Exception:
                return False
        else:
            # Remove from in-memory store
            original_len = len(self._store)
            self._store = [r for r in self._store if r["doc_id"] != doc_id]
            return len(self._store) < original_len
