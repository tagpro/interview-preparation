# Design WhatsApp

## Functional Requirements
- One-on-one messaging
- Group chats (up to 256 members)
- Online/offline status
- Message delivery receipts (sent, delivered, read)
- Media sharing (images, videos)
- End-to-end encryption

## Non-Functional Requirements
- 2B users, 500M daily active
- Average user sends 40 messages/day
- Support offline message delivery
- Low latency (<100ms)
- 99.99% uptime
- Messages stored for 30 days

## Capacity Estimation
- Messages per day: 500M * 40 = 20B messages
- Messages per second: 20B / 86400 = 231K messages/sec
- Storage: 231K * 100 bytes = 23 MB/sec = 2TB/day
- Media: 10% have media (avg 100KB) = 200TB/day
- WebSocket connections: 500M concurrent connections

## API Design

```
WebSocket /ws/connect
  - Maintains persistent connection
  - Sends/receives messages in real-time

POST /api/v1/messages
  body: {from_user, to_user, content, encryption_key, timestamp}
  
GET /api/v1/messages/{user_id}
  params: {conversation_id, before_timestamp, limit}
  
PUT /api/v1/messages/{message_id}/status
  body: {status: delivered|read}
```

## High-Level Architecture

```
Users → Load Balancer → WebSocket Servers (Connection Pool)
                              ↓
                   ┌──────────┼──────────┐
                   ↓          ↓          ↓
            Message Service  Session Service  Media Service
                   ↓          ↓          ↓
            MongoDB/Cassandra Redis    S3/CDN
            (Messages)     (Sessions) (Media)
                   ↓
              Kafka (Message Queue)
```

## Database Schema

### Messages (Cassandra)
```
message_id (UUID), conversation_id, sender_id, 
content (encrypted), timestamp, status, media_url
Partition key: conversation_id
Sort key: timestamp (DESC)
```

### User Sessions (Redis)
```
Key: user:{user_id}:session
Value: {connection_id, websocket_server, last_seen}
TTL: 5 minutes (refresh on activity)
```

### Conversations (MongoDB)
```
conversation_id, participants[], type (one-on-one|group),
last_message, last_updated, unread_count_per_user
```

### Message Status (Redis)
```
Key: msg:{message_id}:status
Value: {sent_at, delivered_at, read_at}
```

## Detailed Component Design

### Message Sending Flow

1. **Client sends message via WebSocket**
   - Client encrypts message with recipient's public key
   - Sends to WebSocket server

2. **WebSocket server receives message**
   - Validates authentication
   - Assigns message_id (UUID with timestamp)
   - Sends ACK to sender immediately

3. **Message persistence**
   - Write to Cassandra (async)
   - Publish to Kafka for delivery

4. **Recipient online:**
   - Check Redis for recipient's session
   - If online, push via WebSocket directly
   - Update status to "delivered"
   - Recipient sends read receipt when viewed

5. **Recipient offline:**
   - Store in inbox queue (Redis list)
   - Send push notification via Firebase/APNs
   - Deliver when user reconnects

## Connection Management

### WebSocket Server Pool
```
- Each server handles ~65K connections
- Use connection pooling per server
- Heartbeat every 30 seconds to detect disconnects
- Reconnection with exponential backoff
```

### Session Registry (Redis)
```
user:123:session → {
  connection_id: "conn_abc",
  server: "ws-server-5",
  device_id: "device_xyz",
  last_seen: timestamp
}
```

### Message Routing
```
1. Lookup recipient's session in Redis
2. If same server: direct delivery
3. If different server: internal RPC to that server
4. If offline: queue in Redis list
```

## Group Chat

### Fan-out approach
```
1. Message received for group
2. Fetch all group members (cached)
3. Create individual message for each member
4. Process as N one-on-one messages
5. Use Kafka for parallel delivery
```

### Optimization for large groups
```
- Don't store N copies, store once with delivery tracking
- Each member has pointer to message
- Delivery status tracked separately per member
```

## Message Status Tracking

### Delivery Receipts
```
1. Message sent: Status = "sent"
2. Delivered to recipient device: Status = "delivered"
3. User opens chat and views: Status = "read"

For groups:
- Show "delivered to all" only when all received
- Show read count (Read by 5/10)
```

## Media Handling

### Upload Flow
```
1. Client requests upload URL (signed)
2. Upload directly to S3
3. Generate thumbnail (Lambda/async worker)
4. Message contains media_url (CDN link)
5. Recipients download from CDN
```

### Optimization
```
- Compress images before upload
- Progressive JPEG for fast display
- Video: Multiple quality versions
- Cache frequently accessed media
```

## Scaling Considerations

### WebSocket Servers
- Horizontal scaling with load balancer
- Sticky sessions not required
- Use Redis pub/sub for cross-server messaging
- Graceful shutdown: notify clients to reconnect

### Message Storage
- Cassandra for write throughput
- Partition by conversation_id
- Archive old messages to cold storage (S3)
- TTL-based deletion after 30 days

### Session Management
- Redis cluster (sharded by user_id)
- Replicate for high availability
- Backup session data periodically

### Delivery Guarantees
- At-least-once delivery via Kafka
- Client-side deduplication using message_id
- Retry logic with exponential backoff
- Dead letter queue for failed deliveries

## Encryption

### End-to-End
```
- Signal Protocol or similar
- Each device has key pair
- Keys never sent to server
- Server only routes encrypted messages
- Forward secrecy with ratcheting
```

## Online/Offline Status

### Presence System
```
- User connects: Set status "online" in Redis
- Heartbeat every 30s updates last_seen
- On disconnect: Status becomes "last seen at X"
- Publish presence changes to interested users via pub/sub
```

## Trade-offs

- **WebSocket vs HTTP polling:** WebSocket for real-time, higher server load
- **Message storage duration:** Balance storage cost vs user experience
- **Read receipts:** Privacy vs feature richness
- **Group size limit:** Performance vs functionality

## Key Insights

1. **WebSocket connections** enable true real-time messaging
2. **Redis for session management** provides fast lookups for routing
3. **Kafka for message delivery** ensures reliability and scalability
4. **Cassandra for message storage** handles massive write throughput
5. **End-to-end encryption** keeps server from seeing message content
6. **Offline message queuing** ensures no messages are lost
