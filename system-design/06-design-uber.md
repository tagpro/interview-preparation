# Design Uber

## Functional Requirements
- Riders request rides
- Match riders with nearby drivers
- Real-time location tracking
- ETA calculation
- Dynamic pricing (surge)
- Payment processing
- Rating system

## Non-Functional Requirements
- 500K drivers, 5M riders globally
- 1M trips per day
- Location updates every 4 seconds
- Match riders within 30 seconds
- Low latency (< 500ms)
- High availability

## Capacity Estimation
- Active drivers at once: 500K * 10% = 50K drivers
- Location updates: 50K * 60 * 60 / 4 = 45M updates/hour = 12K updates/sec
- Ride requests: 1M/day = 12 requests/sec (peak 120 req/sec)
- Storage: 1M trips * 10KB = 10GB/day = 3.6TB/year

## API Design

```
POST /api/v1/rides/request
  body: {rider_id, pickup_location, dropoff_location, ride_type}
  response: {ride_id, estimated_price, available_drivers}
  
POST /api/v1/drivers/location
  body: {driver_id, latitude, longitude, timestamp}
  
GET /api/v1/rides/{ride_id}/status
  response: {status, driver_location, ETA}
  
POST /api/v1/rides/{ride_id}/complete
  body: {final_price, distance, duration}
```

## High-Level Architecture

```
Riders/Drivers → Load Balancer → API Servers
                                      ↓
              ┌───────────────────────┼───────────────────────┐
              ↓                       ↓                       ↓
    Location Service        Matching Service          Trip Service
              ↓                       ↓                       ↓
      Redis/Geospatial           Graph DB              PostgreSQL
      (Driver locations)      (Road network)            (Trips)
              ↓                       ↓
        QuadTree Index         Pricing Service
                                     ↓
                              Redis (Surge data)
```

## Database Schema

### Users
```
user_id (PK), name, phone, email, type (rider/driver),
rating, payment_methods, created_at
```

### Drivers
```
driver_id (PK), user_id, vehicle_info, license, 
status (available/busy/offline), current_location (lat, lon),
last_updated
```

### Trips
```
trip_id (PK), rider_id, driver_id, pickup_location,
dropoff_location, status, request_time, start_time,
end_time, price, distance, route[]
Index: (rider_id, request_time), (driver_id, request_time)
```

### Locations (Time-series DB - InfluxDB)
```
driver_id, timestamp, latitude, longitude, speed, heading
```

## Geospatial Indexing

### QuadTree Structure

```
- Divide world map into recursive quadrants
- Each leaf node: Small geographic area (e.g., 1km²)
- Store driver_ids in leaf nodes
- Update as drivers move

Example:
         [World]
        /   |   \   \
    [NW] [NE] [SW] [SE]
     /\    /\    /\    /\
   ... Further subdivision ...
   
Leaf node: Grid cell containing [driver_1, driver_5, driver_19]
```

**Operations:**
```
Insert:
1. Calculate lat/lon quadrant path
2. Traverse to leaf node
3. Add driver_id to node

Query (find nearby drivers):
1. Find quadrant for rider location
2. Get drivers in same quadrant
3. If insufficient, expand to adjacent quadrants
4. Return sorted by distance

Update:
1. Remove from old quadrant
2. Add to new quadrant
3. Happens every 4 seconds per driver
```

### Alternative: Geohash

```
- Encode lat/lon to string: "dr5ru7" (6-char = ~1.2km)
- Store in Redis sorted set:
  GEOADD drivers:active lon lat driver_id
  GEORADIUS lon lat 5 km
  
- Simpler than QuadTree
- Redis native support
- Precision configurable
```

## Detailed Component Design

### Driver Location Updates

**Client (Driver app):**
```
1. GPS provides location every 4 seconds
2. Batch multiple updates if network poor
3. Send to Location Service
```

**Server:**
```
1. Validate location (sanity checks)
2. Update QuadTree/Geohash index
3. Update driver's current_location in DB (async)
4. Store in time-series DB for analytics
5. Publish to WebSocket subscribers (rider app if on trip)

Optimization:
- Only update if moved > 50 meters
- Client-side filtering reduces load
- Server-side deduplication
```

## Ride Matching Algorithm

```
1. Rider requests ride at location (lat, lon)

2. Find candidate drivers:
   - Query QuadTree for drivers within 5km radius
   - Filter by:
     * Status = available
     * Vehicle type matches request
     * Rating > 4.0
     * Not recently rejected by rider
   
3. Calculate for each candidate:
   - Distance to pickup
   - ETA to pickup (using road network, traffic)
   - Driver rating
   
4. Score drivers:
   score = 
     0.5 * (1 / distance_km) +
     0.3 * (1 / ETA_minutes) +
     0.2 * (rating / 5)
   
5. Sort by score, take top 5

6. Send ride request to best driver

7. Wait 15 seconds for acceptance
   - If accepted: Match confirmed
   - If rejected: Try next driver
   - If timeout: Try next driver
   
8. If all drivers reject, expand radius and retry

9. If still no match after 3 attempts:
   - Return "no drivers available"
   - Add to waiting queue
   - Retry when driver becomes available
```

## ETA Calculation

**Simple approach:**
```
ETA = (distance / average_speed) + traffic_factor
```

**Advanced approach:**
```
1. Use road network graph (OSM data)
2. Dijkstra's algorithm for shortest path
3. Edge weights = (distance / speed_limit) * traffic_multiplier
4. Historical data: Average speeds by time/day
5. Real-time traffic data: Update edge weights

Traffic multiplier:
- Green: 1.0x (normal)
- Yellow: 1.5x (moderate)
- Red: 3.0x (heavy)

Update frequency:
- Calculate once at request time
- Recalculate every 2 minutes during trip
- Push updates to rider app
```

## Dynamic Pricing (Surge)

### Demand calculation

```
1. Count ride requests in area (last 10 minutes)
2. Count available drivers in area
3. Calculate demand/supply ratio

Surge multiplier:
ratio = pending_requests / available_drivers

if ratio < 1.0:
    surge = 1.0 (no surge)
elif ratio < 2.0:
    surge = 1.2x
elif ratio < 3.0:
    surge = 1.5x
else:
    surge = 2.0x (cap at 2x)

Implementation:
- Divide city into cells (geohash precision 6)
- Calculate surge per cell every 5 minutes
- Store in Redis: cell_id → surge_multiplier
- Display to rider before confirmation
- Lock in price at request time

Heat map:
- Show surge areas on rider/driver app
- Incentivize drivers to move to high-demand areas
```

## Trip Flow

```
1. REQUESTED:
   - Rider submits request
   - Store in trip table
   - Start matching

2. DRIVER_ASSIGNED:
   - Driver accepts
   - Notify rider
   - Share driver location/ETA

3. DRIVER_ARRIVED:
   - Driver marks arrival
   - Rider notified
   - Start pickup timer (5 min grace)

4. IN_PROGRESS:
   - Rider confirms pickup
   - Trip starts, timer begins
   - Real-time tracking enabled
   - ETA to destination calculated

5. COMPLETED:
   - Arrive at destination
   - Calculate final price
   - Charge payment method
   - Prompt for ratings

6. CANCELLED:
   - Either party cancels
   - Apply cancellation fee if applicable
   - Free driver for new matches
```

## Real-time Tracking

```
- WebSocket connection between rider and server
- Server pushes driver location every 4 seconds
- Client interpolates between updates (smooth movement)
- Show on map with route overlay

Protocol:
1. Rider app opens WebSocket: /ws/trip/{trip_id}
2. Server subscribes to driver location stream
3. On driver update: Push to WebSocket
4. Include: lat, lon, heading, speed, ETA
```

## Payment Processing

```
1. Rider adds payment method (Stripe/Braintree)
2. At trip request: Pre-authorize estimated amount
3. At trip completion:
   - Calculate final fare
   - Capture payment
   - Transfer to driver (minus commission)
   - Generate receipt

Fare calculation:
base_fare = $2.00
per_km = $1.50
per_minute = $0.30
booking_fee = $1.00
surge_multiplier = 1.5x

total = (base_fare + distance * per_km + duration * per_minute + booking_fee) * surge_multiplier

Payout:
- Driver gets 75% of fare
- Platform gets 25% commission
- Weekly automated payouts to driver bank
```

## Scaling Considerations

### Location Service
```
- Redis cluster (sharded by geohash prefix)
- 50K drivers * 250 updates/hour = 12M updates/hour
- Use Redis GEOADD for atomic operations
- Replicate for read scaling
- Time to live: Remove stale locations (> 1 minute)
```

### Matching Service
```
- Stateless service (horizontal scaling)
- Load balance ride requests
- Cache nearby drivers (Redis, TTL 10 sec)
- Async processing with message queue
- Retry logic for failed matches
```

### Database
```
- PostgreSQL with read replicas
- Shard trips by city or date
- Archive old trips to cold storage
- PostGIS extension for geospatial queries
```

### WebSocket Connections
```
- Separate WebSocket servers
- Use Redis pub/sub for broadcasting
- Connection pooling
- Graceful reconnection
```

## Advanced Features

### Route Optimization
```
- Batch multiple rides going same direction
- UberPool: Shared rides with price discount
- Algorithm: Find riders with similar routes
- Minimize detour time
```

### Predictive Positioning
```
- ML model predicts demand hotspots
- Suggest drivers move to high-demand areas
- Reduce wait times proactively
```

### Fraud Detection
```
- Detect GPS spoofing
- Unusual route patterns
- Account for legitimate detours (traffic)
- Flag for manual review
```

## Trade-offs

- **QuadTree vs Geohash:** Custom vs Redis native
- **ETA accuracy vs computation cost:** Simple distance vs full routing
- **Surge cap:** Revenue vs user satisfaction
- **Real-time vs batch processing:** Latency vs cost
- **Matching speed vs optimal driver:** Wait time vs distance

## Key Insights

1. **Geospatial indexing** (QuadTree/Geohash) enables fast nearby driver queries
2. **WebSocket connections** provide real-time location tracking
3. **Dynamic pricing** balances supply and demand
4. **Matching algorithm** must consider multiple factors (distance, rating, ETA)
5. **Redis for location storage** provides fast reads/writes for high update frequency
6. **Time-series database** efficiently stores location history for analytics
