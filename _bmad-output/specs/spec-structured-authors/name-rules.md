# Name split and display rules

Single contract for ISBN prefill, the one-time migration script, and catalog short form. Honorific matching uses the persisted list seeded in `honorifics.md`.

## Split a stored or API author string

1. Split the string on `,` to get author segments. Trim each segment. Drop empty segments.
2. For each segment, split on ASCII space and drop empty tokens.
3. If there are no tokens, skip the segment (do not create an author).
4. If there is one token (mononym): first name = that token; last name = a single space; middle name omitted.
5. If there are two or more tokens: first name = first token; last name = last token; middle name = any leftover tokens joined with a single space, or omitted when none.

This split does **not** move titles into other columns. Titles stay in first/middle/last. Changing the honorific list does not re-split stored authors.

Examples:

| Input | Authors |
| --- | --- |
| `Dale Carnegie` | first=`Dale`, last=`Carnegie` |
| `Dale B. Carnegie` | first=`Dale`, middle=`B.`, last=`Carnegie` |
| `John Ronald Reuel Tolkien` | first=`John`, middle=`Ronald Reuel`, last=`Tolkien` |
| `Dale Carnegie, Jane Doe` | two authors: Dale/Carnegie and Jane/Doe |
| `D. Carnegie` | first=`D.`, last=`Carnegie` |
| `Dr. Davinder Singh` | first=`Dr.`, middle=`Davinder`, last=`Singh` |
| `Bhai Sahib Bhai Vir Singh ji` | first=`Bhai`, middle=`Sahib Bhai Vir Singh`, last=`ji` |
| `Plato` | first=`Plato`, last=` ` (one space) |
| `Unknown Author` | first=`Unknown`, last=`Author` |
| `` (empty) | zero authors |

## Catalog short form

Rebuild the token sequence: first name, then middle tokens, then last name unless last name is a single space (omit that last token).

Peel recognized **prefix** honorifics from the front and **suffix** honorifics from the end using the persisted list (`honorifics.md`). Longest match first. Collect prefix abbreviations in peel order; skip any with an empty abbreviation.

Personal name = tokens left after peeling.

- If no personal tokens remain: show the joined prefix abbreviations, or the reconstructed first name if none.
- If last name was a single space and only one personal token remains (mononym): show prefix abbreviations + that token unchanged (`Plato`, `Sant Plato`).
- Otherwise: first character of the first personal token + `. ` + last personal token. Do not show leftover middle personal tokens. Prepend prefix abbreviations with a single space before that core.

Examples (with the seed list):

| Reconstructed / stored parts | Card |
| --- | --- |
| Dale Carnegie | `D. Carnegie` |
| Dale B. Carnegie | `D. Carnegie` |
| Dr. Davinder Singh | `Dr. D. Singh` |
| Bhai Sahib Bhai Vir Singh ji | `BHB V. Singh` |
| Plato (last = space) | `Plato` |
| Madonna (last = space) | `Madonna` |
| Cher (last = space) | `Cher` |

Multiple authors on a book: those short forms, comma-separated, in book-author order.

`Dale Carnegie` + `Jane Doe` → `D. Carnegie, J. Doe`.
`Plato` + `Jane Doe` → `Plato, J. Doe`.
`Dr. Davinder Singh` + `Jane Doe` → `Dr. D. Singh, J. Doe`.
