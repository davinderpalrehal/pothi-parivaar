# Addendum: Technical & Architecture Notes (PRD)

*This addendum preserves technical details, API payload structures, and database schema recommendations to inform the upcoming Architecture phase.*

---

## 1. Candidate Entity Models (Relational Schema)

### Books Table
* `id`: UUID / Integer (Primary Key)
* `title`: String (Required)
* `author`: String (Required)
* `publication_year`: Integer (Optional)
* `isbn`: String (Optional, 10 or 13 digits)
* `summary`: Text (Optional)
* `cover_url`: String (Optional)
* `page_count`: Integer (Optional)
* `genres_tags`: String / JSON Array (e.g. `["History", "Space", "Punjabi", "Fiction"]`)
* `formats`: String / JSON Array (e.g. `["physical", "kindle", "epub", "pdf"]`)
* `location_room`: String (e.g. "Office")
* `location_unit`: String (e.g. "Main Shelf")
* `location_shelf`: String (e.g. "Shelf 2")
* `read_count`: Integer (Default 0)
* `created_at`: Timestamp
* `updated_at`: Timestamp

### Readers Table
* `id`: UUID / Integer
* `name`: String (e.g., "Davinderpal", "Daughter 1", "Son", "Wife")
* `avatar_color_or_icon`: String
* `created_at`: Timestamp

### Reading_Sessions Table
* `id`: UUID / Integer
* `book_id`: Foreign Key (`books.id`)
* `reader_id`: Foreign Key (`readers.id`)
* `status`: Enum (`to_read`, `reading`, `finished`)
* `current_page`: Integer (Default 0)
* `start_date`: Date
* `finish_date`: Date (Nullable)
* `notes`: Text (Optional)

---

## 2. Hermes REST API Specification (Draft)

### `GET /api/books`
* **Query Params**: `q`, `genre`, `format`, `status`, `location`, `limit`, `offset`
* **Response**: `[ { "id": 1, "title": "...", "author": "...", "cover_url": "...", "location": "Office / Shelf 2", "status": "available", "current_reader": null } ]`

### `GET /api/books/recommend`
* **Query Params**: `topic`, `age`, `exclude_reader_id`
* **Response**: Ranked candidates matching genre/topic keywords and age criteria with physical shelf location strings.

### `GET /api/readers/activity`
* **Response**: Current active reading sessions with book titles, reader names, and page percentage.
