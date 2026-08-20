---
title: "Product Brief: Pothi Parivaar"
status: complete
created: 2026-08-20
updated: 2026-08-20
---

# Product Brief: Pothi Parivaar

## Executive Summary

**Pothi Parivaar** (*Pothi* = Book, *Parivaar* = Family) is a home library and reading companion system designed to catalog, organize, and bring alive a generational collection of 1,000+ physical and digital books. Built as a mobile-first web application, it serves as the central hub for the family's books across physical bookshelves and digital formats (Kindle, EPUB, PDF).

In an era where conversational AI makes instant answers effortless, Pothi Parivaar is built on a deliberate counter-philosophy: cultivating deep reading habits, bibliographical literacy, and note-taking skills in growing children (ages 10 and 7). Rather than using AI as a shortcut that replaces reading, the system integrates with a self-hosted **Hermes AI Agent** on a VPS to act as a discovery guide and research mentor—pointing family members to the right books on their own shelves.

---

## The Problem

1. **The AI Shortcut Trap**: In a world of fast LLM summaries, children risk losing the vital discipline of long-form reading, primary source research, and synthesizing their own notes.
2. **The "Lost on the Shelf" Friction**: A 1,000+ book physical collection spanning an overflowing home office shelf and various rooms makes finding relevant books difficult. Books sit unread simply because their existence or exact location is forgotten.
3. **Fragmented Library Formats**: Books are scattered across physical bookcases, Kindle libraries, EPUBs, and PDFs, making it hard to see the family's total knowledge base in one place.
4. **Reading Tracking Gaps**: No clear visibility into who is currently reading what, bookmark/page progress, start/finish dates, or how many times a cherished book has been enjoyed across family members.

---

## The Solution

Pothi Parivaar provides a clean, unified, and kid-friendly platform featuring:

* **Physical Location Mapping**: Flexible, hierarchical location tags (Room → Bookcase → Shelf → Tag) so any family member can immediately locate a book on a physical shelf.
* **Unified Digital & Physical Index**: Track physical editions alongside Kindle, EPUB, and PDF assets in a single searchable catalog.
* **Dual Ingestion Engine**:
  * *Pedagogical Manual Entry*: Encourages children to inspect physical title pages, copyright notices, authors, and publication years, reinforcing real-world book knowledge.
  * *Prominent ISBN Lookup*: Instant metadata and cover retrieval for rapid cataloging by parents or grandparents.
* **Lightweight Reading Tracker**: Real-time reader assignment, current page/progress tracking, start and completion dates, and lifetime re-read counters.
* **Hermes AI Agent Integration**: Direct REST API on the VPS allowing the family Hermes agent to suggest relevant books based on topics, reader age, and shelf availability.

---

## What Makes This Different

* **Pedagogy Over Passive Automation**: Designed with intentional "healthy friction" that turns cataloging and searching into an educational activity for children.
* **Agentic Co-Pilot, Not Ghostwriter**: Repositions AI (Hermes) as an intelligent library curator that encourages children to open physical books and do deep research, rather than serving as the final answer.
* **Family Heritage Focus**: Built specifically around multi-generational collections (from grandparents' books to children's literature) with collective reading history.

---

## Who This Serves

* **Primary Users — Children (Ages 10 & 7)**:
  * *Eldest (10yo)*: Discovers research topics, manages index cards/cataloging, tracks reading goals and page progress.
  * *Middle (7yo)*: Browses visual covers, explores early reader categories, and tracks current books.
  * *(Toddler / 2yo)*: Future user as reading begins.
* **Secondary Users — Parents & Grandparents**:
  * Organize and sort shelves, bulk catalog with ISBN lookup, track family reading trends.
* **Machine Consumer — Hermes AI Agent**:
  * Queries library endpoints to answer family questions like *"What books do we have on astronomy for a 10yo?"* and suggest books to read.

---

## Scope & MVP Boundaries

### In Scope for V1
* **Catalog Management**: Add, edit, view, and search books (Title, Author, Year, Genre/Tags, ISBN, Cover).
* **Location Tracking**: Multi-location/shelf tagging (e.g. `Office / Main Shelf / Row 2`).
* **Format Flags**: Physical, Kindle, EPUB, PDF.
* **Reading Progress Tracker**: Reader selector, current page, reading status (To Read, In Progress, Completed), start/end dates, total read count.
* **Single Family Profile**: Frictionless shared catalog without complex permission walls or logins.
* **Hermes REST API & Skill**: Localhost endpoints for Hermes to search, query, and recommend books.

### Out of Scope for V1 (Future Roadmap)
* In-app digital EPUB/PDF reader (links/locations tracked only).
* In-depth digital note-taking / journal sync (physical notebooks used initially).
* User authentication / restricted access tiers.
* Multi-family lending or public community sharing.

---

## Success Criteria

1. **Physical Library Organized & Cataloged**: Transitioning the 1,000+ collection incrementally into tagged shelf locations.
2. **Daily / Weekly Kid Engagement**: Children independently using the app to log their page progress and pick their next read.
3. **Active Hermes Recommendations**: Hermes successfully querying Pothi Parivaar to suggest relevant physical/digital books during family inquiries.
4. **Zero Cataloging Burnout**: Smooth balance between kids' manual index-card entry and parents' ISBN lookup.

---

## Vision (2–3 Years)

Pothi Parivaar evolves into the living digital intellectual hearth of the family—a knowledge repository tracking decades of reading, integrated with family voice assistants and local AI agents, and potentially expandable to connect with cousins and local community book circles.
