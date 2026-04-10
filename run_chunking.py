from src.chunking import SentenceChunker
from pathlib import Path

# Read the file
file_path = Path("data/Giao trinh Triet hoc.md")
if not file_path.exists():
    print(f"File not found: {file_path}")
    exit(1)

content = file_path.read_text(encoding="utf-8")
print(f"📄 File: {file_path}")
print(f"📊 Content length: {len(content)} characters\n")

# Apply SentenceChunker
chunker = SentenceChunker(max_sentences_per_chunk=3)
chunks = chunker.chunk(content)

print(f"✂️  Total chunks: {len(chunks)}\n")
print("=" * 80)

# Display chunks
for i, chunk in enumerate(chunks, 1):
    print(f"\n📋 Chunk {i}:")
    print(f"   Length: {len(chunk)} chars")
    print(f"   Content preview: {chunk[:150]}...")
    if i >= 10:  # Show first 10 chunks
        print(f"\n... and {len(chunks) - 10} more chunks")
        break

print("\n" + "=" * 80)
print(f"\n✅ Chunking completed!")
print(f"Average chunk size: {len(content) / len(chunks):.0f} characters")

# Save chunks to file
output_file = Path("chunks_output.txt")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(f"File: {file_path}\n")
    f.write(f"Total chunks: {len(chunks)}\n")
    f.write(f"Total characters: {len(content)}\n")
    f.write(f"Average chunk size: {len(content) / len(chunks):.0f}\n")
    f.write("=" * 80 + "\n\n")
    
    for i, chunk in enumerate(chunks, 1):
        f.write(f"--- CHUNK {i} ({len(chunk)} chars) ---\n")
        f.write(chunk)
        f.write("\n\n")

print(f"📁 Chunks saved to: {output_file}")
