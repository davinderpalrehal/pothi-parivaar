// Language is entered by a human and never guessed. These helpers only
// normalize and label what was typed or picked; they never infer a default.

export const LANGUAGE_OPTIONS = [
  { code: 'pan', label: 'Punjabi' },
  { code: 'eng', label: 'English' },
  { code: 'hin', label: 'Hindi' },
  { code: 'san', label: 'Sanskrit' },
  { code: 'urd', label: 'Urdu' },
  { code: 'mul', label: 'Multiple languages' },
]

const LABEL_BY_CODE = new Map(LANGUAGE_OPTIONS.map((item) => [item.code, item.label]))

const CODE_PATTERN = /^[a-z]{3}$/

const INVALID_CODE_MESSAGE = 'Use a 3-letter ISO 639-3 code (e.g. pan)'

/**
 * Normalize free-entry or selected language input to a lowercase ISO 639-3
 * code. Accepts a raw string, or the `{ code, label }` object a v-combobox
 * returns when a shortlist item is picked. Returns null when the input is
 * empty or is not exactly three ASCII letters.
 */
export function normalizeLanguage(input) {
  if (input == null) return null

  if (typeof input === 'object') {
    return normalizeLanguage(input.code ?? input.value ?? null)
  }

  const trimmed = String(input).trim().toLowerCase()
  if (!trimmed) return null
  return CODE_PATTERN.test(trimmed) ? trimmed : null
}

/**
 * Human-readable label for a language code. Known shortlist codes get their
 * name; anything else falls back to the uppercased code. Empty input yields ''.
 */
export function languageLabel(code) {
  const normalized = normalizeLanguage(code)
  if (!normalized) return ''
  return LABEL_BY_CODE.get(normalized) ?? normalized.toUpperCase()
}

/**
 * Vuetify field rule for the language combobox. Blank is allowed -- absent
 * language means NULL. Anything non-blank must be a well-formed code, so a
 * typo surfaces inline instead of being silently discarded on submit.
 */
export function languageRule(value) {
  if (value == null) return true
  if (typeof value === 'string' && !value.trim()) return true
  return normalizeLanguage(value) !== null || INVALID_CODE_MESSAGE
}

/**
 * The additional languages worth showing alongside a primary: the `", "`-joined
 * string split into trimmed, non-empty entries, minus any entry that is just
 * the primary repeated. Entries stay as typed -- free text is deliberate here.
 */
export function additionalLanguageList(language, additionalLanguages) {
  const primary = normalizeLanguage(language)
  return String(additionalLanguages ?? '')
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
    .filter((part) => !(primary && normalizeLanguage(part) === primary))
}

function labelOrRaw(entry) {
  return languageLabel(entry) || entry
}

/**
 * Compact card chip text: the primary language label, suffixed ` +N` when N
 * additional languages remain. No primary means no chip, so return ''.
 */
export function languageChipLabel(language, additionalLanguages) {
  const primary = languageLabel(language)
  if (!primary) return ''
  const extras = additionalLanguageList(language, additionalLanguages)
  return extras.length ? `${primary} +${extras.length}` : primary
}

/**
 * Expanded detail-view text. Names every language rather than counting them,
 * and still reports extras when no primary was ever set so nothing the user
 * typed goes unseen.
 */
export function languageDetailLabel(language, additionalLanguages) {
  const primary = languageLabel(language)
  const extras = additionalLanguageList(language, additionalLanguages).map(labelOrRaw)

  if (!primary) return extras.length ? `Also: ${extras.join(', ')}` : ''
  return extras.length ? `${primary} (also ${extras.join(', ')})` : primary
}

/**
 * Sentinel for the "No language set" filter choice. Cannot collide with a real
 * value: every stored language is exactly three ASCII letters, enforced by the
 * API validator and by `normalizeLanguage` here.
 */
export const MISSING_LANGUAGE_VALUE = '__none__'

/**
 * Build v-select items from the catalog-languages summary. Titles carry the
 * count so the librarian can see the size of each group. The "No language set"
 * entry is appended LAST rather than sorted into the count order -- it is a
 * different kind of thing from a language, and with most of the collection
 * unset it would otherwise dominate the top of the list. It is omitted entirely
 * when nothing is unset.
 */
export function languageFilterOptions(summary) {
  const languages = Array.isArray(summary?.languages) ? summary.languages : []

  const items = languages.map((entry) => ({
    title: `${languageLabel(entry.code) || entry.code} (${entry.book_count})`,
    value: normalizeLanguage(entry.code) ?? entry.code,
  }))

  const missingCount = Number(summary?.missing_count) || 0
  if (missingCount > 0) {
    items.push({
      title: `No language set (${missingCount})`,
      value: MISSING_LANGUAGE_VALUE,
    })
  }

  return items
}

/**
 * Map the selected filter value to the query fragment for GET /books. Returns
 * an empty object when nothing is selected, so a cleared filter sends neither
 * param -- and never both at once.
 */
export function languageFilterParams(value) {
  if (value === MISSING_LANGUAGE_VALUE) return { missing_language: true }

  const code = normalizeLanguage(value)
  if (code) return { language: code }

  // The option list comes from the server, which normalizes stored codes but
  // does not enforce the 3-letter shape on read. Pass an odd code through
  // rather than send no filter at all -- that would silently show the whole
  // catalog while the control claims to be filtering.
  const raw = typeof value === 'string' ? value.trim().toLowerCase() : ''
  return raw ? { language: raw } : {}
}
