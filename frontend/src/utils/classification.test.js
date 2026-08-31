import { test } from 'node:test'
import assert from 'node:assert/strict'
import { CLASS_SOURCE_DEFAULT, hasNoClassSignal } from './classification.js'

test('a "default" source means the class is only a fallback', () => {
  assert.equal(hasNoClassSignal('default'), true)
  assert.equal(hasNoClassSignal(CLASS_SOURCE_DEFAULT), true)
})

test('a real keyword match is not flagged', () => {
  assert.equal(hasNoClassSignal('title'), false)
  assert.equal(hasNoClassSignal('genres'), false)
})

test('no fetch having run is not flagged', () => {
  // The dialog opened on a book that already has a stored call number, so the
  // watcher skipped the fetch and the ref still holds its reset value.
  assert.equal(hasNoClassSignal(''), false)
  assert.equal(hasNoClassSignal(undefined), false)
  assert.equal(hasNoClassSignal(null), false)
})

test('the exported constant is the literal the API sends', () => {
  assert.equal(CLASS_SOURCE_DEFAULT, 'default')
})
