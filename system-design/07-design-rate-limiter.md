# Design Rate Limiter

## Functional Requirements
- Limit requests per user/IP/API key
- Multiple time windows (per second, minute, hour)
- Different limits for different endpoints
- Return clear error messages (429 Too Many Requests)
- Allow burst traffic within limits

## Non-Functional Requirements
- Low latency (< 5ms overhead)
- Highly available
- Accurate rate limiting
- Distributed system support
- 1M requests/second throughput

## API Design

```
# Rate limiter as middleware
GET /api/v1/resource
Headers:
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 42
  X-RateLimit-Reset: 1609459200

If exceeded:
  Status: 429 Too Many Requests
  Headers:
    Retry-After: 60
  Body: {error: "Rate limit exceeded"}
```

## Rate Limiting Algorithms

### 1. Fixed Window Counter

**Simple counter per time window**
```
- Reset at window boundary

Example: 100 requests per minute
- Window: 10:00:00 - 10:00:59
- Counter starts at 0
- Increment on each request
- Reset to 0 at 10:01:00

Redis implementation:
key = "user:123:minute:10:00"
INCR key
EXPIRE key 60
if count > limit: reject

Problem: Burst at window edges
- 100 requests at 10:00:59
- 100 requests at 10:01:00
- = 200 requests in 2 seconds!
```

### 2. Sliding Window Log

**Store timestamp of each request**
```
- Count requests in last N seconds

Redis implementation:
key = "user:123:requests"
current_time = now()
window_start = current_time - 60

# Add current request
ZADD key current_time request_id

# Remove old entries
ZREMRANGEBYSCORE key 0 window_start

# Count requests in window
count = ZCOUNT key window_start current_time

if count > limit: reject

Pros: Accurate, no edge bursts
Cons: Memory intensive (stores all timestamps)
```

### 3. Sliding Window Counter (Recommended)

**Hybrid of fixed window and sliding log**
```
- More accurate than fixed, less memory than log

Algorithm:
previous_window_count * overlap_percentage + current_window_count

Example: 100 req/minute, current time 10:00:45
- Previous window (09:59-10:00): 80 requests
- Current window (10:00-10:01): 30 requests
- Overlap: 75% of previous (45 seconds)
- Estimated count: 80 * 0.25 + 30 = 50 requests
- Allow: 50 < 100 ✓

Redis implementation:
current_window = floor(timestamp / 60)
previous_window = current_window - 1

current_count = GET "user:123:#{current_window}"
previous_count = GET "user:123:#{previous_window}"

weight = (60 - (timestamp % 60)) / 60
estimated = previous_count * weight + current_count

if estimated > limit: reject
else: INCR "user:123:#{current_window}"
```

### 4. Token Bucket (Recommended for burst)

**Bucket holds tokens**
```
- Tokens added at fixed rate
- Request consumes token
- Allows burst if bucket has tokens

Parameters:
- bucket_capacity: Max tokens (burst size)
- refill_rate: Tokens per second

Example: 10 requests/sec, burst of 20
- Capacity: 20 tokens
- Refill: 10 tokens/sec
- Can handle 20 instant requests, then 10/sec

Redis implementation:
key = "user:123:bucket"
current_time = now()

# Get bucket state
tokens, last_refill = HMGET key "tokens", "last_refill"

# Calculate new tokens
time_passed = current_time - last_refill
new_tokens = time_passed * refill_rate
tokens = min(bucket_capacity, tokens + new_tokens)

if tokens >= 1:
    tokens -= 1
    HSET key "tokens" tokens "last_refill" current_time
    allow request
else:
    reject
```

### 5. Leaky Bucket

**Similar to token bucket**
```
- Requests leak out at fixed rate
- Smooth out bursts

Queue implementation:
- Requests enter queue
- Process at fixed rate
- Queue full = reject

Good for: Consistent output rate
Not good for: Interactive APIs (adds latency)
```

## High-Level Architecture

```
Client → Load Balancer → Rate Limiter → API Servers
                              ↓
                         Redis Cluster
                      (Rate limit counters)
                              ↓
                       Rules Service
                    (Limit configurations)
```

## Detailed Design

### Rate Limiter Service

```python
class RateLimiter:
    def __init__(self, redis_client, rules_service):
        self.redis = redis_client
        self.rules = rules_service
    
    def is_allowed(self, user_id, endpoint, timestamp):
        # Get applicable rules
        rules = self.rules.get_rules(user_id, endpoint)
        
        for rule in rules:
            key = f"{rule.scope}:{user_id}:{endpoint}:{rule.window}"
            limit = rule.limit
            
            if rule.algorithm == "sliding_window":
                allowed = self.check_sliding_window(key, limit, timestamp)
            elif rule.algorithm == "token_bucket":
                allowed = self.check_token_bucket(key, rule.capacity, rule.rate)
            
            if not allowed:
                return False, rule.window  # Blocked, retry after
        
        return True, None  # Allowed
```

## Rules Configuration

```json
{
  "rules": [
    {
      "endpoint": "/api/v1/search",
      "scope": "user",
      "limits": [
        {"window": "1s", "max": 10, "algorithm": "token_bucket"},
        {"window": "1m", "max": 100, "algorithm": "sliding_window"},
        {"window": "1h", "max": 1000, "algorithm": "sliding_window"}
      ]
    },
    {
      "endpoint": "/api/v1/upload",
      "scope": "ip",
      "limits": [
        {"window": "1m", "max": 5, "algorithm": "fixed_window"}
      ]
    }
  ],
  "user_tiers": {
    "free": {"multiplier": 1.0},
    "premium": {"multiplier": 10.0}
  }
}
```

## Distributed Rate Limiting

### Challenge
```
- Multiple API servers
- Need coordinated rate limiting
- Race conditions in distributed system
```

### Solution 1: Centralized Redis

**Pros:**
```
- Accurate counts
- Consistent across servers
- Simple implementation
```

**Cons:**
```
- Single point of failure
- Network latency
- Redis becomes bottleneck
```

**Mitigation:**
```
- Redis Cluster (sharded)
- Redis Sentinel (high availability)
- Connection pooling
```

### Solution 2: Local Cache + Redis (Hybrid)

```
1. Each server maintains local counter (in-memory)
2. Sync to Redis periodically (every 100ms)
3. Read from Redis for accurate count
4. Local counter for fast decision

Trade-off:
- Slightly inaccurate (overages possible)
- Much faster (no network call per request)
- Good for high throughput

Implementation:
local_count = increment_local_counter()
if local_count > threshold:
    redis_count = sync_with_redis()
    if redis_count > limit:
        reject
```

### Solution 3: Consistent Hashing

```
- Hash user_id to specific rate limiter instance
- All requests for user go to same instance
- Reduces need for coordination

Problem: Uneven distribution, hotspots
```

## Scaling Considerations

### Redis Cluster

```
- Shard by rate limit key (user_id, ip, api_key)
- Hash slot distribution
- Replicate each shard (primary + replicas)
- Automatic failover

Capacity:
- 1M req/sec * 10 bytes per counter = 10 MB/sec
- Redis handles 100K ops/sec per instance
- Need 10 Redis instances
- With replication: 30 instances total
```

### Performance Optimization

```
- Lua scripts for atomic operations
- Pipelining multiple Redis commands
- Connection pooling
- Async processing (don't block request)
```

## Monitoring & Observability

### Metrics to track
```
- Rate limit hit rate
- Rejected requests by endpoint
- Redis latency (p50, p95, p99)
- False positives/negatives
```

### Alerts
```
- High rejection rate (DDoS?)
- Redis latency spike
- Uneven traffic distribution
```

### Logging
```
- Log every rejected request
- Include: user_id, endpoint, current_count, limit
- Aggregate for analysis
```

## Advanced Features

### Dynamic Rate Limits

```
- Adjust based on system load
- Reduce limits during incidents
- Increase for premium users automatically

Circuit breaker integration:
- If downstream service struggling, tighten limits
- Protect backend from overload
```

### Whitelist/Blacklist

```
- Whitelist: Internal services, admins (bypass rate limit)
- Blacklist: Known bad actors (immediate rejection)
- Store in Redis with high priority check
```

### Geographic Distribution

```
- Different limits per region
- Account for time zones (peak hours vary)
- Regional Redis clusters
```

### Usage Analytics

```
- Track usage patterns per user
- Identify power users for upsell
- Detect anomalies (compromised accounts)
- Feed into billing system
```

## Trade-offs

- **Accuracy vs Performance:** Strict vs lenient rate limiting
- **Fixed vs Sliding:** Simple vs accurate
- **Centralized vs Distributed:** Consistency vs latency
- **Rejection at edge vs backend:** Early rejection vs context-aware limiting

## Key Insights

1. **Sliding window counter** provides good balance of accuracy and performance
2. **Token bucket** allows controlled bursts while maintaining average rate
3. **Redis clustering** handles distributed coordination efficiently
4. **Multiple time windows** (second, minute, hour) catch different abuse patterns
5. **Rules engine** enables flexible configuration without code changes
6. **Monitoring and alerting** essential for detecting attacks and misconfigurations
