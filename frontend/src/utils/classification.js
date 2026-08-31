// The classification suggestion carries a `class_source` marker describing how
// its LCC class was reached: "genres" or "title" when a keyword actually
// matched, "default" when nothing did and the class is only a fallback.
//
// The marker describes the *suggestion*, never the book -- it is never sent
// back on PUT /books/{id}.

export const CLASS_SOURCE_DEFAULT = 'default'

/**
 * True when the suggestion matched nothing and the human should be asked
 * rather than handed the fallback class.
 *
 * Anything other than the literal "default" is treated as signal-present,
 * including the empty string and undefined: those mean no fetch ran at all
 * (the dialog opened on a book that already has a stored call number), and a
 * warning there would be about nothing.
 */
export function hasNoClassSignal(classSource) {
  return classSource === CLASS_SOURCE_DEFAULT
}
