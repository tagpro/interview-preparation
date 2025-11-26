# Design URL Shortener

## Functional Requirements
- Generate short URL from long URL
- Redirect short URL to original URL
- Optional custom aliases
- Analytics (click tracking)
- Expiration after certain time

## Non-Functional Requirements
- 100M URLs shortened per month
- 10:1 read/write ratio
- Low latency (<100ms)
- Shortened URLs should be 7 characters
- 10 year retention

## Capacity Estimation
- Writes: 100M/month = ~40 writes/sec
- Reads: 400 reads/sec
- Storage: 100M URLs/month * 500 bytes = 50GB/month = 6TB for 10 years
- Unique URLs needed: 100M * 12 * 10 = 12B URLs
- With base62: 62^7 = 3.5 trillion combinations (sufficient)

## API Design

```
POST /api/v1/shorten
  body: {long_url, custom_alias?, expiration?}
  response: {short_url, created_at}
  
GET /{short_code}
  response: 302 redirect to long_url
  
GET /api/v1/analytics/{short_code}
  response: {clicks, locations, referrers}
```

## Database Schema

### URL Mappings (PostgreSQL)
```
id, short_code (indexed), long_url, user_id, 
created_at, expires_at, click_count
```

### Analytics (Cassandra)
```
short_code, timestamp, ip_address, user_agent, 
referrer, country
Partition key: short_code, Sort key: timestamp
```

## Short Code Generation

### Approach 1: Counter-based (Recommended)

```
1. Use distributed counter (Redis or Zookeeper)
2. Get next counter value
3. Encode counter in base62: [0-9a-zA-Z]
4. Counter range: Each app server gets range (1M-2M, 2M-3M)
```

**Base62 encoding:**
```python
def encode(num):
    chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = ""
    while num > 0:
        result = chars[num % 62] + result
        num //= 62
    return result.rjust(7, '0')
```

### Approach 2: Hash-based

```
1. MD5(long_url) → 128 bit hash
2. Take first 43 bits, encode in base62
3. Handle collisions with random salt or counter
Problem: Harder to guarantee uniqueness
```

## High-Level Architecture

```
User → CDN → Load Balancer → API Servers
                                   ↓
                        ┌──────────┴─────────┐
                        ↓                    ↓
                  Redis Cache          PostgreSQL
                  (URL mappings)       (Persistent store)
                        ↓
                 Range Service ──→ Zookeeper
                 (Generate IDs)
                        ↓
                  Cassandra
                  (Analytics)
```

## Detailed Flow

### URL Shortening

1. Check if long_url already exists (hash index)
2. If exists, return existing short_code
3. If new:
   - Get next ID from range service
   - Encode to base62
   - Store mapping in DB
   - Cache in Redis (TTL 24 hours)
4. Return short URL

### URL Redirection

1. Check Redis cache (hot URLs)
2. If miss, query PostgreSQL
3. If found:
   - Increment click counter (async)
   - Log analytics event to Kafka
   - Return 302 redirect
4. Cache the mapping (TTL varies by popularity)

## Scaling Considerations

### Database
- PostgreSQL with read replicas
- Shard by hash(short_code) if needed
- Index on short_code for fast lookups
- Separate hot URLs in faster storage tier

### Caching
- Redis cluster (sharded by short_code)
- 80/20 rule: Cache top 20% URLs
- LRU eviction policy
- Write-through cache for new URLs

### Range Service
- Zookeeper to coordinate ID ranges
- Each server gets 1M ID range
- Preload next range before current exhausted
- Prevents collisions across servers

### Analytics
- Write to Kafka buffer (async)
- Batch write to Cassandra
- Separate from critical path
- Partition by short_code for query efficiency

## Custom Aliases
- Check uniqueness before assignment
- Reserve some patterns (admin, api, etc.)
- Handle race conditions with unique constraint

## Expiration
- Background job scans for expired URLs
- Lazy deletion on access
- Archive analytics before deletion

## Trade-offs

- **Counter-based:** Sequential codes (predictable but simple)
- **Hash-based:** Random codes (less predictable but collision handling)
- **302 vs 301:** 302 allows analytics, 301 better caching
- **Sync vs async analytics:** Async better for latency, eventual consistency

## Key Insights

1. **Base62 encoding** provides compact, URL-safe short codes
2. **Range-based ID generation** prevents collisions in distributed systems
3. **Caching strategy** is critical for handling read-heavy workload
4. **Async analytics** keeps redirect path fast
5. **Pre-checking for duplicates** saves storage and provides consistent short URLs
