import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  authorsPayload,
  emptyAuthorRow,
  hasIncompleteAuthorRows,
  hydrateAuthorRows,
  isAuthorRowEmpty,
  isAuthorRowIncomplete,
} from './authors.js'

test('two authors: payload keeps order and drops empty extra rows', () => {
  const rows = [
    { first_name: 'Dale', last_name: 'Carnegie', middle_name: '' },
    { first_name: 'Jane', last_name: 'Doe', middle_name: '' },
    emptyAuthorRow(),
  ]
  assert.deepEqual(authorsPayload(rows), [
    { first_name: 'Dale', last_name: 'Carnegie' },
    { first_name: 'Jane', last_name: 'Doe' },
  ])
})

test('magazine: empty rows become zero authors', () => {
  assert.deepEqual(authorsPayload([emptyAuthorRow()]), [])
  assert.equal(hasIncompleteAuthorRows([emptyAuthorRow()]), false)
})

test('mononym: last name is a single space', () => {
  const rows = [{ first_name: 'Cher', last_name: ' ', middle_name: '' }]
  assert.deepEqual(authorsPayload(rows), [{ first_name: 'Cher', last_name: ' ' }])
  assert.equal(hasIncompleteAuthorRows(rows), false)
})

test('incomplete kept row is blocked', () => {
  assert.equal(
    isAuthorRowIncomplete({ first_name: 'Dale', last_name: '', middle_name: '' }),
    true
  )
  assert.equal(hasIncompleteAuthorRows([{ first_name: 'Dale', last_name: '', middle_name: '' }]), true)
})

test('edit hydrate uses authors[] name parts, not the derived short form', () => {
  const stored = [
    { first_name: 'Dale', last_name: 'Carnegie', middle_name: null },
    { first_name: 'Jane', last_name: 'Doe', middle_name: null },
  ]
  const rows = hydrateAuthorRows(stored)
  assert.equal(rows[0].first_name, 'Dale')
  assert.equal(rows[0].last_name, 'Carnegie')
  assert.equal(rows[1].first_name, 'Jane')
  assert.notEqual(rows.map((r) => `${r.first_name} ${r.last_name}`).join(', '), 'D. Carnegie, J. Doe')
})

test('remove author: remaining row is the only payload', () => {
  const afterRemove = [{ first_name: 'Jane', last_name: 'Doe', middle_name: '' }]
  assert.deepEqual(authorsPayload(afterRemove), [{ first_name: 'Jane', last_name: 'Doe' }])
})

test('hydrate skips null entries and keeps mononym space', () => {
  const rows = hydrateAuthorRows([null, { first_name: 'Cher', last_name: ' ', middle_name: null }])
  assert.equal(rows.length, 1)
  assert.equal(rows[0].last_name, ' ')
  assert.ok(rows[0]._key)
})

test('null row is empty not incomplete', () => {
  assert.equal(isAuthorRowEmpty(null), true)
  assert.equal(hasIncompleteAuthorRows([null]), false)
})

test('whitespace-only last with blank first is dropped', () => {
  assert.equal(isAuthorRowEmpty({ first_name: '', last_name: '   ', middle_name: '' }), true)
  assert.deepEqual(authorsPayload([{ first_name: '', last_name: '   ', middle_name: '' }]), [])
})
