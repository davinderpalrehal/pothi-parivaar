# Stub — 3.1 Generic reader roles

**Priority:** high  
**Status:** backlog stub (not ready-for-dev)  
**Tomorrow:** run `[BD] Build` (`bmad-build`) in a **fresh chat** with this file as the intent.

## Intent (draft)

Add Reader currently hard-codes family-specific labels with ages in `ReaderTracker.vue` (`ageGroupOptions`: Child 10yo Eldest, Child 7yo Middle, Toddler 2yo Youngest, Parent/Adult, Grandparent). Replace with **generic life-stage labels that never mention years**.

## Proposed labels (starting point — confirm in Build)

Stored `value` stays stable; **titles** are what people see:

| value (draft) | Label |
|---------------|--------|
| `infant` | Infant |
| `child` | Child |
| `preteen` | Pre-teen |
| `teen` | Teen |
| `adult` | Adult |

Map existing rows: `child-2` → infant, `child-7` → child, `child-10` → preteen (or child — confirm), `adult` stays, `grandparent` → adult.

## Likely touchpoints

- `frontend/src/components/ReaderTracker.vue` (`ageGroupOptions`, `formatAgeGroup`, default `child-10`)
- `app/models.py` `Reader.age_group` (already a free string)
- `tests/test_readers_and_sessions.py` fixtures using `child-10` / `child-7`

## Out of scope for this stub

- Per-reader birthdates
- Hermes age_appropriate recommend (deferred FR-13)
