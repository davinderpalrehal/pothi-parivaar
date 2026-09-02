# Recognized author honorifics

Data contract for the short-form deriver. The running app persists this list so a household member can add, edit, disable, or delete rows without a code change. This file is the **seed** for a first install and the recovery baseline if the list is emptied.

Each row: **role** (`prefix` | `suffix`), **tokens** (space-separated, match order), **abbreviation** (card text; empty = omit from the card).

Matching: case-insensitive; a token matches with or without a trailing period (`Dr` = `Dr.`). Longest token count wins. Prefixes peel from the front of the reconstructed sequence; suffixes from the end. Repeat until no match. Disabled rows are ignored.

Do not seed `Singh`, `Kaur`, or `Guru` — those are names in this catalog.

## Seed — prefixes (longest first)

| Tokens | Abbreviation |
| --- | --- |
| Bhai Sahib Bhai | BHB |
| Bibi Sahib Bibi | BSB |
| Singh Sahib | S.S. |
| Sardar Bahadur | S.B. |
| Sardar Sahib | S. Sahib |
| Bhai Sahib | B.S. |
| Bibi Sahib | Bibi S. |
| Sant Baba | Sant Baba |
| Doctor | Dr. |
| Professor | Prof. |
| Reverend | Rev. |
| Honourable | Hon. |
| Honorable | Hon. |
| Dr | Dr. |
| Prof | Prof. |
| Rev | Rev. |
| Hon | Hon. |
| Fr | Fr. |
| Father | Fr. |
| Sr | Sr. |
| Sister | Sr. |
| Capt | Capt. |
| Captain | Capt. |
| Col | Col. |
| Colonel | Col. |
| Gen | Gen. |
| General | Gen. |
| Lt | Lt. |
| Lieutenant | Lt. |
| Maj | Maj. |
| Major | Maj. |
| Sgt | Sgt. |
| Sergeant | Sgt. |
| Sir | Sir |
| Dame | Dame |
| Lord | Lord |
| Lady | Lady |
| Bhai | Bhai |
| Bibi | Bibi |
| Baba | Baba |
| Mata | Mata |
| Sant | Sant |
| Gyani | Gyani |
| Giani | Gyani |
| Mahant | Mahant |
| Jathedar | Jath. |
| Granthi | Granthi |
| Kathakar | Kathakar |
| Ragi | Ragi |
| Sardar | S. |
| Sardarni | Sdn. |
| Ustad | Ustad |
| Pandit | Pt. |
| Pundit | Pt. |
| Pt | Pt. |
| Swami | Swami |
| Sri | Sri |
| Shri | Sri |
| Smt | Smt. |
| Shrimati | Smt. |
| Kumari | Km. |
| Maulana | Maulana |
| Hafiz | Hafiz |

## Seed — suffixes (omit on card)

| Tokens | Abbreviation |
| --- | --- |
| ji Maharaj | |
| jee | |
| ji | |
| sahiba | |
| sahib | |

## Editor (CAP-9)

A household member can create a row (tokens, role, abbreviation), change any field, disable it (kept but unused), or delete it. Changes apply to the next derived short form and to search against that form. Changing the list does not rewrite stored first/middle/last.

Duplicate tokens+role are rejected. Tokens must be non-empty.
