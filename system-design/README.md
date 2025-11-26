# System Design Interview Problems - Complete Guide

This collection contains detailed system design solutions for the most common interview questions. Each document covers functional/non-functional requirements, capacity estimation, API design, architecture, database schema, detailed components, scaling considerations, and trade-offs.

## Documents Overview

### 1. Design Twitter News Feed
**File:** [01-design-twitter-news-feed.md](01-design-twitter-news-feed.md)

**Key Topics:**
- Fan-out on write vs fan-out on read
- Hybrid approach for celebrities
- Redis feed caching
- Cassandra for tweets
- Message queues (Kafka)
- Ranking algorithms

**Complexity:** Medium-High
**Best For:** Understanding social media feeds, caching strategies, fan-out patterns

---

### 2. Design URL Shortener
**File:** [02-design-url-shortener.md](02-design-url-shortener.md)

**Key Topics:**
- Base62 encoding
- Counter-based vs hash-based ID generation
- Redis caching
- Analytics tracking
- Custom aliases
- Distributed ID generation

**Complexity:** Medium
**Best For:** Understanding encoding, distributed counters, caching strategies

---

### 3. Design WhatsApp
**File:** [03-design-whatsapp.md](03-design-whatsapp.md)

**Key Topics:**
- WebSocket connections
- Real-time messaging
- Message queuing (Kafka)
- Session management
- Group chat fan-out
- End-to-end encryption
- Delivery receipts

**Complexity:** High
**Best For:** Understanding real-time systems, WebSockets, message delivery guarantees

---

### 4. Design Autocomplete/Typeahead
**File:** [04-design-autocomplete-typeahead.md](04-design-autocomplete-typeahead.md)

**Key Topics:**
- Trie data structure
- Pre-computed suggestions
- Fuzzy matching
- Trending queries
- Personalization
- Multi-level caching

**Complexity:** Medium
**Best For:** Understanding tries, prefix search, caching strategies, personalization

---

### 5. Design Dropbox
**File:** [05-design-dropbox.md](05-design-dropbox.md)

**Key Topics:**
- File chunking
- Deduplication
- Synchronization protocols
- Conflict resolution
- Versioning
- Block storage
- Delta sync

**Complexity:** High
**Best For:** Understanding file storage, sync algorithms, deduplication, conflict resolution

---

### 6. Design Uber
**File:** [06-design-uber.md](06-design-uber.md)

**Key Topics:**
- Geospatial indexing (QuadTree, Geohash)
- Real-time location tracking
- Matching algorithms
- Dynamic pricing (surge)
- ETA calculation
- WebSocket connections
- Payment processing

**Complexity:** High
**Best For:** Understanding geospatial systems, real-time tracking, matching algorithms

---

### 7. Design Rate Limiter
**File:** [07-design-rate-limiter.md](07-design-rate-limiter.md)

**Key Topics:**
- Token bucket algorithm
- Sliding window counter
- Fixed window counter
- Distributed rate limiting
- Redis for state management
- Multiple time windows
- Rules engine

**Complexity:** Medium
**Best For:** Understanding rate limiting algorithms, distributed coordination, Redis usage

---

### 8. Design YouTube
**File:** [08-design-youtube.md](08-design-youtube.md)

**Key Topics:**
- Video transcoding pipeline
- Adaptive bitrate streaming (HLS/DASH)
- Multi-tier CDN
- Recommendation algorithms
- Search with Elasticsearch
- View counting at scale
- Event streaming

**Complexity:** Very High
**Best For:** Understanding video streaming, CDNs, ML recommendations, large-scale systems

---

## Common Patterns Across All Designs

### Database Choices
- **Cassandra:** High write throughput (messages, tweets, logs)
- **PostgreSQL:** Strong consistency, relational data (user accounts, transactions)
- **Redis:** Caching, session storage, counters
- **Elasticsearch:** Full-text search, analytics

### Caching Strategies
- **Multi-level caching:** Client → CDN → Application → Database
- **Cache invalidation:** TTL-based, event-driven
- **Cache-aside vs write-through:** Read-heavy vs write-heavy workloads

### Scaling Patterns
- **Horizontal scaling:** Add more servers
- **Sharding:** Partition data across databases
- **Replication:** Read replicas for read-heavy workloads
- **Message queues:** Async processing, decoupling

### Communication Patterns
- **REST APIs:** Synchronous, request-response
- **WebSockets:** Real-time, bidirectional
- **Message Queues:** Async, pub-sub (Kafka, RabbitMQ)

### Storage Solutions
- **Blob storage:** S3, MinIO (videos, images, files)
- **Relational DB:** PostgreSQL, MySQL (structured data)
- **NoSQL:** Cassandra, MongoDB (semi-structured, high throughput)
- **Time-series DB:** InfluxDB, TimescaleDB (metrics, logs)

---

## Interview Approach

### 1. Clarify Requirements (5 min)
- Functional requirements
- Non-functional requirements (scale, latency, consistency)
- Constraints and assumptions

### 2. Back-of-envelope Estimation (5 min)
- Users, requests per second
- Storage requirements
- Bandwidth requirements

### 3. High-level Design (10 min)
- Draw main components
- Explain data flow
- Identify bottlenecks

### 4. Detailed Design (15 min)
- API design
- Database schema
- Deep dive into 2-3 components
- Scaling strategies

### 5. Trade-offs and Discussion (5 min)
- Consistency vs availability
- Latency vs throughput
- Cost vs performance
- Alternative approaches

---

## Key Takeaways

### Always Consider
1. **Scalability:** How does it handle 10x, 100x traffic?
2. **Reliability:** What happens when things fail?
3. **Performance:** What are the latency requirements?
4. **Maintainability:** How complex is the system?
5. **Cost:** What's the infrastructure cost?

### Common Mistakes to Avoid
- Jumping to details too quickly
- Not asking clarifying questions
- Ignoring non-functional requirements
- Over-engineering simple problems
- Not discussing trade-offs

### Pro Tips
- Draw diagrams, don't just talk
- Think out loud, explain your reasoning
- Start simple, then add complexity
- Acknowledge what you don't know
- Relate to real-world systems you've used

---

## Additional Resources

### Books
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "System Design Interview" by Alex Xu (Volumes 1 & 2)

### Online
- ByteByteGo (YouTube)
- Gaurav Sen (YouTube)
- System Design Primer (GitHub)

### Practice
- Mock interviews on platforms like Pramp, Interviewing.io
- Study real system architectures (blogs from Netflix, Uber, Twitter)
- Build small versions of these systems

---

Good luck with your system design interviews!
