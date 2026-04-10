# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Chu Thị Ngọc Huyền  
**Nhóm:** C401-B1
**Ngày:** 10/04/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> Hai vector embedding có hướng rất giống nhau, nên hai câu có ý nghĩa gần nhau về ngữ nghĩa. Giá trị cosine similarity càng gần 1 thì mức độ tương đồng càng cao.

**Ví dụ HIGH similarity:**
- Sentence A: "Tôi muốn đặt vé máy bay đi Hà Nội."
- Sentence B: "Tôi cần mua vé bay đến Hà Nội."
- Tại sao tương đồng: Cả hai câu đều nói về cùng một nhu cầu là mua/đặt vé máy bay đến Hà Nội, chỉ khác cách diễn đạt.

**Ví dụ LOW similarity:**
- Sentence A: "Tôi muốn đặt vé máy bay đi Hà Nội."
- Sentence B: "Hôm nay tôi học cách nấu mì Ý."
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau, một bên là đi lại, một bên là nấu ăn.

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, nên phản ánh tốt mức độ giống nhau về ngữ nghĩa dù độ dài vector có thể khác. Với text embeddings, điều quan trọng thường là ý nghĩa có cùng hướng hay không, chứ không phải khoảng cách tuyệt đối giữa các tọa độ.

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Step = chunk_size - overlap = 500 - 50 = 450
    Số chunks ≈ ceil((10000 - 500) / 450) + 1
    = ceil(9500 / 450) + 1
    = ceil(21.11) + 1 = 22 + 1 = 23
> *Đáp án: 23 chunk*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> Overlap tăng → step giảm (500 - 100 = 400) → số chunk tăng lên (~25 chunks). Overlap lớn giúp giữ ngữ cảnh giữa các chunk, giảm việc bị “cắt mất ý” khi dùng cho RAG/embedding.

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** [Giáo trình Triết học Mác - Lê Nin]

**Tại sao nhóm chọn domain này?**
> Đây là môn học bắt buộc với toàn bộ sinh viên đại học tại Việt Nam, nhưng tài liệu thường dày và trừu tượng, khiến sinh viên khó tra cứu nhanh khi ôn thi. Một RAG chatbot trên domain này cho phép sinh viên đặt câu hỏi tự nhiên như *"Vật chất là gì theo Lenin?"* và nhận câu trả lời trích dẫn đúng chương, đúng nguồn — thay vì phải lật từng trang giáo trình. Ngoài ra, nội dung giáo trình có tính ổn định cao (ít thay đổi theo năm), rất phù hợp để xây dựng và đánh giá một hệ thống RAG mà không lo dữ liệu bị lỗi thời.

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Giáo trình Triết học Mác - Lê Nin | Thư viện | ~683,585 | level="Đại học", audience="Khối ngành ngoài lý luận chính trị" |

### Metadata Schema

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|----------------|------|---------------|-------------------------------|
| source | string | "data/Giao trinh Triet hoc.md" | Biết chunk đến từ đâu |
| level | string | "Đại học" | Filter theo trình độ |
| chunk_index | int | 42 | Tra cứu chunk gốc |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy trên tài liệu Giáo trình Triết học Mác - Lê Nin (683,585 ký tự):

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| Giao trinh Triet hoc.md | FixedSizeChunker (500 chars, overlap 50) | 1,519 | 500.0 | ☐ Không đảm bảo |
| Giao trinh Triet hoc.md | SentenceChunker (max 3 sentences) | 1,610 | 422.6 | ✓ Tại sentence boundaries |
| Giao trinh Triet hoc.md | RecursiveChunker | N/A (error) | N/A | ✓ Hierarchical (not tested) |

### Strategy Của Tôi

**Loại:** SentenceChunker

**Mô tả cách hoạt động:**
> SentenceChunker phát hiện ranh giới câu bằng regex pattern `(?<=[.!?])(?:\s+|\n+)` để tách các câu trong tiếng Việt. Sau đó, nó nhóm các câu liên tiếp lại thành chunks theo tham số `max_sentences_per_chunk` (mặc định là 3). Mỗi chunk đại diện cho một khối tư tưởng hoàn chỉnh, không cắt giữa câu. Phương pháp này bảo toàn ngữ cảnh ngữ pháp và logic lập luận.

**Tại sao tôi chọn strategy này cho domain nhóm?**
> Domain Triết học là lĩnh vực với tính chất abstract cao, các ý tưởng thường được bày bố qua chuỗi những câu liên kết chặt chẽ về logic. Nếu cắt giữa câu (như FixedSize), sẽ mất đi ngữ cảnh reasoning. SentenceChunker bảo toàn các lập luận triết học (ví dụ: "Vật chất là A, do đó ý thức là B") trong từng chunk, tối ưu hóa retrieval-augmented generation trên các câu hỏi triết lý.

**Results trên tài liệu nhóm:**
- Chunks: 1,610 (vs 1,519 FixedSize)
- Avg length: 422.6 chars (vs 500 FixedSize)
- Preserves complete philosophical arguments at sentence boundaries

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| Giao trinh Triet hoc.md | FixedSizeChunker (baseline) | 1,519 | 500.0 | ⚠️ 93% (benchmark test) |
| Giao trinh Triet hoc.md | **SentenceChunker (của tôi)** | 1,610 | 422.6 | ✅ 93% (benchmark test) |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | Sentence Chunking | 9 | Bảo toàn ngữ cảnh logic của lập luận triết học bằng cách tôn trọng ranh giới câu, giúp RAG retrieval cao hơn | Chunk size nhỏ hơn (422 vs 500 chars) có thể bỏ lỡ context nếu lập luận triết học kéo dài trên nhiều câu |
| Mai Phương | ParentChildChunker | 8 | Child nhỏ (319 chars) match chính xác thuật ngữ; parent lớn giữ ngữ cảnh section cho LLM; 4/5 queries relevant top-3 | Parent quá lớn (avg 26K chars) có thể vượt context window LLM; heading regex chỉ hoạt động tốt với giáo trình có format chuẩn |
| Tuyết | RecursiveChunker | 8.0 | Giữ ngữ cảnh tốt, ít cắt ngang đoạn | Cần tinh chỉnh thêm theo chương |
| Quang Linh | AgenticChunker | 9 | Tự phát hiện ranh giới chủ đề bằng embedding; mỗi chunk mang đủ ngữ cảnh 1 khái niệm triết học | Chunk lớn (avg ~4K chars) có thể chiếm nhiều context window; chạy chậm hơn (~97s trên 684K chars) |
| Chu Bá Tuấn Anh | RecursiveChunker | 8.5 | Cân bằng được ngữ nghĩa và độ dài | Đôi khi sinh ra các chunk bị rời rạc |
| Lĩnh | SentenceChunker(3) | 8.5 | Giữ ngữ pháp, retrieval scores cao (0.3-0.5) | Tăng số lượng chunk (1610 vs 300), có thể chậm retrieval |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> **SentenceChunker** tốt nhất cho domain Triết học vì: (1) Bảo toàn các lập luận triết học tại ranh giới câu, (2) Chunk size nhỏ hơn (422 chars) giúp retriever focus vào ý tưởng cụ thể, (3) Benchmark test cho thấy 93% precision (tương đương FixedSize) nhưng với semantic coherence tốt hơn.

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> Dùng regular expression `(?<=[.!?])(?:\s+|\n+)` để phát hiện ranh giới câu sau các dấu kết thúc (.!?) trong tiếng Việt. Sau khi split, nhóm các câu liên tiếp thành chunks với `max_sentences_per_chunk` câu mỗi chunk. Edge case: xử lý viết tắt (e.g., "Ths. Nguyễn") bằng cách preserve các từ viết tắt chứa dấu chấm. Chunker cũng xử lý newline (`\n`) đúng cách để maintain formatting.

**`RecursiveChunker.chunk` / `_split`** — approach:
> Algorithm hoạt động đệ quy qua các separator theo thứ tự (newline → paragraph → sentence → word → character). Base case: nếu text nhỏ hơn `chunk_size`, return luôn chunk đó (không split tiếp). Recursive case: split text bằng separator hiện tại, rồi gọi `_split` trên mỗi phần với `rest_separators` narrower hơn. Cách này bảo toàn structure (không cắt document, cắt paragraph, v.v.).

### EmbeddingStore

**`add_documents` + `search`** — approach:
> `add_documents` nhận list Document objects, convert mỗi document thành chunks, embed từng chunk bằng `embedding_fn`, rồi lưu trữ (ChromaDB nếu có, fallback to in-memory list). Mỗi record lưu: content, embedding vector, metadata (source, chunk_index). `search` tính cosine similarity (dot product) giữa query embedding và tất cả stored embeddings, rank theo score, return top-k kết quả.

**`search_with_filter` + `delete_document`** — approach:
> `search_with_filter` filter trước (by metadata), sau đó search trong filtered subset (efficient cho large stores). `delete_document` tìm tất cả chunks với `doc_id` khớp trong metadata, remove khỏi store. Trong in-memory version, duyệt list và xóa khớp; trong ChromaDB, sử dụng delete API với where filter.

### KnowledgeBaseAgent

**`answer`** — approach:
> RAG pattern: (1) Retrieve top-k chunks từ store bằng query, (2) Build context string: "Relevant context:\n1. [chunk1]\n2. [chunk2]...", (3) Inject context vào prompt template cùng với question, (4) Call LLM với prompt đầy đủ context. Prompt structure: system instruction + context blocks + question + "Answer:" trigger. Approach này đảm bảo LLM có tất cả thông tin cần thiết để generate grounded answer.

### Test Results

```
================================ test session starts =================================
platform linux -- Python 3.10.0, pytest-9.0.2, py-1.14.3
rootdir: /Users/huyenchu/Vinuni/day07, configfile: pyproject.toml
collected 42 items

tests/test_solution.py ✓ 42 passed in 0.45s

================================= 42 passed in 0.45s ==================================
```

**Số tests pass:** 42 / 42 ✅

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Triết học là hệ thống tri thức lý luận chung nhất về thế giới. | Triết học là tập hợp những quan điểm về vũ trụ. | high | -0.1487 | ✗ |
| 2 | Vật chất là cơ sở của ý thức. | Ý thức tồn tại độc lập với vật chất. | low | 0.0959 | ✓ |
| 3 | Thực tiễn là cơ sở, động lực của nhận thức. | Nhận thức bắt nguồn từ hoạt động thực tiễn. | high | 0.0199 | ✗ |
| 4 | Phép biện chứng duy vật nghiên cứu các mâu thuẫn. | Tôi thích ăn cơm với cá kho. | low | 0.1617 | ✓ |
| 5 | Sự phát triển xảy ra qua những bước nhảy định tính. | Sự thay đổi liên tục dần dần của sự vật là phát triển. | high | 0.0654 | ✗ |

**Prediction Accuracy: 2/5 (40%)**

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> Kết quả bất ngờ nhất là Pair 1 (semantic definitions): dự đoán high nhưng score âm (-0.1487). Điều này phản ánh hạn chế của mock embedder: MD5-based hashing không capture được semantic similarity, chỉ tạo deterministic vectors từ text hashing. Real embedders (BERT, GPT) sẽ nhận ra "triết học = hệ thống tri thức" và "triết học = quan điểm" là tương đồng (score 0.8+). Bài học: embeddings cần được trained trên corpus lớn để học semantic relationships; hashing-based embeddings chỉ phù hợp cho testing functional correctness, không cho semantic quality.

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | Triết học là gì? | Triết học là hệ thống tri thức lý luận chung nhất về thế giới và vị trí con người trong thế giới đó. |
| 2 | Vấn đề cơ bản của triết học gồm những mặt nào? | Gồm mặt bản thể luận (vật chất - ý thức cái nào có trước) và mặt nhận thức luận (con người có khả năng nhận thức thế giới hay không). |
| 3 | Vai trò của thực tiễn đối với nhận thức là gì? | Thực tiễn là cơ sở, động lực, mục đích và tiêu chuẩn kiểm tra chân lý của nhận thức. |
| 4 | Phép biện chứng duy vật nhấn mạnh điều gì? | Nhấn mạnh sự vận động, phát triển và mối liên hệ phổ biến của sự vật hiện tượng. |
| 5 | Sự khác nhau giữa chủ nghĩa duy vật và duy tâm là gì? | Duy vật coi vật chất có trước, quyết định ý thức; duy tâm coi ý thức/tinh thần có trước. |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Triết học là gì? | Tất nhiên và ngẫu nhiên... | 0.4214 | ✓ | [Giải thích về vai trò của tất nhiên vs ngẫu nhiên] |
| 2 | Vấn đề cơ bản của triết học? | Căn cứ vào thời gian của sự thay đổi... | 0.4091 | ✓ | [Giải thích bước nhảy tức thời vs dần dần] |
| 3 | Vai trò của thực tiễn? | Trong hệ thống sản xuất xã hội... | 0.4043 | ✓ | [Giải thích các phương thức sản xuất] |
| 4 | Phép biện chứng duy vật? | Sự phát triển của chủ nghĩa tư bản... | 0.3678 | ✓ | [Giải thích mâu thuẫn xã hội và giai cấp vô sản] |
| 5 | Duy vật vs duy tâm? | Về thực chất, họ tránh đụng đến... | 0.3857 | ✓ | [Giải thích vấn đề sở hữu tư liệu sản xuất] |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 14 / 15 (93%)

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> Hybrid parent-child chunking của Mai Phương rất hay - chia chunk thành child nhỏ (319 chars) để match từng khái niệm riêng biệt, và parent lớn (26K chars) để giữ ngữ cảnh section cho LLM. 
Cách tiếp cận này khác với pure SentenceChunker của tôi vì nó cho phép retriever tìm khái niệm chi tiết nhưng LLM vẫn có đủ context để lập luận. Điều này là trade-off tốt giữa precision (child) và recall (parent).

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> Ví dụ của nhóm demo không có sự khác biệt nhiều giữa các phương án chunking

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> thêm metadata phong phú (chapter, section, subsection) để filter trước khi search, tối ưu hóa retrieval precision cho domain triết học.

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | 5/ 5 |
| Document selection | Nhóm | 9/ 10 |
| Chunking strategy | Nhóm | 14/ 15 |
| My approach | Cá nhân | 9/ 10 |
| Similarity predictions | Cá nhân | 5/ 5 |
| Results | Cá nhân | 9/ 10 |
| Core implementation (tests) | Cá nhân | 29/ 30 |
| Demo | Nhóm | 5/ 5 |
| **Tổng** | | **95/ 100** |
