---
title: "PRD: Pothi Parivaar"
status: final
created: 2026-08-20
updated: 2026-08-20
---

# PRD: Pothi Parivaar
*Home Library & Reading Companion for the Rehal Family*

## 0. Document Purpose

This Product Requirements Document (PRD) defines the functional requirements, user journeys, data models, and API surface for **Pothi Parivaar** V1. It translates the approved [Product Brief](file:///Users/davinderpalrehal/Projects/pothi-parivaar/_bmad-output/planning-artifacts/briefs/brief-pothi-parivaar-2026-08-20/brief.md) into concrete, testable specifications for the engineering and architecture phases. Downstream workflows (Architecture `bmad-architecture`, Epics & Stories `bmad-create-epics-and-stories`, and Build `bmad-build`) derive their invariants and tasks directly from the globally numbered Functional Requirements (FR-1 through FR-14) in this document.

---

## 1. Vision

**Pothi Parivaar** (*Pothi* = Book, *Parivaar* = Family) is a centralized, mobile-first home library and reading tracking platform built to catalog and breathe active life into a generational collection of 1,000+ physical and digital books.

In an age where conversational AI offers instant, effortless summaries, Pothi Parivaar is built around an intentional philosophy: cultivating deep reading habits, bibliographical literacy, and disciplined research skills in growing children (ages 10 and 7). Instead of using AI as a crutch that replaces reading, the platform exposes a clean REST API on the VPS to integrate with a self-hosted **Hermes AI Agent**. Hermes serves as an intelligent family librarian and reading mentor—helping family members discover relevant physical books on their shelves, explore new topics, and track their reading milestones.

---

## 2. Target Users & Key User Journeys

### 2.1 Jobs To Be Done (JTBD)
* **For Kids (10yo & 7yo)**: "Help me find exciting books to read for my hobbies and school projects, see what page I'm on, and feel proud of finishing books."
* **For Parents & Grandparents**: "Help us organize our 1,000+ book home collection into clear physical locations, catalog new/existing books quickly, and see our children's reading progress."
* **For Hermes AI Agent (VPS)**: "Allow me to query the family's book catalog, check book locations, and recommend age-appropriate reads to family members during conversations."

### 2.2 Non-Users (V1)
* **Toddler (2yo)**: Not interacting directly with the app in V1; parents can curate picture books on her behalf.
* **External Public / Community**: V1 is strictly single-tenant for the immediate family on the VPS; no public registration or multi-tenant isolation.

### 2.3 Key User Journeys

#### UJ-1: Eldest Daughter (10yo) Catalogs a Book & Tracks Reading
> **Context**: She has created a physical index card for a history book and wants to record it and track her reading.  
> **Flow**: She opens the mobile web app, taps **"Add Book"**, and types the Title, Author, Year, and selects `Office / Main Shelf / Shelf 2`. She saves the book, taps **"Start Reading"**, selecting her name. Over the next three days, she opens the app to update her current page (`Page 45` → `Page 120`). Upon finishing, she taps **"Mark as Finished"**; the book records a completion date and increments the book's total read count to 1.

#### UJ-2: Younger Child (7yo) Browses by Cover & Genre
> **Context**: Looking for an animal or adventure book to read before bed.  
> **Flow**: He opens the web app on a tablet, sees large visual cover tiles, and taps the **"Adventures"** genre filter. He sees a book titled *"The Secret Island"* marked with a badge: `Living Room / Shelf 1`. He shows the location to his parent to grab the physical book from the shelf and sets his reading status to **"Reading"**.

#### UJ-3: Parent / Grandparent Rapid Ingestion via ISBN
> **Context**: Organizing a stack of 20 newly sorted books from the office floor.  
> **Flow**: The parent opens **"Add Book"**, selects **"ISBN Lookup"**, enters or scans the 13-digit ISBN. The app auto-fetches title, author, publication year, description, and cover image from Open Library/Google Books. The parent confirms the physical location as `Office / Bookcase B / Shelf 3` and taps **"Save & Add Next"**.

#### UJ-4: Hermes Agent Recommends a Book via VPS REST API
> **Context**: Davinderpal asks Hermes in their family chat: *"Can you suggest a book we have on astronomy or space for my 10-year-old?"*  
> **Flow**: Hermes calls the Pothi Parivaar REST endpoint `GET /api/books?topic=space&age_group=10`. Pothi Parivaar returns 2 matching titles with their shelf locations. Hermes responds: *"You have 'Cosmos & Stars' located in your Office on Shelf 2. Neither of the kids has read it yet!"*

---

## 3. Glossary

* **Book**: The core bibliographic entity representing a title, which may exist in physical format, digital format, or both.
* **Physical Location**: A hierarchical location descriptor (e.g., `Location: Office` → `Unit: Main Bookcase` → `Shelf: Shelf 2`).
* **Format**: The manifestation of a book (`Physical`, `Kindle`, `EPUB`, `PDF`).
* **Reader**: A named family member profile (e.g., Davinderpal, Daughter 1 [10yo], Child 2 [7yo], Wife).
* **Reading Session**: An active tracking record connecting a Reader to a Book, storing start date, finish date, current page, total pages, and status (`To Read`, `Reading`, `Finished`).
* **Read Count**: Cumulative counter tracking how many times a book has been completed across all family members.
* **Hermes Skill**: The client integration script running on the VPS enabling the Hermes agent to interact with Pothi Parivaar via REST endpoints.

---

## 4. Features & Functional Requirements

### 4.1 Book Catalog & Search
**Description**: The central library view allowing family members to browse, search, filter, and inspect books. Optimized for mobile touchscreens with clear cover cards, instant keyword search, and genre/location filters. Realizes UJ-1, UJ-2.

#### FR-1: Book Creation & Editing
Any family member can create or update a Book record with fields: Title, Author(s), Publication Year, ISBN (optional), Genres/Tags, Cover Image (URL or upload), Summary, Page Count, Format(s), and Physical Location.
* *Consequences*: New books immediately appear in the catalog and are searchable via UI and API.
* *Out of Scope*: Mandatory ISBN requirement (manual entry without ISBN is fully supported).

#### FR-2: Search & Multi-Filter Catalog
Users can search books by keyword (title, author, tags) and filter by Format (`Physical`, `Kindle`, `EPUB`, `PDF`), Genre/Topic, Physical Location, and Reading Status.
* *Consequences*: Instant responsive filtering (<100ms response for local SQLite/Postgres catalog).

#### FR-3: Book Detail View & Physical Location Display
Viewing a book displays all metadata, cover art, its exact physical shelf location badge, digital format links, and current/past reader history.
* *Consequences*: Location badge is clearly styled and legible for children (e.g. `📍 Office ➔ Main Shelf ➔ Shelf 3`).

#### FR-4: Book Deletion & Archiving
Users can remove or archive a book record.
* *Consequences*: Deletion prompts a confirmation dialog to prevent accidental deletion by children.

---

### 4.2 Dual Ingestion Engine (Pedagogical Manual Entry & Fast ISBN Lookup)
**Description**: Supports both the children's educational workflow (inspecting physical book colophons and typing index info) and fast automated ingestion for parents. Realizes UJ-1, UJ-3.

#### FR-5: Manual Bibliographical Input Mode
The "Add Book" interface provides clean, prominent manual input fields (Title, Author, Year, Location, Tags) allowing children to enter book details without requiring an ISBN or external API call.
* *Consequences*: Submitting form creates book with status `available` and stores all manual metadata accurately.

#### FR-6: ISBN Autofill Lookup
The "Add Book" interface includes a prominent ISBN lookup action. Entering a valid 10-digit or 13-digit ISBN queries public book APIs (Open Library / Google Books) to autofill title, author, publication date, description, cover image URL, and page count.
* *Consequences*: Autofilled fields remain fully editable before saving. If ISBN is not found, user is gracefully notified and can continue with manual entry.

---

### 4.3 Physical Shelf & Digital Asset Tracking
**Description**: Links every book to its real-world physical location in the home or digital asset type. Realizes UJ-1, UJ-2, UJ-3.

#### FR-7: Hierarchical Physical Location Management
The system supports configurable physical locations with a 3-tier hierarchy:
1. `Room / Location` (e.g., Office, Living Room, Kids Room)
2. `Unit / Bookcase` (e.g., Main Shelf, Bookcase A)
3. `Shelf / Row` (e.g., Shelf 1, Top Shelf)
* *Consequences*: Users can pick existing locations from a dropdown or quickly type a new shelf location.

#### FR-8: Digital Format Association
Books can be flagged with digital formats (`Kindle`, `EPUB`, `PDF`) with optional local file path or cloud link note.
* *Consequences*: Catalog items indicate format icons (e.g. 📖 Physical, 📱 Kindle, 📄 PDF).

---

### 4.4 Active Reader & Reading Progress Tracking
**Description**: Tracks who in the family is reading what, progress by page, and records reading milestones and total read counts. Realizes UJ-1, UJ-2.

#### FR-9: Reader Profiles & Assignment
The system provides a lightweight list of named Family Readers (e.g., Davinderpal, Daughter 1 [10yo], Child 2 [7yo], Wife). Any reader can be assigned as the active reader of a book with one tap.
* *Consequences*: No passwords or login walls required in V1; selecting a reader is frictionless.

#### FR-10: Page Progress & Bookmark Updates
Active readers can update their current page number on an in-progress book.
* *Consequences*: The UI displays a visual progress bar (e.g., `Page 84 of 250 (34%)`).

#### FR-11: Reading Lifecycle & History Log
Books transition through states: `Available` → `Reading` → `Finished`. Marking a book as `Finished` records the completion timestamp, assigns it to the reader's history, and increments the book's `read_count`.
* *Consequences*: The book detail screen shows the lifetime read count and list of completed reading sessions.

---

### 4.5 Hermes AI Agent REST API
**Description**: Exposes clean, lightweight REST endpoints on `localhost` (VPS) enabling the Hermes agent to query and interact with the library. Realizes UJ-4.

#### FR-12: Book Search & Query Endpoint (`GET /api/books`)
API endpoint allowing query parameters: `query`, `author`, `genre`, `format`, `location`, `status`, and `limit`.
* *Consequences*: Returns JSON list of books with title, author, year, cover, location, and reading status.

#### FR-13: Recommendation Helper Endpoint (`GET /api/books/recommend`)
API endpoint accepting `topic`, `age_appropriate` (e.g. 7, 10, adult), and `exclude_read_by` parameters.
* *Consequences*: Returns ranked candidates suitable for Hermes to formulate conversational suggestions.

#### FR-14: Reader Status & Activity Endpoint (`GET /api/readers/activity`)
API endpoint returning currently active reading sessions across all family members.
* *Consequences*: Hermes can report who is currently reading what and current page progress.

---

## 5. Non-Goals (Explicit for V1)

* **[NON-GOAL] In-App Digital Reader**: Pothi Parivaar is a catalog, location, and progress tracker; it will not render an in-browser EPUB or PDF reader in V1.
* **[NON-GOAL] Complex Multi-User Authentication**: No user passwords, OAuth, or permission lockdowns in V1. All family members share the single local web interface.
* **[NON-GOAL] Multi-Tenant / Public Sharing**: No community lending or multi-family accounts in V1.
* **[NON-GOAL] Full Digital Note-taking Sync**: Deep notes and reading journals remain on physical paper index cards / notebooks in V1.

---

## 6. MVP Scope Summary

| Area | In Scope (V1) | Deferred (V2 / V3) |
| :--- | :--- | :--- |
| **Catalog** | Full CRUD, cover images, multi-format tags, instant search | Barcode scanner camera streaming, bulk CSV export/import |
| **Ingestion** | Manual entry form + ISBN Open Library auto-fetch | Batch OCR index-card scanning |
| **Locations** | 3-tier hierarchy (`Room` → `Unit` → `Shelf`) | Visual 2D shelf diagram / interactive map |
| **Readers** | Family reader selector, current page, start/end dates, read count | Gamified badges, reading speed analytics, streaks |
| **Agent API** | REST API for Hermes (`/api/books`, `/recommend`, `/activity`) | Bidirectional websocket alerts, voice assistant skill |

---

## 7. Success Metrics & Counter-Metrics

### Primary Metrics
* **SM-1 (Catalog Adoption)**: 100+ books cataloged within the first 2 weeks of VPS deployment. *(Validates FR-1, FR-5, FR-6)*.
* **SM-2 (Daily Kid Engagement)**: Children independently logging page progress or picking books at least 4 days a week. *(Validates FR-9, FR-10, FR-11)*.
* **SM-3 (Hermes Utility)**: Hermes successfully recommending available physical books in response to family queries. *(Validates FR-12, FR-13)*.

### Counter-Metrics (Do Not Optimize At Expense Of Vision)
* **SM-C1 (Speed over Learning)**: Do not optimize for 100% automated barcode scanning if it eliminates the children's opportunity to inspect physical books and practice manual cataloging.
* **SM-C2 (Screen Time vs. Reading Time)**: Time spent inside the web app should be minimal (search & log); reading time must happen with physical/digital books.

---

## 8. Cross-Cutting Non-Functional Requirements (NFRs)

* **NFR-1 (Performance)**: Web UI initial load < 1s; catalog search & filtering queries return in < 100ms on a 1,000+ item database.
* **NFR-2 (Mobile-First Responsiveness)**: Clean touch-friendly interface optimized for smartphone and tablet screens (large touch targets, readable typography).
* **NFR-3 (Deployment Simplicity)**: Single-container or lightweight self-hosted stack deployable on a Linux VPS alongside Hermes with minimal RAM/CPU footprint.
* **NFR-4 (Data Integrity & Backups)**: SQLite or Postgres database with automated local backups to ensure the family's catalog data is never lost.

---

## 9. Assumptions Index

* `[ASSUMPTION: V1-Auth]` No authentication/passwords needed because the app runs inside a private home network / VPS with private access or basic reverse-proxy protection.
* `[ASSUMPTION: ISBN-Provider]` Open Library API and Google Books API (free tiers) provide sufficient coverage for ISBN metadata and cover images.
* `[ASSUMPTION: Hermes-Network]` Hermes and Pothi Parivaar communicate over `http://localhost:<PORT>` on the same VPS instance without requiring complex token-based OAuth.
