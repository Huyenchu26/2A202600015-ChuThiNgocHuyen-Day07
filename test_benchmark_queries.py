#!/usr/bin/env python3
"""Test RAG system with 5 benchmark queries"""

from pathlib import Path
from src.chunking import SentenceChunker
from src.store import EmbeddingStore
from src.models import Document
from src.agent import KnowledgeBaseAgent
from src.embeddings import _mock_embed

def demo_llm(prompt: str) -> str:
    """Mock LLM for demo."""
    # Extract just the context part for clearer output
    lines = prompt.split('\n')
    start = -1
    for i, line in enumerate(lines):
        if 'Relevant context:' in line:
            start = i + 1
            break
    if start != -1:
        context = '\n'.join(lines[start:start+5])
        return f"[LLM Generated]\n{context}"
    return prompt[:200]

# Benchmark queries from report
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Triết học là gì?",
        "gold_answer": "Triết học là hệ thống tri thức lý luận chung nhất về thế giới và vị trí con người trong thế giới đó."
    },
    {
        "id": 2,
        "query": "Vấn đề cơ bản của triết học gồm những mặt nào?",
        "gold_answer": "Gồm mặt bản thể luận (vật chất - ý thức cái nào có trước) và mặt nhận thức luận (con người có khả năng nhận thức thế giới hay không)."
    },
    {
        "id": 3,
        "query": "Vai trò của thực tiễn đối với nhận thức là gì?",
        "gold_answer": "Thực tiễn là cơ sở, động lực, mục đích và tiêu chuẩn kiểm tra chân lý của nhận thức."
    },
    {
        "id": 4,
        "query": "Phép biện chứng duy vật nhấn mạnh điều gì?",
        "gold_answer": "Nhấn mạnh sự vận động, phát triển và mối liên hệ phổ biến của sự vật hiện tượng."
    },
    {
        "id": 5,
        "query": "Sự khác nhau giữa chủ nghĩa duy vật và duy tâm là gì?",
        "gold_answer": "Duy vật coi vật chất có trước, quyết định ý thức; duy tâm coi ý thức/tinh thần có trước."
    }
]

# Configuration
FILE_PATH = Path("data/Giao trinh Triet hoc.md")
TOP_K = 3

print("\n" + "=" * 120)
print("🔍 BENCHMARK QUERIES TEST - CHUNKING & RAG SYSTEM")
print("=" * 120)

# Step 1: Load and prepare
print("\n📖 Loading and chunking document...\n")
if not FILE_PATH.exists():
    print(f"❌ File not found: {FILE_PATH}")
    exit(1)

content = FILE_PATH.read_text(encoding="utf-8")
chunker = SentenceChunker(max_sentences_per_chunk=3)
chunks = chunker.chunk(content)

print(f"✅ Document loaded: {len(content)} characters")
print(f"✅ Created {len(chunks)} chunks (avg {len(content) / len(chunks):.0f} chars)")

# Create chunk documents
chunk_docs = [
    Document(
        id=f"chunk_{i}",
        content=chunk_text,
        metadata={
            "source": str(FILE_PATH),
            "chunk_index": i,
            "total_chunks": len(chunks)
        }
    )
    for i, chunk_text in enumerate(chunks)
]

# Step 2: Create store and add documents
print(f"\n🏪 Creating EmbeddingStore...\n")
store = EmbeddingStore(collection_name="triet_hoc", embedding_fn=_mock_embed)
store.add_documents(chunk_docs)
store_size = store.get_collection_size()
print(f"✅ Store ready with {store_size} chunks")

# Step 3: Test each query
print(f"\n{'=' * 120}")
print("📋 BENCHMARK RESULTS")
print("=" * 120)

results_summary = []

for q_info in BENCHMARK_QUERIES:
    q_id = q_info["id"]
    query = q_info["query"]
    gold_answer = q_info["gold_answer"]
    
    print(f"\n\n{'█' * 120}")
    print(f"Query #{q_id}: {query}")
    print(f"{'█' * 120}")
    print(f"\n🎯 Gold Answer: {gold_answer}\n")
    
    # Search
    results = store.search(query, top_k=TOP_K)
    
    print(f"📍 Top-{TOP_K} Retrieved Chunks:\n")
    relevant_count = 0
    
    for rank, result in enumerate(results, 1):
        score = result.get("score", 0)
        chunk_content = result["content"][:250].replace("\n", " ")
        chunk_idx = result.get("metadata", {}).get("chunk_index", "?")
        
        # Simple relevance check: does chunk contain key terms from gold answer?
        key_terms = set(word.lower() for word in gold_answer.split() if len(word) > 3)
        chunk_terms = set(word.lower() for word in result["content"].split() if len(word) > 3)
        overlap = len(key_terms & chunk_terms) / len(key_terms) if key_terms else 0
        is_relevant = overlap > 0.2 or score > 0.35
        
        if is_relevant:
            relevant_count += 1
        
        status = "✓ RELEVANT" if is_relevant else "✗ NOT RELEVANT"
        print(f"  Rank {rank} | Score: {score:.4f} | Chunk: {chunk_idx} | {status}")
        print(f"  Preview: {chunk_content}...")
        print()
    
    # Generate agent answer
    agent = KnowledgeBaseAgent(store, demo_llm)
    answer = agent.answer(query, top_k=TOP_K)
    print(f"🤖 Agent Answer:\n{answer}\n")
    
    results_summary.append({
        "id": q_id,
        "query": query,
        "relevant_chunks": relevant_count,
        "top_score": results[0].get("score", 0) if results else 0
    })

# Step 4: Summary
print(f"\n{'=' * 120}")
print("📊 SUMMARY TABLE")
print("=" * 120 + "\n")

print(f"{'#':<3} {'Query':<45} {'Relevant (top-3)':<20} {'Best Score':<20}")
print("-" * 120)

total_relevant = 0
for res in results_summary:
    total_relevant += res["relevant_chunks"]
    print(f"{res['id']:<3} {res['query']:<45} {res['relevant_chunks']}/3{'':<15} {res['top_score']:.4f}")

print("-" * 120)
print(f"\n✅ Total relevant chunks retrieved: {total_relevant} / 15 ({total_relevant*100//15}%)")
print(f"✅ Average retrieval score: {sum(r['top_score'] for r in results_summary) / len(results_summary):.4f}")
print(f"✅ All tests completed successfully!\n")
