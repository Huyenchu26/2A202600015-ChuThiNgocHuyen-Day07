#!/usr/bin/env python3
"""Generate similarity predictions for report Section 5"""

from src.embeddings import _mock_embed
from src.chunking import _dot

print("\n" + "="*100)
print("🔍 SIMILARITY PREDICTIONS TEST")
print("="*100 + "\n")

# Create 5 test pairs with Vietnamese philosophy content
test_pairs = [
    {
        "id": 1,
        "a": "Triết học là hệ thống tri thức lý luận chung nhất về thế giới.",
        "b": "Triết học là tập hợp những quan điểm về vũ trụ và con người.",
        "prediction": "high",
        "reason": "Cùng định nghĩa triết học, chỉ khác diễn đạt"
    },
    {
        "id": 2,
        "a": "Vật chất là cơ sở của ý thức.",
        "b": "Ý thức tồn tại độc lập với vật chất.",
        "prediction": "low",
        "reason": "Hai mệnh đề đối lập (duy vật vs duy tâm)"
    },
    {
        "id": 3,
        "a": "Thực tiễn là cơ sở, động lực của nhận thức.",
        "b": "Nhận thức bắt nguồn từ hoạt động thực tiễn.",
        "prediction": "high",
        "reason": "Cùng quan hệ thực tiễn-nhận thức"
    },
    {
        "id": 4,
        "a": "Phép biện chứng duy vật nghiên cứu các mâu thuẫn của sự vật.",
        "b": "Tôi thích ăn cơm với cá kho.",
        "prediction": "low",
        "reason": "Một về triết học, một về đời sống"
    },
    {
        "id": 5,
        "a": "Sự phát triển xảy ra qua những bước nhảy định tính.",
        "b": "Sự thay đổi liên tục dần dần của sự vật là phát triển.",
        "prediction": "high",
        "reason": "Cùng về phát triển, khác góc nhìn"
    }
]

# Test predictions
print(f"{'Pair':<6} {'Prediction':<12} {'Actual Score':<15} {'Accurate?':<12} {'Reason':<35}")
print("-"*100)

correct = 0
results_data = []

for pair in test_pairs:
    # Get embeddings
    emb_a = _mock_embed(pair["a"])
    emb_b = _mock_embed(pair["b"])
    
    # Calculate similarity
    score = _dot(emb_a, emb_b)
    
    # Determine actual prediction
    actual_pred = "high" if score > 0.3 else "low"
    is_correct = actual_pred == pair["prediction"]
    
    if is_correct:
        correct += 1
    
    status = "✓" if is_correct else "✗"
    
    print(f"{pair['id']:<6} {pair['prediction']:<12} {score:<14.4f} {status:<12} {pair['reason']:<35}")
    
    results_data.append({
        "id": pair["id"],
        "prediction": pair["prediction"],
        "actual_score": score,
        "actual_prediction": actual_pred,
        "correct": is_correct
    })

print("-"*100)
accuracy = (correct / len(test_pairs)) * 100
print(f"\n✅ Prediction Accuracy: {correct}/{len(test_pairs)} ({accuracy:.0f}%)\n")

# Most interesting result
print("="*100)
print("ANALYSIS:")
print("="*100)

# Find most surprising
most_surprising = max(results_data, key=lambda x: abs(0.5 - x["actual_score"]))

print(f"""
🎯 Most Surprising Result: Pair {most_surprising["id"]}
   - Predicted: {most_surprising["prediction"]}
   - Actual Score: {most_surprising["actual_score"]:.4f}
   - Status: {"Correct" if most_surprising["correct"] else "Incorrect"}

💡 What this tells us about embeddings:
   The mock embedder based on MD5 hashing creates deterministic but not semantically
   meaningful embeddings. While it simulates embedding behavior for testing, it cannot
   capture true semantic similarity between antonymous concepts (duy vật vs duy tâm)
   or distinguish philosophical concepts well. Real embeddings (BERT, GPT) would score
   these pairs with much better discrimination (0.7-0.95 for similar, 0.1-0.3 for opposite).
""")

print("="*100 + "\n")
