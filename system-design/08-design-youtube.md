# Design YouTube

## Functional Requirements
- Upload videos
- Stream videos (adaptive bitrate)
- Search videos
- Recommendations
- Comments, likes, subscriptions
- Analytics (view count, watch time)

## Non-Functional Requirements
- 2B users, 500M daily active
- 500 hours of video uploaded per minute
- 1B videos in catalog
- 5 million concurrent viewers
- Multiple resolutions (1080p, 720p, 480p, 360p)
- Low latency streaming (<2 seconds)

## Capacity Estimation
- Video uploads: 500 hours/min = 30K hours/day
- Average video size (compressed): 1GB/hour
- Storage per day: 30K * 1GB = 30TB/day = 11PB/year
- With encoding (multiple resolutions): 11PB * 5 = 55PB/year
- Bandwidth: 5M viewers * 5Mbps = 25 Terabits/sec
- Metadata: 1B videos * 10KB = 10TB

## API Design

```
POST /api/v1/videos/upload
  multipart: {video_file, title, description, tags[], thumbnail}
  response: {video_id, processing_status}
  
GET /api/v1/videos/{video_id}/stream
  params: {resolution, start_time}
  response: Video stream (HLS/DASH manifest)
  
GET /api/v1/videos/search
  params: {query, filters}
  
POST /api/v1/videos/{video_id}/view
  body: {user_id, watch_time}
  
GET /api/v1/recommendations
  params: {user_id}
```

## High-Level Architecture

```
Users → CDN → Origin Servers
             ↓
Upload → Processing Pipeline → Storage (S3)
             ↓
        Transcode Workers
             ↓
        Thumbnail Generation
             ↓
        Metadata Extraction
             ↓
      Database (Cassandra)
             ↓
      Search Index (Elasticsearch)
             ↓
   Recommendation Engine (ML)
```

## Database Schema

### Videos (Cassandra)
```
video_id (PK), user_id, title, description, 
upload_date, duration, view_count, like_count,
status (processing/ready), thumbnail_url, tags[]
Partition key: video_id
```

### Users
```
user_id (PK), username, email, subscriber_count,
total_views
```

### Video Files (Metadata)
```
video_id, resolution, format, file_path (S3), 
size, bitrate, codec
```

### Comments (Cassandra)
```
comment_id (PK), video_id, user_id, text, 
timestamp, likes, parent_comment_id
Partition key: video_id
Sort key: timestamp (DESC)
```

### Subscriptions
```
user_id (PK), subscribed_to[], subscription_date
```

### View History (Cassandra)
```
user_id, video_id, timestamp, watch_duration,
completion_percentage
Partition key: user_id
Sort key: timestamp (DESC)
```

## Detailed Component Design

### Video Upload & Processing

**Upload Flow:**
```
1. Client initiates upload
   - POST /api/v1/videos/upload/initiate
   - Server returns upload_id and presigned S3 URL

2. Client uploads directly to S3
   - Chunked upload (multipart)
   - Resume on failure
   - Progress tracking

3. Upload completion callback
   - S3 triggers Lambda/SNS
   - Publishes to processing queue (Kafka)

4. Video Processing Pipeline starts
```

**Processing Pipeline:**
```
1. Download original video from S3

2. Extract metadata:
   - Resolution, duration, codec, bitrate
   - FFprobe for video analysis
   
3. Generate thumbnail:
   - Extract frame at 10% of video
   - Create multiple sizes (SD, HD)
   - Upload to S3

4. Transcode to multiple resolutions:
   - 1080p (5 Mbps)
   - 720p (2.5 Mbps)
   - 480p (1 Mbps)
   - 360p (500 Kbps)
   - 240p (250 Kbps)
   
   FFmpeg command:
   ffmpeg -i input.mp4 \
     -vf scale=1920:1080 -b:v 5M output_1080p.mp4 \
     -vf scale=1280:720 -b:v 2.5M output_720p.mp4 \
     ...

5. Generate adaptive bitrate streaming:
   - HLS (Apple): .m3u8 playlist + .ts segments
   - DASH (universal): .mpd manifest + .mp4 segments
   - Segment size: 10 seconds each
   
6. Upload all versions to S3

7. Update database:
   - Video status = "ready"
   - Store all file paths
   - Publish notification

Parallelization:
- Multiple workers transcode different resolutions simultaneously
- Use spot instances for cost savings
- Queue depth monitoring (scale workers)
```

## Video Streaming (Adaptive Bitrate)

### HLS (HTTP Live Streaming)

**Master playlist (video_id.m3u8):**
```
#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
720p/playlist.m3u8
...
```

**Individual playlist (1080p/playlist.m3u8):**
```
#EXTM3U
#EXT-X-TARGETDURATION:10
#EXTINF:10.0,
segment0.ts
#EXTINF:10.0,
segment1.ts
...
```

**Client:**
```
1. Fetch master playlist
2. Choose resolution based on bandwidth
3. Fetch individual playlist
4. Download segments sequentially
5. Monitor bandwidth, switch quality as needed
```

### Streaming Flow

```
1. Client requests video: GET /api/v1/videos/{video_id}/stream

2. Server returns manifest URL (CDN):
   https://cdn.youtube.com/videos/{video_id}/master.m3u8

3. Client fetches manifest from CDN
   - CDN cache hit: Instant response
   - CDN cache miss: Fetch from origin, cache

4. Client downloads video segments
   - Adaptive bitrate selection
   - Prefetch next segments
   - Buffer management (30 seconds ahead)

5. View tracking:
   - Heartbeat every 30 seconds
   - Report watch time to analytics
```

## Content Delivery Network (CDN)

### Multi-tier caching

**Edge Servers (PoPs):**
```
- Distributed globally (200+ locations)
- Cache popular videos
- LRU eviction
- 80% of traffic served from edge
```

**Regional Servers:**
```
- Fewer locations (20-30)
- Larger cache (hot + warm content)
- Fallback for edge misses
```

**Origin Servers:**
```
- Central data centers
- Complete video catalog
- Serve only on regional miss (5% of traffic)
```

**Cache Strategy:**
```
- Popular videos: Pushed to all edges proactively
- New uploads: Cached on first request
- Cold content: Served from origin
- Cache TTL: Based on popularity
  Hot: 7 days
  Warm: 24 hours
  Cold: 1 hour
```

## Video Recommendations

### Recommendation Algorithm

**Signals:**
```
1. User watch history
2. Video metadata (title, tags, category)
3. User interactions (likes, comments, shares)
4. Similar users' behavior (collaborative filtering)
5. Video popularity (trending)
6. Freshness (recent uploads)
```

**Approach:**

**1. Candidate Generation:**
```
- Content-based: Similar to watched videos
- Collaborative filtering: User similarity
- Trending: Global popular videos
- Subscriptions: New videos from subscribed channels
→ Produces 1000 candidates
```

**2. Ranking:**
```
- ML model (neural network)
- Features: User profile, video features, context
- Score each candidate
- Sort by score, take top 20
```

**3. Diversification:**
```
- Avoid repetitive topics
- Mix different categories
- Include some exploration (new genres)
```

### Offline Training

```
1. Collect training data:
   - User clicks (positive labels)
   - Impressions without clicks (negative labels)
   - Watch time (regression target)

2. Feature engineering:
   - User: Age, location, watch history embedding
   - Video: Category, upload date, engagement rate
   - Context: Time of day, device type

3. Train model (daily):
   - Distributed training (TensorFlow)
   - Store model in serving layer

4. A/B test new model:
   - Compare engagement metrics
   - Gradual rollout if better
```

### Online Serving

```
1. User requests recommendations
2. Fetch user embedding (pre-computed)
3. ANN (Approximate Nearest Neighbors) search for candidates
4. Score with ML model
5. Rank and return top 20
6. Cache results (15 minutes TTL)

Latency:
- Candidate generation: 50ms
- Ranking: 100ms
- Total: <200ms
```

## Search

### Indexing (Elasticsearch)

**Document structure:**
```json
{
  "video_id": "abc123",
  "title": "How to cook pasta",
  "description": "Step by step guide...",
  "tags": ["cooking", "italian", "pasta"],
  "channel": "Chef Mario",
  "view_count": 1000000,
  "upload_date": "2024-01-15",
  "duration": 600,
  "category": "Education"
}
```

**Indexing pipeline:**
```
1. New video uploaded → Publish to Kafka
2. Indexing worker consumes event
3. Extract text fields, apply NLP:
   - Tokenization
   - Stemming ("cooking" → "cook")
   - Synonyms ("recipe" includes "cooking")
4. Index in Elasticsearch
5. Build inverted index

Update frequency:
- Real-time: Title, description changes
- Batch: View count, engagement metrics (hourly)
```

### Search Query

```
GET /api/v1/videos/search?q=pasta+recipe&sort=relevance

Elasticsearch query:
{
  "query": {
    "multi_match": {
      "query": "pasta recipe",
      "fields": ["title^3", "description", "tags^2"]
    }
  },
  "sort": [
    {"_score": "desc"},
    {"view_count": "desc"}
  ],
  "filters": {
    "upload_date": {"gte": "now-1y"},
    "duration": {"gte": 60, "lte": 3600}
  }
}

Ranking factors:
- Text relevance (BM25 score)
- Video popularity (view count, like ratio)
- Freshness (recent uploads boost)
- User personalization (watch history)
- Click-through rate (historical)

Combined score:
final_score = 
  0.4 * text_relevance +
  0.3 * popularity_score +
  0.2 * personalization_score +
  0.1 * freshness_score
```

### Autocomplete

```
- Separate index for search suggestions
- Prefix matching with fuzzy tolerance
- Boost popular queries
- Personalize based on user history
- Update in real-time (trending searches)
```

## Analytics & View Counting

### View Tracking

**Client-side:**
```
1. Video starts playing
2. Send initial view event immediately
3. Send heartbeat every 30 seconds with watch_time
4. Send final event on close/complete
```

**Server-side (Event Processing):**
```
1. Receive view events → Kafka
2. Aggregate in stream processor (Flink):
   - Count views per video (windowed)
   - Calculate average watch time
   - Detect completion rate
3. Update Cassandra (batch writes)
4. Update cache (Redis) for hot videos

View count accuracy trade-off:
- Eventual consistency (few minutes delay)
- Prevents DB overload from millions of updates/sec
```

### Fraud Detection

```
- Detect bot views (rapid playback, no user interaction)
- IP rate limiting
- Device fingerprinting
- ML model to identify anomalous patterns
```

## Scaling Considerations

### Storage
```
- S3 or equivalent (Petabyte scale)
- Multi-region replication
- Lifecycle policies:
  Infrequent access (IA) after 90 days
  Glacier for old, rarely watched videos
- Deduplication (same video uploaded multiple times)
```

### Database
```
- Cassandra for videos, comments (high write throughput)
- Shard by video_id
- Replicate across data centers
- Read replicas for heavy read endpoints
```

### Processing
```
- Auto-scaling worker pools
- Spot instances for transcoding (cost optimization)
- Priority queue (popular channels processed first)
- Parallel transcoding (distribute resolutions)
```

### CDN
```
- Multi-CDN strategy (CloudFront, Akamai)
- Geo-routing for lowest latency
- Cache warming for trending videos
- Bandwidth optimization (video compression)
```

### Live Streaming
```
- Separate infrastructure
- RTMP ingest servers
- Real-time transcoding
- Ultra-low latency (< 2 seconds)
- WebRTC for interaction
```

## Trade-offs

- **Storage cost vs quality:** Multiple resolutions expensive
- **Transcoding speed vs cost:** Faster encoding = more $$$
- **CDN caching vs freshness:** Stale content possible
- **View count accuracy vs performance:** Eventual consistency
- **Recommendation complexity vs latency:** Better recs = slower

## Key Insights

1. **Adaptive bitrate streaming** (HLS/DASH) provides smooth viewing across varying network conditions
2. **Multi-tier CDN** dramatically reduces origin load and improves global latency
3. **Offline video processing** enables high-quality transcoding without affecting upload experience
4. **ML-based recommendations** drive engagement but require significant infrastructure
5. **Elasticsearch** provides fast, relevant search results at scale
6. **Event streaming** (Kafka) enables real-time analytics without overwhelming databases
7. **Content-based deduplication** saves storage costs
8. **Spot instances** reduce transcoding costs by 70-90%
