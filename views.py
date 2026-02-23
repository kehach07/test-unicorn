rom fastapi import FastAPI
from pydantic import BaseModel
import time
import hashlib
from datetime import datetime, timedelta
from collections import OrderedDict
import math

app = FastAPI(title="OptimizeAI Intelligent Cache")

# =========================
# Config
# =========================
TTL_HOURS = 24
MAX_CACHE_SIZE = 2000
MODEL_COST_PER_TOKEN = 0.50 / 1_000_000
AVG_TOKENS = 500

# =========================
# Data Models
# =========================
class QueryRequest(BaseModel):
    query: str
    application: str


# =========================
# Cache Storage (LRU)
# =========================
cache = OrderedDict()
embeddings_store = {}

# Analytics
total_requests = 0
cache_hits = 0
cache_misses = 0
cached_tokens = 0


# =========================
# Utilities
# =========================

def md5_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def fake_embedding(text):
    # Simple embedding simulation
    vec = [0]*10
    for i, ch in enumerate(text.lower()):
        vec[i % 10] += ord(ch)
    norm = math.sqrt(sum(v*v for v in vec))
    return [v/norm for v in vec] if norm != 0 else vec


def cosine_sim(v1, v2):
    return sum(a*b for a, b in zip(v1, v2))


def semantic_search(query_emb):
    for key, emb in embeddings_store.items():
        if cosine_sim(query_emb, emb) > 0.95:
            return key
    return None


def fake_llm(query):
    # Simulate LLM latency
    time.sleep(0.8)
    return f"Answer to: {query}"


def clean_expired():
    now = datetime.utcnow()
    expired_keys = [
        k for k, v in cache.items()
        if now - v["timestamp"] > timedelta(hours=TTL_HOURS)
    ]
    for k in expired_keys:
        cache.pop(k, None)
        embeddings_store.pop(k, None)


def lru_insert(key, value, embedding):
    if key in cache:
        cache.move_to_end(key)
    cache[key] = value
    embeddings_store[key] = embedding

    if len(cache) > MAX_CACHE_SIZE:
        old_key, _ = cache.popitem(last=False)
        embeddings_store.pop(old_key, None)


# =========================
# Main Endpoint
# =========================
@app.post("/")
def query_llm(req: QueryRequest):
    global total_requests, cache_hits, cache_misses, cached_tokens

    start = time.time()
    total_requests += 1
    clean_expired()

    query = req.query.strip()
    key = md5_hash(query)

    # Exact match
    if key in cache:
        cache_hits += 1
        cache.move_to_end(key)
        latency = int((time.time() - start) * 1000)

        return {
            "answer": cache[key]["answer"],
            "cached": True,
            "latency": latency,
            "cacheKey": key
        }

    # Semantic match
    emb = fake_embedding(query)
    semantic_key = semantic_search(emb)

    if semantic_key:
        cache_hits += 1
        cache.move_to_end(semantic_key)
        latency = int((time.time() - start) * 1000)

        return {
            "answer": cache[semantic_key]["answer"],
            "cached": True,
            "latency": latency,
            "cacheKey": semantic_key
        }

    # Cache miss
    cache_misses += 1
    answer = fake_llm(query)

    timestamp = datetime.utcnow()
    record = {
        "answer": answer,
        "timestamp": timestamp
    }

    lru_insert(key, record, emb)

    latency = int((time.time() - start) * 1000)

    return {
        "answer": answer,
        "cached": False,
        "latency": latency,
        "cacheKey": key
    }


# =========================
# Analytics Endpoint
# =========================
@app.get("/analytics")
def analytics():
    total_tokens = total_requests * AVG_TOKENS
    uncached_tokens = cache_misses * AVG_TOKENS
    saved_tokens = total_tokens - uncached_tokens

    baseline_cost = total_tokens * MODEL_COST_PER_TOKEN
    actual_cost = uncached_tokens * MODEL_COST_PER_TOKEN
    savings = baseline_cost - actual_cost

    hit_rate = cache_hits / total_requests if total_requests else 0

    return {
        "hitRate": round(hit_rate, 2),
        "totalRequests": total_requests,
        "cacheHits": cache_hits,
        "cacheMisses": cache_misses,
        "cacheSize": len(cache),
        "costSavings": round(savings, 2),
        "savingsPercent": round(hit_rate * 100, 2),
        "strategies": [
            "exact match",
            "semantic similarity",
            "LRU eviction",
            "TTL expiration"
        ]
    }


# =========================
# Health Check
# =========================
@app.get("/")
def root():
    return {"status": "Intelligent cache running"}
