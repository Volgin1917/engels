# API Documentation

This document describes the REST API for the Entity Extraction System. It covers endpoints, request/response formats, authentication, and error handling.

## Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://api.yourdomain.com/api/v1`

## Authentication

The API uses **Bearer Token** authentication (JWT). Include the token in the `Authorization` header:

```http
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

Send a POST request to `/auth/login` with credentials:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Endpoints

### 1. Sources (Источники)

Manage source documents for entity extraction.

#### `POST /sources`
Upload a new source document.

**Request:**
```json
{
  "title": "Annual Report 2024",
  "content": "Full text content here...",
  "source_type": "TEXT",
  "metadata": {
    "author": "John Doe",
    "language": "en"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Annual Report 2024",
  "status": "PENDING",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### `GET /sources`
List all sources with pagination.

**Query Parameters:**
- `page` (int, default: 1): Page number
- `size` (int, default: 20): Items per page
- `status` (string, optional): Filter by status (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Annual Report 2024",
      "status": "COMPLETED",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### `GET /sources/{id}`
Get details of a specific source.

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Annual Report 2024",
  "content": "Full text...",
  "source_type": "TEXT",
  "status": "COMPLETED",
  "metadata": {},
  "created_at": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T10:31:00Z"
}
```

#### `DELETE /sources/{id}`
Delete a source and its associated entities (cascade).

**Response (204 No Content)**

---

### 2. Entities (Сущности)

Retrieve and manage extracted entities.

#### `GET /entities`
List entities with filtering.

**Query Parameters:**
- `entity_type` (string, optional): Filter by type (`PERSON`, `ORGANIZATION`, etc.)
- `source_id` (uuid, optional): Filter by source
- `needs_review` (boolean, optional): Filter for human review queue
- `search` (string, optional): Full-text search on name

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Acme Corp",
      "entity_type": "ORGANIZATION",
      "confidence_score": 0.95,
      "needs_review": false,
      "attributes": {
        "industry": "Technology"
      },
      "source_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "total": 1
}
```

#### `GET /entities/{id}`
Get detailed info about an entity including relations.

**Response (200 OK):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Acme Corp",
  "entity_type": "ORGANIZATION",
  "confidence_score": 0.95,
  "needs_review": false,
  "attributes": {},
  "relations": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "target_entity_id": "880e8400-e29b-41d4-a716-446655440003",
      "target_entity_name": "John Doe",
      "relation_type": "EMPLOYEES",
      "confidence_score": 0.88
    }
  ]
}
```

#### `PUT /entities/{id}`
Update an entity (used in Human-in-the-loop correction).

**Request:**
```json
{
  "name": "Acme Corporation",
  "attributes": {
    "industry": "Software",
    "founded": "2010"
  },
  "needs_review": false
}
```

**Response (200 OK):** Updated entity object.

---

### 3. Relations (Связи)

Manage relationships between entities.

#### `GET /relations`
List relations.

**Query Parameters:**
- `source_entity_id` (uuid, optional)
- `target_entity_id` (uuid, optional)
- `relation_type` (string, optional)

#### `POST /relations`
Create a new relation manually.

**Request:**
```json
{
  "source_entity_id": "660e8400-e29b-41d4-a716-446655440001",
  "target_entity_id": "880e8400-e29b-41d4-a716-446655440003",
  "relation_type": "OWNED_BY",
  "confidence_score": 1.0
}
```

---

### 4. Review (Проверка)

Human-in-the-loop endpoints for experts.

#### `GET /review/queue`
Get list of entities needing review.

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "name": "Unknown Entity",
      "entity_type": "PERSON",
      "confidence_score": 0.45,
      "source_title": "Scanned Document #12"
    }
  ],
  "total": 5
}
```

#### `POST /review/{id}/approve`
Approve an entity as correct.

**Response (200 OK):** `{ "status": "approved" }`

#### `POST /review/{id}/reject`
Reject an entity (marks for deletion or re-extraction).

**Request:**
```json
{
  "comment": "Incorrect extraction, not a person name."
}
```

---

### 5. Audit (Аудит)

View change history.

#### `GET /audit/logs`
Get audit logs.

**Query Parameters:**
- `entity_id` (uuid, optional)
- `user_id` (uuid, optional)
- `action` (string, optional)
- `from_date` (datetime, optional)
- `to_date` (datetime, optional)

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "log-uuid",
      "entity_id": "660e8400...",
      "user_email": "expert@example.com",
      "action": "UPDATE",
      "old_value": { "name": "Acme" },
      "new_value": { "name": "Acme Corp" },
      "created_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

---

## Error Handling

All errors return a standard JSON format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Field 'email' is required",
    "details": [
      { "field": "email", "issue": "missing" }
    ]
  }
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
| :--- | :--- | :--- |
| `200` | OK | Request succeeded |
| `201` | Created | Resource created successfully |
| `204` | No Content | Success, no body returned |
| `400` | Bad Request | Invalid input or validation error |
| `401` | Unauthorized | Missing or invalid token |
| `403` | Forbidden | Valid token but insufficient permissions |
| `404` | Not Found | Resource does not exist |
| `409` | Conflict | Duplicate resource or state conflict |
| `500` | Internal Server Error | Unexpected server error |

## Rate Limiting

- **Default**: 100 requests per minute per IP.
- **Authenticated Users**: 500 requests per minute.
- **Headers**:
  - `X-RateLimit-Limit`: Max requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Versioning

API version is included in the URL path (`/api/v1/`). Breaking changes will result in a new major version (`/api/v2/`).
