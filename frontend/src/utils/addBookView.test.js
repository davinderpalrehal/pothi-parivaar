import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  ADD_BOOK_VIEW,
  SHELL_VIEWS,
  shellNavValue,
  viewAfterAddBookCancel,
  viewAfterAddBookPersist,
} from './addBookView.js'

const frontendSrc = join(dirname(fileURLToPath(import.meta.url)), '..')
const addBookVue = readFileSync(join(frontendSrc, 'components/AddBookDialog.vue'), 'utf8')
const appVue = readFileSync(join(frontendSrc, 'App.vue'), 'utf8')

test('open add: App.vue navigates to add-book, not a dialog v-model', () => {
  assert.match(appVue, /goToAddBook/)
  assert.match(appVue, /currentView === ADD_BOOK_VIEW/)
  assert.doesNotMatch(appVue, /showAddBook/)
  assert.doesNotMatch(addBookVue, /v-dialog/)
  assert.match(addBookVue, /<v-card/)
})

test('save to library: persist without addNext returns catalog', () => {
  assert.equal(viewAfterAddBookPersist({ addNext: false }), 'catalog')
  assert.match(addBookVue, /emit\('done'\)/)
  assert.match(appVue, /viewAfterAddBookPersist\(\{ addNext: false \}\)/)
})

test('save and add next: persist with addNext stays on add-book', () => {
  assert.equal(viewAfterAddBookPersist({ addNext: true }), ADD_BOOK_VIEW)
  assert.match(addBookVue, /async function submitAndAddNext/)
  assert.match(addBookVue, /if \(ok\) resetForm\(\)/)
  assert.doesNotMatch(
    addBookVue.slice(addBookVue.indexOf('async function submitAndAddNext')),
    /emit\('done'\)/
  )
})

test('leave mid-form: switching a shell view leaves add-book', () => {
  for (const view of SHELL_VIEWS) {
    assert.equal(shellNavValue(view), view)
  }
  assert.equal(viewAfterAddBookCancel(), 'catalog')
  assert.match(appVue, /viewAfterAddBookCancel\(\)/)
})

test('isbn lookup tab still exists on the page', () => {
  assert.match(addBookVue, /value="isbn"/)
  assert.match(addBookVue, /handleLookupISBN/)
  assert.match(addBookVue, /v-tab value="manual"/)
})

test('small viewport: add-book is a v-main page, not a sixth bottom-nav item', () => {
  assert.equal(shellNavValue(ADD_BOOK_VIEW), null)
  assert.doesNotMatch(appVue, /v-btn value="add-book"/)
  assert.match(appVue, /v-else-if="currentView === ADD_BOOK_VIEW"/)
  assert.match(appVue, /pb-16/)
  assert.match(addBookVue, /if \(isSaving\.value\) return/)
})
