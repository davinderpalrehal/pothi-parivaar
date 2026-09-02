---
title: 'Add Book as a full page'
type: 'feature'
created: '2026-09-02'
status: 'done'
review_loop_iteration: 0
baseline_commit: '9c31a1af1a2058bb10f09d662a17a3f2ce818bd0'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Add Book is a `v-dialog` (`max-width="650"`, not scrollable). On small screens the form is clipped and cannot be scrolled to ISBN lookup, authors, location, or Save.

**Approach:** Add Book is always a normal app view (same shell as Catalog / Honorifics). Remove the add-book dialog on all screen sizes. Book detail/edit stays a dialog.

## Boundaries & Constraints

**Always:**
- Keep dual ingestion: Manual Entry + ISBN Lookup, same fields, validation, Save to Library, Save & Add Next, and `POST /books` / ISBN / locations APIs.
- After Save to Library, return to Catalog and refresh lists the way `handleBookSaved` does today.
- After Save & Add Next, stay on the Add Book page with a reset form.
- App bar “Add Book” and empty-catalog CTA open this view, not a dialog.
- Vuetify 3 only; no custom themes/CSS; no backend/schema change.

**Ask First:**
- Adding `vue-router` or any new npm dependency.
- Changing Book Detail / edit to a page.
- Adding Add Book as a sixth drawer/tab/bottom-nav destination.

**Never:**
- Keep a parallel add-book modal for desktop.
- Change create-book payload shape or API contracts.
- Rewrite AuthorRows / location cascade / language comboboxes except as needed to live outside a dialog.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Open add | App bar or empty-catalog CTA | Full-page form in `v-main`; page scrolls; both tabs reachable | N/A |
| Save to Library | Valid form | Book created; view = catalog; lists refresh | Existing snackbar/alert on create failure; stay on page |
| Save & Add Next | Valid form | Book created; form reset; remain on Add Book | Same as today |
| Leave mid-form | Switch Catalog/Tracker/etc. | Leave Add Book view (no persistent dialog) | Unsaved data discarded (same as dialog close) |
| ISBN lookup | Valid ISBN on ISBN tab | Prefill + switch to Manual, as today | Existing lookup error UI |
| Small viewport | Phone-width with bottom nav | Form scrolls above bottom nav; actions not trapped off-screen | N/A |

</frozen-after-approval>

## Code Map

- `frontend/src/App.vue` -- Shell `currentView` plus `ADD_BOOK_VIEW` page branch (`v-else-if`, Honorifics pattern) with `pb-16` so actions clear mobile `v-bottom-navigation`. App bar and empty-catalog CTA call `goToAddBook`. `AddBookDialog` is inlined in `v-main` (`@saved` → `handleBookSaved`, `@done` → `viewAfterAddBookPersist({ addNext: false })`, `@cancel` → `viewAfterAddBookCancel()`). No `showAddBook` overlay. `shellView` uses `shellNavValue`; setter ignores Vuetify null-model sync while opening add-book. Bottom nav ~L309 does not include add.
- `frontend/src/utils/addBookView.js` -- Live navigation policy: `ADD_BOOK_VIEW`, `SHELL_VIEWS`, `shellNavValue`, `viewAfterAddBookPersist`, `viewAfterAddBookCancel`.
- `frontend/src/components/AddBookDialog.vue` -- Page `v-card` (no `v-dialog`/`modelValue`); tabs; ISBN `handleLookupISBN`; manual form; `persistBook`/`submit`/`submitAndAddNext`; `close` no-ops while `isSaving`; emits `saved` / `done` / `cancel`.
- `frontend/src/components/BookDetailDialog.vue` -- Edit/view dialog; **read-only for this story**.
- `frontend/src/services/api.js` -- `createBook`, `lookupISBN`, `getLocations`; **read-only**.
- `frontend/src/main.js` -- No vue-router; do not add one.
- `frontend/package.json` -- No vue-router; do not add deps.
- Frontend tests: `src/utils/addBookView.test.js` (source-matrix); other utils tests. Backend create/ISBN tests unchanged.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/components/AddBookDialog.vue` -- Convert to a non-dialog page (e.g. card/form in `v-main`): drop `v-dialog`/`modelValue`; keep tabs, form, persist, Save & Add Next; expose a cancel/back that returns to catalog without saving; emit `saved` (and optionally `done` for Save to Library vs stay).
- [x] `frontend/src/App.vue` -- Add `currentView === 'add-book'` branch (do not add drawer/tab/bottom-nav items). Wire app-bar and empty-catalog CTA to `currentView = 'add-book'`. Remove `showAddBook` and `AddBookDialog` v-model. Reuse `handleBookSaved` on save; Save to Library sets `currentView = 'catalog'`.
- [x] Manual small-viewport pass -- Browser MCP unavailable this session; covered by addBookView tests (no v-dialog, page in v-main, not a bottom-nav item). Live phone-width click-through still recommended.

**Acceptance Criteria:**
- Given any screen size, when Add Book is opened, then the user gets a scrolling page in the app shell, not a modal overlay.
- Given a successful Save to Library, when persist completes, then Catalog is shown and book lists refresh.
- Given a successful Save & Add Next, when persist completes, then the user remains on Add Book with an empty form.
- Given Book Detail, when a catalog book is opened, then edit/view is still `BookDetailDialog`.

## Spec Change Log

## Verification

**Commands:**
- `cd frontend && npm test` -- expected: all node:test suites pass, including addBookView matrix coverage.
- `cd frontend && npm run build` -- expected: Vite production build succeeds.

**Manual checks (if no CLI):**
- Phone-width (or narrow window): open Add Book, scroll through ISBN + full manual form; Cancel/Save sit above bottom nav (`pb-16` on the add-book branch).
- Desktop: Add Book still a page, not a centered dialog.
- Create one book via Save to Library (lands on Catalog) and one via Save & Add Next (stays, form clears).

## Suggested Review Order

**Shell navigation**

- App bar opens Add Book as a `currentView`, not a dialog flag.
  [`App.vue:71`](../../frontend/src/App.vue#L71)

- Page branch in `v-main` with mobile bottom padding and save/cancel wiring.
  [`App.vue:227`](../../frontend/src/App.vue#L227)

- Guard so null `shellView` does not bounce off Add Book.
  [`App.vue:363`](../../frontend/src/App.vue#L363)

- Shared add-book vs catalog destinations.
  [`addBookView.js:7`](../../frontend/src/utils/addBookView.js#L7)

**Form is a page**

- Card root replaces `v-dialog`.
  [`AddBookDialog.vue:2`](../../frontend/src/components/AddBookDialog.vue#L2)

- Save to Library emits `done`; Save & Add Next only resets.
  [`AddBookDialog.vue:471`](../../frontend/src/components/AddBookDialog.vue#L471)

- Cancel ignored while persist is in flight.
  [`AddBookDialog.vue:493`](../../frontend/src/components/AddBookDialog.vue#L493)

**Tests**

- Source-matrix coverage for the I/O table.
  [`addBookView.test.js:18`](../../frontend/src/utils/addBookView.test.js#L18)
