import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.vector_store import search_chunks

eval_cases = [
    {
        "question": "What is SpaceX's ticker symbol on Nasdaq?",
        "exp_chunk_index": 0,
        "expected_filename": "sample.txt",
    },
    {
        "question": "When could SpaceX's revenue hit $1 trillion?",
        "exp_chunk_index": 0,
        "expected_filename": "sample.txt",
    },
    {
        "question": "Which professor has collected data on U.S. IPOs since 1960?",
        "exp_chunk_index": 1,
        "expected_filename": "sample.txt",
    },
    {
        "question": "What has been the average one-year return for IPO stocks since 1980?",
        "exp_chunk_index": 1,
        "expected_filename": "sample.txt",
    },
    {
        "question": "Do tech companies generally fare better than non-tech ones?",
        "exp_chunk_index": 2,
        "expected_filename": "sample.txt",
    },
]

def run_evaluation():
    print(f"\n{"-"*40}")
    print(f"Retrieval Evaluation - precision@3")
    print(f"{"-"*40}")

    results_table = []
    hits = 0

    for i, case in enumerate(eval_cases):
        results = search_chunks(query=case["question"], top_k=3)

        top_chunk_indices = [
            r["chunk_index"] for r in results
            if r["filename"] == case["expected_filename"]
        ]
        is_hit = case["exp_chunk_index"] in top_chunk_indices

        if is_hit:
            hits += 1

        top_result = results[0] if results else None
        top_text = (
            top_result["chunk_text"][:80] if top_result else "no results"
        )
        top_score = (
            f"{top_result['score']:.4f}" if top_result else "-"
        )

        results_table.append({
            "question": case["question"],
            "exp_chunk_index": case["exp_chunk_index"],
            "top_index_returned": top_result["chunk_index"] if top_result else "-",
            "top_score": top_score,
            "hit": is_hit,
            "top_text": top_text,
        })

        if i < len(eval_cases) - 1:
            time.sleep(0.5)

    print(f"\n{'Question':<45} {'Exp':>4} {'Got':>4} {'Score':>7} {'Hit':>5}")
    print("-"*70)
    for r in results_table:
        hit_str = "Yes" if r["hit"] else "No"
        question_preview = f"{r["question"][:40]}..."
        print(
            f"{question_preview:<45} {r['exp_chunk_index']:>4}"
            f"{r['top_index_returned']:>4} {r['top_score']:>7} {hit_str:>5}"
        )
    
    precision = hits / len(eval_cases)
    print(f"\nPrecision@3: {hits}/{len(eval_cases)} = {precision:.0%}")

    misses = [r for r in results_table if not r["hit"]]
    if misses:
        print(f"\nMiss analysis:")
        for r in misses:
            print(f"Q: {r['question']}")
            print(f" Top result preview: {r['top_text']}...")
            print()
    
    return precision

precision = run_evaluation()
