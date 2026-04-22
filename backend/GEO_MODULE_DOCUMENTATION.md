# GEO Module Implementation Guide

## Overview

The GEO Module provides comprehensive local SEO tracking capabilities for AdTicks, including:

- **Location Management**: Create and manage multiple business locations
- **Local Rankings**: Track Google Maps and local search positions
- **Review Management**: Monitor and aggregate customer reviews
- **Citation Tracking**: Audit business citations and NAP (Name, Address, Phone) consistency

## Database Models

### Location
Represents a physical business location for local SEO tracking.

**Fields:**
- `id` (UUID): Primary key
- `project_id` (UUID): Parent project reference
- `name` (str): Location name
- `address` (str): Street address
- `city` (str): City
- `state` (str): State/Province
- `country` (str): Country
- `postal_code` (str): Optional postal code
- `phone` (str): Optional phone number
- `latitude` (float): Optional latitude coordinate
- `longitude` (float): Optional longitude coordinate
- `google_business_id` (str): Optional Google Business Profile ID
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

**Relationships:**
- `project`: Parent project (one-to-many)
- `local_ranks`: Local rankings (one-to-many)
- `reviews`: Customer reviews (one-to-many)
- `review_summary`: Aggregated review stats (one-to-one)
- `citations`: Business citations (one-to-many)

### LocalRank
Tracks Google Maps and local search rankings for a location and keyword.

**Fields:**
- `id` (UUID): Primary key
- `location_id` (UUID): Parent location reference
- `keyword_id` (UUID): Optional keyword reference
- `keyword` (str): Keyword term
- `google_maps_rank` (int): Google Maps position
- `local_pack_position` (int): Local pack position (top 3)
- `local_search_rank` (int): Local search position
- `device` (str): Device type (desktop/mobile)
- `timestamp` (datetime): Rank check timestamp
- `created_at` (datetime): Creation timestamp

### Review
Stores individual customer reviews from various sources.

**Fields:**
- `id` (UUID): Primary key
- `location_id` (UUID): Parent location reference
- `source` (str): Review source (google, yelp, facebook, etc.)
- `external_id` (str): External review ID
- `rating` (float): Rating (1-5)
- `text` (str): Review text
- `author` (str): Author name
- `sentiment_score` (float): Sentiment analysis score (-1 to 1)
- `sentiment_label` (str): Sentiment (positive, negative, neutral)
- `review_date` (datetime): When the review was written
- `verified` (bool): Is verified purchase
- `created_at` (datetime): When we imported the review
- `updated_at` (datetime): Last update

### ReviewSummary
Aggregated review statistics for a location.

**Fields:**
- `id` (UUID): Primary key
- `location_id` (UUID): Parent location reference (unique)
- `total_reviews` (int): Total review count
- `average_rating` (float): Average star rating
- `five_star`, `four_star`, `three_star`, `two_star`, `one_star` (int): Distribution counts
- `positive_count`, `negative_count`, `neutral_count` (int): Sentiment distribution
- `google_reviews`, `yelp_reviews`, `facebook_reviews` (int): By-source counts
- `last_updated` (datetime): Last aggregation time
- `created_at` (datetime): Creation timestamp

### Citation
Tracks business citations in online directories.

**Fields:**
- `id` (UUID): Primary key
- `location_id` (UUID): Parent location reference
- `source_name` (str): Directory name
- `url` (str): Citation URL
- `consistency_score` (float): NAP match score (0-1)
- `name_match` (bool): Business name matches
- `address_match` (bool): Address matches
- `phone_match` (bool): Phone matches
- `business_name` (str): Name in citation
- `citation_address` (str): Address in citation
- `citation_phone` (str): Phone in citation
- `last_verified` (datetime): Last verification time
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update

## API Endpoints

### Locations

#### Create Location
```
POST /api/geo/projects/{project_id}/locations
Authorization: Bearer {token}

Request:
{
  "name": "New York Branch",
  "address": "123 Main Street",
  "city": "New York",
  "state": "NY",
  "country": "USA",
  "postal_code": "10001",
  "phone": "+1-212-555-0123",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "google_business_id": "ChIJ..."
}

Response: 201 Created
{
  "id": "uuid",
  "project_id": "uuid",
  "name": "New York Branch",
  ...
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### List Locations
```
GET /api/geo/projects/{project_id}/locations?skip=0&limit=50
Authorization: Bearer {token}

Response: 200 OK
{
  "data": [...],
  "total": 100,
  "skip": 0,
  "limit": 50,
  "has_more": true
}
```

#### Get Location
```
GET /api/geo/locations/{location_id}
Authorization: Bearer {token}

Response: 200 OK
{...location object...}
```

#### Update Location
```
PUT /api/geo/locations/{location_id}
Authorization: Bearer {token}

Request: {partial update fields}

Response: 200 OK
{...updated location...}
```

#### Delete Location
```
DELETE /api/geo/locations/{location_id}
Authorization: Bearer {token}

Response: 204 No Content
```

### Local Rankings

#### Get Local Rankings
```
GET /api/geo/locations/{location_id}/ranks?skip=0&limit=50&keyword=&device=
Authorization: Bearer {token}

Query Parameters:
- skip: Number of items to skip (default: 0)
- limit: Number of items to return (default: 50, max: 500)
- keyword: Optional keyword filter
- device: Optional device filter (desktop/mobile)

Response: 200 OK
{
  "data": [
    {
      "id": "uuid",
      "keyword": "pizza near me",
      "google_maps_rank": 2,
      "local_pack_position": 1,
      "local_search_rank": 3,
      "device": "desktop",
      ...
    }
  ],
  "total": 125,
  ...
}
```

### Reviews

#### Create Review
```
POST /api/geo/locations/{location_id}/reviews
Authorization: Bearer {token}

Request:
{
  "source": "google",
  "rating": 4.5,
  "author": "John Doe",
  "text": "Great service!",
  "sentiment_score": 0.85,
  "sentiment_label": "positive",
  "verified": true,
  "external_id": "review-123",
  "review_date": "2024-01-01T00:00:00Z"
}

Response: 201 Created
{...review object...}
```

#### Get Reviews
```
GET /api/geo/locations/{location_id}/reviews?skip=0&limit=50&source=&min_rating=&max_rating=
Authorization: Bearer {token}

Query Parameters:
- skip: Number of items to skip
- limit: Number of items to return
- source: Optional source filter (google, yelp, etc.)
- min_rating: Optional minimum rating (1-5)
- max_rating: Optional maximum rating (1-5)

Response: 200 OK
{
  "data": [...],
  "total": 150,
  ...
}
```

#### Get Review Summary
```
GET /api/geo/locations/{location_id}/reviews/summary
Authorization: Bearer {token}

Response: 200 OK
{
  "id": "uuid",
  "location_id": "uuid",
  "total_reviews": 150,
  "average_rating": 4.5,
  "five_star": 100,
  "four_star": 35,
  "three_star": 10,
  "two_star": 3,
  "one_star": 2,
  "positive_count": 145,
  "negative_count": 3,
  "neutral_count": 2,
  "google_reviews": 80,
  "yelp_reviews": 50,
  "facebook_reviews": 20,
  "last_updated": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Citations

#### Create Citation
```
POST /api/geo/locations/{location_id}/citations
Authorization: Bearer {token}

Request:
{
  "source_name": "Google Business",
  "url": "https://business.google.com/123",
  "business_name": "New York Branch",
  "citation_address": "123 Main Street",
  "citation_phone": "+1-212-555-0123"
}

Response: 201 Created
{
  "id": "uuid",
  "consistency_score": 1.0,
  "name_match": true,
  "address_match": true,
  "phone_match": true,
  ...
}
```

#### Get Citations
```
GET /api/geo/locations/{location_id}/citations?skip=0&limit=50&source=
Authorization: Bearer {token}

Query Parameters:
- skip: Number of items to skip
- limit: Number of items to return
- source: Optional source filter

Response: 200 OK
{
  "data": [...],
  "total": 50,
  ...
}
```

#### NAP Consistency Check
```
GET /api/geo/locations/{location_id}/citations/nap-check
Authorization: Bearer {token}

Response: 200 OK
{
  "location_id": "uuid",
  "total_citations": 50,
  "consistent_citations": 45,
  "consistency_percentage": 90.0,
  "issues": [
    {
      "citation_id": "uuid",
      "source": "Yelp",
      "url": "https://yelp.com/...",
      "issues": [
        "Phone mismatch: Expected '+1-212-555-0123', found '212-555-9999'"
      ]
    }
  ]
}
```

## Frontend Components

### LocationList
Displays and manages locations with search and filter capabilities.

**Props:**
```typescript
interface LocationListProps {
  locations?: Location[];
  loading?: boolean;
  onAdd?: () => void;
  onEdit?: (location: Location) => void;
  onDelete?: (location: Location) => void;
  onSelect?: (location: Location) => void;
}
```

**Features:**
- Search by name, city, or address
- Expand/collapse for quick edit/delete
- Add new locations
- Responsive design

### LocalRankCards
Displays local ranking data in card format.

**Props:**
```typescript
interface LocalRankCardsProps {
  ranks?: LocalRank[];
  loading?: boolean;
  maxRows?: number;
}
```

**Features:**
- Shows Google Maps, Local Pack, and Local Search ranks
- Device indicator (desktop/mobile)
- Color-coded ranking positions
- Pagination with "more" indicator

### ReviewDashboard
Comprehensive review analytics dashboard.

**Props:**
```typescript
interface ReviewDashboardProps {
  summary?: ReviewSummary;
  loading?: boolean;
}
```

**Features:**
- Average rating display
- Star distribution chart
- Sentiment breakdown (positive/negative/neutral)
- Reviews by source (Google, Yelp, Facebook)
- Visual progress bars

### CitationAudit
Citation and NAP consistency tracking component.

**Props:**
```typescript
interface CitationAuditProps {
  citations?: Citation[];
  napCheck?: NAPCheckResult;
  loading?: boolean;
  maxRows?: number;
}
```

**Features:**
- NAP consistency summary
- Individual citation cards
- Name/Address/Phone match indicators
- Consistency score badges
- External links to citations
- Issue details for mismatches

## Testing

### Backend Tests (21 tests)

```bash
cd backend
python -m pytest tests/test_geo.py -v
```

**Coverage:**
- Location CRUD operations
- Authorization checks
- Pagination
- Local rankings retrieval and filtering
- Review creation and retrieval
- Review filtering by rating
- Review summaries
- Citation creation
- Citation retrieval
- NAP consistency checks
- Error handling
- Invalid data validation

### Frontend Tests (23 tests)

```bash
cd frontend
npm test __tests__/components/geo/geo.test.tsx
```

**Coverage:**
- LocationList: render, search, add, edit, delete
- LocalRankCards: render, filtering, pagination
- ReviewDashboard: display summary, ratings, sentiment, sources
- CitationAudit: NAP checks, consistency display, issues

## Pagination Format

All list endpoints return paginated responses:

```typescript
{
  data: T[],           // Array of items
  total: number,       // Total count in database
  skip: number,        // Items skipped
  limit: number,       // Items returned
  has_more: boolean    // Whether more items exist
}
```

## Error Handling

- **401**: Unauthorized - Missing or invalid authentication
- **403**: Forbidden - User does not own the project/location
- **404**: Not Found - Resource not found
- **422**: Unprocessable Entity - Invalid request data
- **500**: Internal Server Error - Unexpected error

## Caching

The module uses Redis caching for performance:

- Location lists: `cache:locations:{project_id}:*`
- Local rankings: `cache:local_ranks:{location_id}:*`
- Reviews: `cache:reviews:{location_id}:*`
- Citations: `cache:citations:{location_id}:*`

Caches are invalidated on create/update/delete operations.

## Features & Capabilities

✅ **Fully Implemented:**
- Location management (CRUD)
- Local rank tracking with device support
- Review aggregation and sentiment analysis
- Citation auditing with NAP consistency
- Comprehensive API endpoints
- Request ID propagation
- Full authorization checks
- Pagination on all list endpoints
- Redis caching
- 21+ backend tests
- 23+ frontend tests
- Type-safe TypeScript code
- Error handling
- No breaking changes

## Future Enhancements

- Batch citation verification
- Automated review sentiment analysis
- Competitive analysis for rankings
- Historical trend charts
- Review response tracking
- Bulk location import/export
- Real-time ranking notifications
- Review spike detection

## Integration Points

The GEO module integrates with:

- **Projects**: All locations belong to a project
- **Keywords**: LocalRank references keywords
- **Security**: Full auth and authorization
- **Caching**: Redis integration
- **Logging**: Structured logging with request IDs
- **Database**: SQLAlchemy ORM with PostgreSQL

## Quick Start

### Creating a location:
```python
POST /api/geo/projects/{project_id}/locations
{
  "name": "Main Office",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "country": "USA"
}
```

### Getting local rankings:
```python
GET /api/geo/locations/{location_id}/ranks
```

### Checking NAP consistency:
```python
GET /api/geo/locations/{location_id}/citations/nap-check
```

## Module Files

**Backend:**
- `app/models/geo.py` - Database models
- `app/schemas/geo.py` - Pydantic schemas
- `app/api/geo.py` - API endpoints
- `tests/test_geo.py` - Backend tests

**Frontend:**
- `components/geo/LocationList.tsx` - Location management
- `components/geo/LocalRankCards.tsx` - Local rankings display
- `components/geo/ReviewDashboard.tsx` - Review analytics
- `components/geo/CitationAudit.tsx` - Citation tracking
- `__tests__/components/geo/geo.test.tsx` - Frontend tests
- `lib/types.ts` - TypeScript types

## Compliance & Standards

✅ **Requirements Met:**
- Pagination format: `{data, total, skip, limit, has_more}`
- Redis caching with invalidation
- Request ID propagation
- Full authorization checks
- Type-safe code
- No breaking changes
- All tests passing
