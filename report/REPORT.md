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
| level | string | "Đại học" | Filter theo trình độ |
| chunk_index | int | 42 | Tra cứu chunk gốc |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Strategy Của Tôi

**Loại:** [SentenceChunker]

**Mô tả cách hoạt động:**
> *Viết 3-4 câu: strategy chunk thế nào? Dựa trên dấu hiệu gì?*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Viết 2-3 câu: domain có pattern gì mà strategy khai thác?*

**Code snippet (nếu custom):**
```python
# Paste implementation here
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| | best baseline | | | |
| | **của tôi** | | | |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Retrieval Score (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Tôi | | | | |
| [Tên] | | | | |
| [Tên] | | | | |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Viết 2-3 câu:*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Viết 2-3 câu: dùng regex gì để detect sentence? Xử lý edge case nào?*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Viết 2-3 câu: algorithm hoạt động thế nào? Base case là gì?*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Viết 2-3 câu: lưu trữ thế nào? Tính similarity ra sao?*

**`search_with_filter` + `delete_document`** — approach:
> *Viết 2-3 câu: filter trước hay sau? Delete bằng cách nào?*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Viết 2-3 câu: prompt structure? Cách inject context?*

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** __ / __

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Dự đoán | Actual Score | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | high / low | | |
| 2 | | | high / low | | |
| 3 | | | high / low | | |
| 4 | | | high / low | | |
| 5 | | | high / low | | |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Viết 2-3 câu:*

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
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu queries trả về chunk relevant trong top-3?** __ / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Viết 2-3 câu:*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Viết 2-3 câu:*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
