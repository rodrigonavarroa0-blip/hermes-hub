from collections import defaultdict
import heapq

def process_data(records: list[dict]) -> dict:
    if not records:
        return {"top_categories": [], "user_summaries": {}, "suspicious_tx_ids": []}

    cat_totals = defaultdict(float)
    user_totals = defaultdict(float)
    user_counts = defaultdict(int)

    for r in records:
        amt = float(r["amount"])
        cat_totals[r["category"]] += amt
        u = r["user_id"]
        user_totals[u] += amt
        user_counts[u] += 1

    # Using heapq nsmallest with custom sorting key (-total, category)
    top_categories = heapq.nsmallest(3, cat_totals.keys(), key=lambda c: (-cat_totals[c], c))

    user_summaries = {}
    thresholds = {}
    for u, total in user_totals.items():
        cnt = user_counts[u]
        avg = total / cnt
        user_summaries[u] = {
            "total_spent": round(total, 2),
            "avg_spent": round(avg, 2),
            "tx_count": cnt
        }
        thresholds[u] = 3.0 * avg if cnt > 1 else float("inf")

    suspicious = [
        r["id"] for r in records
        if float(r["amount"]) > thresholds[r["user_id"]]
    ]
    suspicious_tx_ids = sorted(set(suspicious))

    return {
        "top_categories": top_categories,
        "user_summaries": user_summaries,
        "suspicious_tx_ids": suspicious_tx_ids
    }
