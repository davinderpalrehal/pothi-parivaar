import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  LANGUAGE_OPTIONS,
  MISSING_LANGUAGE_VALUE,
  additionalLanguageList,
  languageChipLabel,
  languageDetailLabel,
  languageFilterOptions,
  languageFilterParams,
  languageLabel,
  languageRule,
  normalizeLanguage,
} from './languages.js'

test('shortlist holds the six seed codes as {code,label} objects', () => {
  assert.deepEqual(
    LANGUAGE_OPTIONS.map((item) => item.code),
    ['pan', 'eng', 'hin', 'san', 'urd', 'mul']
  )
  for (const item of LANGUAGE_OPTIONS) {
    assert.equal(typeof item.code, 'string')
    assert.ok(item.label)
  }
})

test('normalize trims and lowercases a typed code', () => {
  assert.equal(normalizeLanguage('PAN'), 'pan')
  assert.equal(normalizeLanguage('  Pan  '), 'pan')
})

test('normalize treats empty and nullish input as no language', () => {
  assert.equal(normalizeLanguage(''), null)
  assert.equal(normalizeLanguage('   '), null)
  assert.equal(normalizeLanguage(null), null)
  assert.equal(normalizeLanguage(undefined), null)
})

test('normalize rejects anything that is not exactly three ASCII letters', () => {
  assert.equal(normalizeLanguage('punjabi'), null)
  assert.equal(normalizeLanguage('pa'), null)
  assert.equal(normalizeLanguage('pa1'), null)
  assert.equal(normalizeLanguage('pa-'), null)
  assert.equal(normalizeLanguage('ਪੰਜ'), null)
})

test('normalize unwraps the object a combobox returns for a picked item', () => {
  assert.equal(normalizeLanguage({ code: 'pan', label: 'Punjabi' }), 'pan')
  assert.equal(normalizeLanguage({ code: '  ENG ', label: 'English' }), 'eng')
  assert.equal(normalizeLanguage({ label: 'Punjabi' }), null)
})

test('normalize accepts an unknown but well-formed code', () => {
  assert.equal(normalizeLanguage('zzz'), 'zzz')
})

test('label names shortlist codes', () => {
  assert.equal(languageLabel('pan'), 'Punjabi')
  assert.equal(languageLabel('PAN'), 'Punjabi')
  assert.equal(languageLabel('mul'), 'Multiple languages')
})

test('label falls back to the uppercased code for unknown languages', () => {
  assert.equal(languageLabel('zzz'), 'ZZZ')
})

test('label is empty for missing or malformed input', () => {
  assert.equal(languageLabel(null), '')
  assert.equal(languageLabel(''), '')
  assert.equal(languageLabel('punjabi'), '')
})

test('rule accepts blank input -- absent language is legitimate', () => {
  assert.equal(languageRule(null), true)
  assert.equal(languageRule(undefined), true)
  assert.equal(languageRule(''), true)
  assert.equal(languageRule('   '), true)
})

test('rule accepts a well-formed code and a picked shortlist object', () => {
  assert.equal(languageRule('pan'), true)
  assert.equal(languageRule('PAN'), true)
  assert.equal(languageRule({ code: 'pan', label: 'Punjabi' }), true)
})

test('rule rejects a non-code with a message, not silent loss', () => {
  const result = languageRule('punjabi')
  assert.notEqual(result, true)
  assert.equal(typeof result, 'string')
  assert.match(result, /3-letter/)
})

test('additional list splits, trims and drops empties', () => {
  assert.deepEqual(additionalLanguageList('eng', 'san, hin'), ['san', 'hin'])
  assert.deepEqual(additionalLanguageList('eng', ' san ,hin '), ['san', 'hin'])
})

test('additional list drops the primary repeated among the extras', () => {
  assert.deepEqual(additionalLanguageList('eng', 'eng, san'), ['san'])
  assert.deepEqual(additionalLanguageList('eng', 'ENG , san'), ['san'])
})

test('additional list is empty when there is nothing to add', () => {
  assert.deepEqual(additionalLanguageList('eng', null), [])
  assert.deepEqual(additionalLanguageList('eng', ''), [])
  assert.deepEqual(additionalLanguageList(null, ''), [])
})

test('additional list keeps free-text entries when there is no primary', () => {
  // A primary of null must not swallow entries that also fail to normalize.
  assert.deepEqual(additionalLanguageList(null, 'punjabi, san'), ['punjabi', 'san'])
})

test('chip label suffixes +N for the matrix multi-language row', () => {
  assert.equal(languageChipLabel('eng', 'san, hin'), 'English +2')
})

test('chip label omits the suffix when no extras remain after dedup', () => {
  assert.equal(languageChipLabel('eng', 'eng'), 'English')
  assert.equal(languageChipLabel('pan', ''), 'Punjabi')
  assert.equal(languageChipLabel('pan', null), 'Punjabi')
})

test('chip label ignores a trailing comma rather than counting it', () => {
  assert.equal(languageChipLabel('eng', 'san, hin,'), 'English +2')
  assert.equal(languageChipLabel('eng', 'san,'), 'English +1')
})

test('chip label is empty without a primary -- no primary means no chip', () => {
  assert.equal(languageChipLabel(null, 'san, hin'), '')
  assert.equal(languageChipLabel('', ''), '')
  assert.equal(languageChipLabel('punjabi', 'san'), '')
})

test('detail label names the extras instead of counting them', () => {
  assert.equal(languageDetailLabel('eng', 'san, hin'), 'English (also Sanskrit, Hindi)')
  assert.equal(languageDetailLabel('eng', 'san, hin,'), 'English (also Sanskrit, Hindi)')
})

test('detail label is just the primary when no extras remain', () => {
  assert.equal(languageDetailLabel('pan', ''), 'Punjabi')
  assert.equal(languageDetailLabel('pan', 'pan'), 'Punjabi')
})

test('detail label still reports extras when no primary was set', () => {
  assert.equal(languageDetailLabel(null, 'san, hin'), 'Also: Sanskrit, Hindi')
  assert.equal(languageDetailLabel('', 'san'), 'Also: Sanskrit')
})

test('detail label falls back to raw text for unrecognized extras', () => {
  assert.equal(languageDetailLabel('eng', 'punjabi'), 'English (also punjabi)')
  assert.equal(languageDetailLabel(null, 'punjabi'), 'Also: punjabi')
})

test('detail label is empty when there is no language at all', () => {
  assert.equal(languageDetailLabel(null, null), '')
  assert.equal(languageDetailLabel('', ''), '')
})

test('mul is a real shortlist code, not a placeholder', () => {
  assert.equal(languageLabel('mul'), 'Multiple languages')
  assert.equal(normalizeLanguage('MUL'), 'mul')
  assert.equal(languageChipLabel('mul', null), 'Multiple languages')
})

// =============================================================================
// Catalog filter helpers
// =============================================================================

test('filter options carry labels and counts, with the missing entry last', () => {
  assert.deepEqual(
    languageFilterOptions({
      languages: [
        { code: 'pan', book_count: 18 },
        { code: 'eng', book_count: 4 },
      ],
      missing_count: 3,
    }),
    [
      { title: 'Punjabi (18)', value: 'pan' },
      { title: 'English (4)', value: 'eng' },
      { title: 'No language set (3)', value: '__none__' },
    ]
  )
})

test('a code outside the entry shortlist still gets an option', () => {
  assert.deepEqual(
    languageFilterOptions({ languages: [{ code: 'tam', book_count: 1 }], missing_count: 0 }),
    [{ title: 'TAM (1)', value: 'tam' }]
  )
})

test('no missing entry when nothing is unset', () => {
  const items = languageFilterOptions({
    languages: [{ code: 'pan', book_count: 2 }],
    missing_count: 0,
  })
  assert.equal(items.length, 1)
  assert.ok(!items.some((item) => item.value === MISSING_LANGUAGE_VALUE))
})

test('an empty catalog yields no options at all', () => {
  assert.deepEqual(languageFilterOptions({ languages: [], missing_count: 0 }), [])
})

test('a missing or malformed summary degrades to an empty list', () => {
  assert.deepEqual(languageFilterOptions(undefined), [])
  assert.deepEqual(languageFilterOptions({}), [])
  assert.deepEqual(languageFilterOptions({ languages: null, missing_count: null }), [])
})

test('params map to exactly one query key, or none', () => {
  assert.deepEqual(languageFilterParams('pan'), { language: 'pan' })
  assert.deepEqual(languageFilterParams(MISSING_LANGUAGE_VALUE), { missing_language: true })
  assert.deepEqual(languageFilterParams(null), {})
  assert.deepEqual(languageFilterParams(''), {})
})

test('params never emit both keys at once', () => {
  for (const value of ['pan', MISSING_LANGUAGE_VALUE, null, '', 'nonsense']) {
    const params = languageFilterParams(value)
    assert.ok(!('language' in params && 'missing_language' in params))
  }
})

test('a server code outside the 3-letter shape still produces a filter', () => {
  // The endpoint normalizes case but does not enforce the shape on read, so the
  // control must not silently degrade to "no filter" and show everything.
  assert.deepEqual(languageFilterParams('english'), { language: 'english' })
  assert.deepEqual(languageFilterParams('  ENGLISH  '), { language: 'english' })
})

test('a selected option always maps back to a filter', () => {
  const summary = {
    languages: [
      { code: 'pan', book_count: 2 },
      { code: 'tam', book_count: 1 },
    ],
    missing_count: 4,
  }
  for (const item of languageFilterOptions(summary)) {
    assert.notDeepEqual(languageFilterParams(item.value), {}, item.title)
  }
})
