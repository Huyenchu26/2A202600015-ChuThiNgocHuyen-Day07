from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        """Store references to store and llm_fn."""
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Retrieve chunks, build prompt, call llm_fn.
        
        RAG pattern:
            1. Retrieve top-k most similar chunks from store
            2. Build a context-aware prompt with the chunks
            3. Call the LLM with the prompt
        """
        # Retrieve top-k relevant chunks
        chunks = self.store.search(question, top_k=top_k)
        
        # Build context from retrieved chunks
        context = ""
        if chunks:
            context = "Relevant context:\n"
            for i, chunk in enumerate(chunks, 1):
                context += f"{i}. {chunk.get('content', '')}\n"
        else:
            context = "No relevant context found."
        
        # Build the prompt for the LLM
        prompt = f"""You are a helpful assistant answering questions based on provided context.

{context}

Question: {question}

Answer:"""
        
        # Call the LLM and return the result
        return self.llm_fn(prompt)
