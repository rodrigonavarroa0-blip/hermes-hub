import time
import sys
from pathlib import Path

# Add the hermes-hub to path so we can import mcp_server
hub_path = Path.home() / ".hermes-hub"
sys.path.append(str(hub_path / "config"))

try:
    import mcp_server
except ImportError as e:
    print(f"Error importing mcp_server: {e}")
    sys.exit(1)

def run_benchmark():
    print("--- BENCHMARK START ---")
    
    # 1. Measure Cold Start (Loading the Graph)
    t0 = time.perf_counter()
    engine = mcp_server.get_engine()
    cold_start_time = (time.perf_counter() - t0) * 1000
    print(f"Cold Start (Graph Load + Token Indexing): {cold_start_time:.2f} ms")
    print(f"Nodes loaded: {len(engine.nodes)}")
    print(f"Edges loaded: {len(engine.edges)}")

    # Clear cache to measure raw activation time
    mcp_server._QUERY_CACHE.clear()

    # 2. Measure Query Latency (Spreading Activation)
    queries = [
        "React and Next.js optimization",
        "Python backend database connections",
        "How to configure Supabase row level security",
        "Agile project management tips",
        "What is the meaning of life?",
        "Security vulnerabilities in Docker",
        "Kubernetes orchestration scaling",
        "Machine learning neural networks",
        "Frontend css typography tailwind",
        "Backend event driven architecture pub sub kafka"
    ]
    
    total_time = 0
    total_queries = 0
    
    # Run each query 10 times
    for q in queries:
        for _ in range(10):
            # Clear cache so we test actual computation
            mcp_server._QUERY_CACHE.clear()
            
            t_start = time.perf_counter()
            # Disable auto reinforce to measure just the activation logic
            mcp_server.resolve_context(q, top_k=5, auto_reinforce=False)
            t_end = time.perf_counter()
            
            total_time += (t_end - t_start)
            total_queries += 1

    avg_time_ms = (total_time / total_queries) * 1000
    print(f"Average Query Latency ({total_queries} runs): {avg_time_ms:.3f} ms")
    print("--- BENCHMARK END ---")
    
    # Save results to file for comparison
    with open("benchmark_results.txt", "a") as f:
        f.write(f"{cold_start_time:.2f},{avg_time_ms:.3f}\n")

if __name__ == "__main__":
    run_benchmark()
