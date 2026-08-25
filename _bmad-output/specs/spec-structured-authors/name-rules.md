# Name split and display rules

Single contract for ISBN prefill, the one-time migration script, and catalog short form.

## Split a stored or API author string

1. Split the string on `,` to get author segments. Trim each segment. Drop empty segments.
2. For each segment, split on ASCII space and drop empty tokens.
3. If there are no tokens, skip the segment (do not create an author).
4. If there is one token (mononym): first name = that token; last name = a single space; middle name omitted.
5. If there are two or more tokens: first name = first token; last name = last token; middle name = any leftover tokens joined with a single space, or omitted when none.

Examples:

| Input | Authors |
| --- | --- |
| `Dale Carnegie` | first=`Dale`, last=`Carnegie` |
| `Dale B. Carnegie` | first=`Dale`, middle=`B.`, last=`Carnegie` |
| `John Ronald Reuel Tolkien` | first=`John`, middle=`Ronald Reuel`, last=`Tolkien` |
| `Dale Carnegie, Jane Doe` | two authors: Dale/Carnegie and Jane/Doe |
| `D. Carnegie` | first=`D.`, last=`Carnegie` |
| `Plato` | first=`Plato`, last=` ` (one space) |
| `Unknown Author` | first=`Unknown`, last=`Author` |
| `` (empty) | zero authors |

## Catalog short form

For an author with a non-space last name: first character of first name + `. ` + last name.

`Dale Carnegie` → `D. Carnegie`. Middle name is not shown.

When last name is a single space (mononym): display the first name unchanged.

`Plato` → `Plato`. `Madonna` → `Madonna`. `Cher` → `Cher`. Not `P.`, `M.`, or `C.`.

Multiple authors on a book: those short forms, comma-separated, in book-author order.

`Dale Carnegie` + `Jane Doe` → `D. Carnegie, J. Doe`.
`Plato` + `Jane Doe` → `Plato, J. Doe`.
