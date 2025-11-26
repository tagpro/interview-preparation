# Design Twitter News Feed

## Functional Requirements
- Users can post tweets (280 chars)
- Users can follow other users
- Users see a feed of tweets from people they follow
- Users can like and retweet

## Non-Functional Requirements
- 200M daily active users
- Average user follows 200 people
- Feed generation should be fast (<300ms)
- High availability, eventual consistency okay
- 100M tweets per day

## Capacity Estimation
- Tweets per second: 100M / 86400 = ~1,200 TPS (avg), peak 6,000 TPS
- Read requests: 200M users * 5 feed refreshes/day = 1B reads/day = ~12K RPS
- Storage: 1,200 tweets/sec * 300 bytes = 360 KB/sec = ~10TB/year

## API Design

```
POST /api/v1/tweet
  body: {user_id, content, media_ids[]}
  
GET /api/v1/feed/{user_id}
  params: {cursor, limit}
  
POST /api/v1/follow
  body: {follower_id, followee_id}
```

## High-Level Architecture

```
Users → Load Balancer → API Servers → Application Layer
                                      ↓
                         ┌────────────┼─────────────┐
                         ↓            ↓             ↓
                    Tweet Service  Feed Service  Graph Service
                         ↓            ↓             ↓
                    Tweet DB     Feed Cache    Follow DB
```

## Database Schema

### Users Table
```
user_id (PK), username, email, created_at
```

### Tweets Table (Cassandra)
```
tweet_id (PK), user_id, content, created_at, like_count, retweet_count
Partition key: user_id, Sort key: created_at (DESC)
```

### Followers Graph (Cassandra)
```
Table 1: follower_id (PK) → [followee_ids]
Table 2: followee_id (PK) → [follower_ids]
```

### Feed Cache (Redis)
```
Key: user:{user_id}:feed
Value: List of tweet_ids (capped at 1000)
```

## Detailed Component Design

### Tweet Creation (Fan-out on Write)

1. User posts tweet → Tweet Service validates and stores in Tweet DB
2. Tweet Service publishes to message queue (Kafka)
3. Fan-out workers consume from queue:
   - For users with <10K followers: Write tweet_id to each follower's feed cache
   - For celebrities (>10K followers): Skip fan-out, use hybrid approach
4. Return success to user immediately after step 1

### Feed Generation (Hybrid Approach)

**For regular users (fan-out on write):**
- Read pre-computed feed from Redis cache
- Merge with any recent tweets from celebrities they follow (fetch on demand)
- Rank and return top N tweets

**For celebrity feeds (fan-out on read):**
- Fetch recent tweets from users they follow from Tweet DB
- Merge and rank in real-time
- Cache result for 30 seconds

### Ranking Algorithm

```
Score = (likes * 2 + retweets * 3) / age_in_hours^1.5
```

- Consider user engagement history
- Use machine learning model for personalization (offline training)

## Scaling Considerations

### Write Path
- Shard Tweet DB by user_id (consistent hashing)
- Use Cassandra for high write throughput
- Kafka for reliable message delivery with multiple partitions
- Multiple fan-out workers for parallel processing

### Read Path
- Redis cluster for feed cache (sharded by user_id)
- CDN for profile images and media
- Read replicas for Tweet DB
- Cache tweet content separately (tweet_id → tweet object)

### Hot Users/Tweets
- Separate cache tier for viral content
- Rate limit fan-out for celebrities
- Use approximate counts for likes/retweets

## Trade-offs

- **Fan-out on write:** Fast reads but expensive writes for celebrities
- **Hybrid approach:** Balances cost and performance
- **Eventual consistency:** Acceptable (follows might take seconds to reflect)
- **Cache invalidation:** Complexity for likes/retweets

## Key Insights

1. **Hybrid fan-out strategy** is essential for handling both regular users and celebrities efficiently
2. **Pre-computing feeds** for most users provides fast read performance
3. **Message queues** decouple tweet creation from feed distribution
4. **Caching at multiple levels** reduces database load significantly
5. **Sharding strategy** must account for uneven distribution (hot users)
