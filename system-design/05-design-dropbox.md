# Design Dropbox

## Functional Requirements
- Upload/download files
- Sync across multiple devices
- File versioning
- Share files with others
- Offline access
- Conflict resolution

## Non-Functional Requirements
- 500M users, 100M daily active
- Average 200 files per user, 100KB each
- 10GB storage per user
- 1M concurrent uploads
- 99.99% durability
- Cross-platform support

## Capacity Estimation
- Total storage: 500M * 10GB = 5 Exabytes
- Daily uploads: 100M * 5 files = 500M files
- Upload bandwidth: 500M * 100KB / 86400 = 579 GB/sec
- Metadata: 500M users * 200 files * 1KB = 100TB

## API Design

```
POST /api/v1/files/upload
  multipart: {file, metadata}
  response: {file_id, version, checksum}
  
GET /api/v1/files/{file_id}/download
  params: {version?}
  
GET /api/v1/files/sync
  params: {device_id, last_sync_timestamp}
  response: {files_to_upload[], files_to_download[]}
  
POST /api/v1/files/{file_id}/share
  body: {user_ids[], permissions}
```

## High-Level Architecture

```
Clients → Load Balancer → API Servers
                              ↓
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
    Upload Service    Metadata Service    Sync Service
          ↓                   ↓                   ↓
   Block Storage         PostgreSQL         Message Queue
   (S3/MinIO)         (File metadata)         (Kafka)
          ↓                                       ↓
    Deduplication                          Notification
      Service                               Service
```

## Database Schema

### Users
```
user_id, email, storage_used, storage_limit, 
created_at
```

### Files
```
file_id (PK), user_id, filename, file_path, 
size, mime_type, created_at, modified_at, 
is_deleted
Index: (user_id, file_path)
```

### File Versions
```
version_id (PK), file_id, version_number, 
size, checksum (SHA-256), created_at, 
block_ids[] (JSON)
```

### Blocks (for deduplication)
```
block_id (PK - SHA-256 hash), size, 
storage_path, ref_count
```

### Devices
```
device_id (PK), user_id, device_name, 
last_sync_at, sync_cursor
```

### File Shares
```
share_id (PK), file_id, shared_by, 
shared_with, permission (read/write), 
created_at
```

## Detailed Component Design

### File Upload (Chunking & Deduplication)

**Client-side:**
```
1. Split file into 4MB chunks
2. Calculate SHA-256 for each chunk
3. Check with server which chunks exist (dedup check)
4. Upload only new chunks
5. Send metadata with chunk references
```

**Server-side:**
```
1. Receive chunk hash manifest
2. Query Blocks table for existing chunks
3. Return list of chunks to upload
4. Receive uploaded chunks
5. Store in S3 with hash as key
6. Update ref_count for existing blocks
7. Create file metadata entry
8. Link file to chunks
```

**Chunking Algorithm:**
```python
def chunk_file(file_path, chunk_size=4MB):
    chunks = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_hash = sha256(chunk).hexdigest()
            chunks.append({
                'hash': chunk_hash,
                'size': len(chunk),
                'data': chunk
            })
    return chunks
```

**Deduplication:**
```
- Store each unique chunk once
- Multiple files reference same chunks
- Saves storage: 
  If 1000 users upload same file,
  store once, 1000 references

Example:
File A: [chunk1, chunk2, chunk3]
File B: [chunk2, chunk4, chunk5]
Storage: chunk1, chunk2 (shared), chunk3, chunk4, chunk5
```

## Synchronization

### Sync Protocol
```
1. Client starts sync
2. Send last_sync_timestamp and device_id
3. Server queries changes since timestamp:
   - Files modified/created by other devices
   - Files deleted by other devices
4. Server returns delta:
   {
     to_upload: [files newer on server],
     to_download: [files newer on client],
     conflicts: [modified on both]
   }
5. Client reconciles and syncs
```

### Change Detection
```
- File system watcher monitors local changes
- On change: Calculate hash, compare with last known
- If different: Mark for upload
- Batch changes (debounce 5 seconds)
- Upload in background
```

### Metadata-first approach
```
1. Sync metadata first (fast)
2. Download file content on demand (lazy)
3. Pre-fetch frequently accessed files
4. Optimize: Sync overnight when idle
```

## Conflict Resolution

### Scenarios
```
1. Same file modified on 2 devices while offline
2. File deleted on one, modified on another
3. File renamed on multiple devices
```

### Resolution Strategy

**Timestamp-based (Last Writer Wins):**
```
- Keep version with latest timestamp
- Create conflict copy for older version
- Rename: file.txt → file (conflict-device).txt
```

**Version Vector:**
```
- Each device maintains version counter
- Detect concurrent modifications
- Present conflict to user for manual resolution
```

**Operational Transform (advanced):**
```
- For text files: Merge changes
- Similar to Google Docs
- Complex but better UX
```

## Versioning

```
Keep last N versions (configurable per plan):
- Free users: 30 days history
- Paid users: Unlimited history

Version pruning:
- Keep all versions < 30 days
- Keep monthly snapshots older than 30 days
- User can restore any version
- Deleted files retained for 30 days

Storage:
- Delta encoding for similar versions
- Store only differences between versions
- Backward deltas (store latest in full)
```

## File Download

```
1. Client requests file_id
2. Server returns metadata + block_ids[]
3. Client checks local cache for blocks
4. Download missing blocks in parallel
5. Reassemble file from blocks
6. Verify checksum
7. Update local metadata

Optimization:
- Download blocks in priority order
- Stream reconstruction (partial file available)
- Resume broken downloads (using block boundaries)
```

## Sharing

### Share by Link
```
1. Generate unique share_token
2. Store: share_token → file_id mapping
3. Set permissions and expiration
4. Anyone with link can access
5. Track access for analytics
```

### Share with Users
```
1. Create share record in database
2. Recipient sees file in "Shared with me"
3. File doesn't count toward recipient's quota
4. Permissions: view-only or edit
5. Notification sent to recipient
```

### Shared folders
```
- Entire folder hierarchy shared
- Recursive permission checking
- Changes sync to all members
- Member can be removed, access revoked
```

## Scaling Considerations

### Storage
```
- S3 or distributed storage (Ceph, MinIO)
- Replication factor: 3x for durability
- Multi-region for disaster recovery
- Hot/Cold storage tiers:
  Hot: Recently accessed (SSD)
  Cold: Archived (cheaper, slower)
- Glacier for long-term backups
```

### Metadata Database
```
- PostgreSQL with read replicas
- Shard by user_id
- Cache heavily accessed metadata in Redis
- Full-text search: Elasticsearch for file search
```

### Upload/Download
```
- Direct upload to S3 (presigned URLs)
- CDN for downloads (CloudFront)
- Multiple upload servers globally
- P2P sync between user's own devices (LAN Sync)
```

### Sync Service
```
- Message queue (Kafka) for sync events
- Each device subscribes to user's stream
- Push notifications for real-time updates
- WebSocket for connected clients
- Poll for disconnected clients (exponential backoff)
```

## Performance Optimizations

### Client-side
```
- Predictive sync (frequently used files)
- Selective sync (sync only specific folders)
- Bandwidth throttling (user configurable)
- Delta sync (binary diff for changed files)
```

### Server-side
```
- Block cache (Redis) for popular blocks
- Metadata cache for active files
- Compression for text files
- Async processing (thumbnail generation, virus scan)
```

## Security

```
- End-to-end encryption (optional)
- TLS for data in transit
- Encryption at rest (S3 server-side encryption)
- Zero-knowledge option (user holds keys)
- Access logs and audit trails
- Virus scanning on upload
```

## Trade-offs

- **Chunking:** Deduplication vs complexity
- **Sync frequency:** Battery/bandwidth vs freshness
- **Version retention:** Storage cost vs recovery
- **Conflict resolution:** Automatic vs user control
- **Centralized vs P2P:** Simplicity vs efficiency

## Key Insights

1. **Chunking and deduplication** dramatically reduces storage requirements
2. **Hash-based block identification** enables efficient deduplication
3. **Metadata-first sync** provides fast synchronization
4. **Multiple versioning strategies** balance storage cost with recovery needs
5. **Change detection** enables efficient incremental syncing
6. **Conflict resolution** requires balancing automation with user control
