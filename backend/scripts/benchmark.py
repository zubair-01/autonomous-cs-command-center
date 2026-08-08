import asyncio
import os
import sys

# Ensure backend root is in search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from typing import List
import httpx
from utils.log import logger


class APILoadTester:
    """
    OOP Async Load Testing & Latency Benchmarking Tool.
    Floods FastAPI POST /api/v1/tickets endpoint with concurrent async requests,
    measuring throughput (RPS), p50, p95, and p99 response latencies.
    """

    def __init__(self, target_url: str = "http://localhost:8000/api/v1/tickets"):
        self.target_url = target_url
        self.payload = {
            "customer_email": "alice@acme.com",
            "subject": "Benchmark Latency Test Ticket Payload",
            "body": "Simulating concurrent high-throughput HTTP 202 ticket ingestion performance."
        }

    async def _send_single_request(self, client: httpx.AsyncClient) -> float:
        """Sends a single HTTP POST request and returns latency in milliseconds."""
        start_time = time.perf_counter()
        try:
            response = await client.post(self.target_url, json=self.payload, timeout=5.0)
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000.0
            if response.status_code == 202:
                return latency_ms
            else:
                return -1.0
        except Exception:
            return -1.0

    async def run_benchmark(self, total_requests: int = 100, concurrency: int = 20):
        """
        Executes benchmark with specified total requests and concurrency limits.
        """
        print("\n" + "="*65)
        print(f"🚀 STARTING FASTAPI INGESTION BENCHMARK: {total_requests} Requests ({concurrency} Concurrent)")
        print("="*65)

        limits = httpx.Limits(max_keepalive_connections=concurrency, max_connections=concurrency)
        async with httpx.AsyncClient(limits=limits) as client:
            sem = asyncio.Semaphore(concurrency)

            async def worker():
                async with sem:
                    return await self._send_single_request(client)

            start_total = time.perf_counter()
            tasks = [worker() for _ in range(total_requests)]
            results: List[float] = await asyncio.gather(*tasks)
            end_total = time.perf_counter()

        # Calculate metrics
        successful_latencies = [lat for lat in results if lat > 0]
        failed_requests = len(results) - len(successful_latencies)
        total_duration_sec = end_total - start_total
        rps = len(successful_latencies) / total_duration_sec if total_duration_sec > 0 else 0

        if not successful_latencies:
            print("❌ Benchmark failed: All requests failed. Ensure FastAPI server is running on http://localhost:8000!")
            return

        sorted_latencies = sorted(successful_latencies)
        p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        avg_lat = sum(sorted_latencies) / len(sorted_latencies)
        min_lat = sorted_latencies[0]
        max_lat = sorted_latencies[-1]

        print("\n📊 EMPIRICAL LATENCY & THROUGHPUT METRICS:")
        print("-" * 65)
        print(f"  Total Requests Executed:    {total_requests}")
        print(f"  Successful HTTP 202:       {len(successful_latencies)} ({len(successful_latencies)/total_requests*100:.1f}%)")
        print(f"  Failed Requests:           {failed_requests}")
        print(f"  Total Duration:            {total_duration_sec:.2f} seconds")
        print(f"  Throughput (RPS):          {rps:.2f} req/sec")
        print("-" * 65)
        print(f"  ⚡ Average Latency:        {avg_lat:.2f} ms")
        print(f"  ⚡ Min Latency:            {min_lat:.2f} ms")
        print(f"  ⚡ Max Latency:            {max_lat:.2f} ms")
        print(f"  🎯 p50 (Median) Latency:    {p50:.2f} ms")
        print(f"  🎯 p95 (95th percentile):  {p95:.2f} ms  <-- QUOTE THIS IN RESUME!")
        print(f"  🎯 p99 (99th percentile):  {p99:.2f} ms")
        print("=" * 65 + "\n")


if __name__ == "__main__":
    tester = APILoadTester()
    asyncio.run(tester.run_benchmark(total_requests=100, concurrency=20))
