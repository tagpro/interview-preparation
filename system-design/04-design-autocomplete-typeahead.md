# Design Autocomplete/Typeahead

## Functional Requirements
- Suggest top 5-10 queries as user types
- Suggestions update with each keystroke
- Personalized suggestions based on history
- Support for typos/fuzzy matching
- Trending searches

## Non-Functional Requirements
- 100M daily active users
- 5B searches per day
- Average 5 characters per query prefix
- Response time < 100ms
- High availability

## Capacity Estimation
- QPS: 5B searches/day = 58K QPS
- Suggestion requests: 58K * 5 keystrokes = 290K QPS
- Storage: 100M unique queries * 50 bytes = 5GB
- Trie storage: ~10GB with metadata

## API Design

```
GET /api/v1/suggestions
  params: {prefix, user_id?, limit=10}
  response: {suggestions: [{query, score, type}]}
  
POST /api/v1/search
  body: {query, user_id}
  - Logs search for analytics
```

## High-Level Architecture

```
Users → Load Balancer → API Servers
                            ↓
                    ┌───────┴────────┐
                    ↓                ↓
            Suggestion Service   Search Service
                    ↓                ↓
            Trie Servers        Query Logs
            (In-memory)          (Cassandra)
                    ↑                
            Offline Processing
            (Spark/Hadoop)
```

## Data Structure - Trie

```
class TrieNode:
    children: Dict[char, TrieNode]
    is_end: bool
    top_suggestions: List[(query, score)]  # Pre-computed
    frequency: int

Example Trie:
         root
         /  \
        c    d
       /      \
      a        o
     / \        \
    t   r        g
   /     \
  (cat)  (car)  (dog)

Each node stores top 10 suggestions for that prefix
```

## Building the Trie

```python
# Offline processing (daily)
1. Aggregate query logs
2. Count query frequencies
3. Calculate scores:
   score = frequency * recency_factor * CTR_weight
   
4. Build trie:
   for query, score in sorted_queries:
       insert_into_trie(query, score)
       
5. For each node, store top 10 queries:
   node.top_suggestions = heapify(all_queries_with_prefix)
   
6. Serialize trie
7. Distribute to suggestion servers
```

## Database Schema

### Query Logs (Cassandra)
```
query_id, query_text, user_id, timestamp, 
clicked, position_clicked
Partition key: date
Sort key: timestamp
```

### User Search History (Redis)
```
Key: user:{user_id}:history
Value: List of recent queries (last 100)
TTL: 30 days
```

### Trending Queries (Redis)
```
Key: trending:global
Value: Sorted set (query → score)
Update: Every 10 minutes
```

## Detailed Component Design

### Suggestion Generation

**Query Processing:**
```
1. Receive prefix: "pyth"
2. Normalize: lowercase, trim
3. Traverse trie to node for "pyth"
4. Retrieve node.top_suggestions (pre-computed)
5. Merge with personalized suggestions
6. Apply filters (profanity, banned terms)
7. Return top 10
```

**Personalization:**
```
1. Fetch user's search history from Redis
2. Boost suggestions matching user's interests
3. Blend:
   - 70% global popular suggestions
   - 20% personalized based on history
   - 10% trending suggestions
```

**Ranking Score:**
```
score = 
  0.4 * frequency_score +
  0.2 * recency_score +
  0.2 * CTR_score +
  0.1 * personalization_score +
  0.1 * trending_score

Where:
- frequency_score: Normalized query count
- recency_score: Decay function (recent queries higher)
- CTR_score: Click-through rate for that suggestion
- personalization_score: Match with user history
- trending_score: Current popularity spike
```

## Fuzzy Matching

### Handling Typos
```
1. Exact match first
2. If < 5 results, apply fuzzy matching:
   - Edit distance (Levenshtein distance ≤ 2)
   - Phonetic matching (Soundex, Metaphone)
   - Common typo corrections (stored separately)
   
3. Build fuzzy trie with common misspellings:
   "python" → also stored under "pyton", "phyton"
```

**Implementation:**
```
- Store prefix variations in trie
- Use BK-tree for efficient fuzzy search
- Pre-compute common typos during offline processing
```

## Trending Queries

### Real-time Trending
```
1. Stream query logs to Kafka
2. Spark Streaming job:
   - Window: Last 1 hour
   - Count queries
   - Compare to historical baseline
   - Detect spikes (> 3x normal)
3. Update Redis trending set
4. Merge into suggestions with high weight
```

## Scaling Considerations

### Trie Distribution

**Approach 1: Replicate entire trie**
```
- Each server has full trie in memory
- Simple, fast lookups
- Good for < 10GB trie
```

**Approach 2: Partition by prefix**
```
- Shard by first 2 characters: 26^2 = 676 shards
- "py*" queries → server handling "py"
- Reduces memory per server
- Need routing layer
```

### Caching Strategy

```
L1: Application cache (in-memory)
- Cache top 10K prefixes
- LRU eviction
- Hit rate ~70%

L2: Redis distributed cache
- Cache all prefixes
- TTL: 1 hour
- Hit rate ~95%

L3: Trie servers
- Fallback for cache misses
```

### Update Strategy

**Offline updates (daily):**
```
1. Build new trie from aggregated logs
2. Serialize to files
3. Gradually roll out to servers
4. A/B test new suggestions
5. Complete rollout after validation
```

**Online updates (streaming):**
```
1. Hot queries detected in real-time
2. Update small delta trie
3. Merge with main trie
4. Push to servers via gossip protocol
```

## Geographic Distribution

```
- Different tries for different languages
- Location-based trending queries
- CDN-like architecture: Regional trie servers
- User routes to nearest server
```

## Performance Optimizations

### Prefix Compression
```
- Compress common prefixes
- Patricia Trie instead of standard Trie
- Reduces memory by ~40%
```

### Query Optimization
```
- Pre-compute suggestions at each node
- No runtime computation needed
- Trade memory for speed
```

### Client-side
```
- Debounce requests (wait 100ms after keystroke)
- Cancel pending requests
- Cache responses on client
- Predict next character (prefetch)
```

## Trade-offs

- **Memory vs Speed:** Pre-computed vs runtime computation
- **Freshness vs Consistency:** Real-time updates vs batch updates
- **Personalization vs Privacy:** Tracking history vs anonymous
- **Global vs Local:** Single trie vs regional tries

## Key Insights

1. **Trie data structure** enables fast prefix-based lookups
2. **Pre-computing suggestions** at each node eliminates runtime overhead
3. **Caching at multiple levels** reduces latency significantly
4. **Personalization blending** balances global popularity with user preferences
5. **Offline batch processing** handles heavy computation without affecting queries
6. **Fuzzy matching** improves user experience for typos
