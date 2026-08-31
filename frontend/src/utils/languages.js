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
