<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="650">
    <v-card v-if="book">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title class="text-subtitle-1 font-weight-bold">
          {{ isEditing ? 'Edit Book' : 'Book Details' }}
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="$emit('update:modelValue', false)"></v-btn>
      </v-toolbar>

      <v-card-text class="pt-4">
        <v-form v-if="isEditing" ref="editFormRef" v-model="isEditValid">
          <v-row density="compact">
            <v-col cols="12">
              <v-text-field
                v-model="editForm.title"
                label="Book Title *"
                :rules="[v => !!v || 'Title is required']"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12">
              <AuthorRows v-model="editForm.authors" />
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="editForm.publication_year"
                label="Publication Year"
                type="number"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="editForm.page_count"
                label="Page Count"
                type="number"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model="editForm.isbn"
                label="ISBN"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-combobox
                v-model="editForm.location_room"
                label="Room"
                :items="roomOptions"
                :custom-filter="locationFilter"
                variant="outlined"
                density="comfortable"
                clearable
              ></v-combobox>
            </v-col>
            <v-col cols="12" sm="4">
              <v-combobox
                v-model="editForm.location_unit"
                label="Unit"
                :items="unitOptions"
                :custom-filter="locationFilter"
                variant="outlined"
                density="comfortable"
                clearable
              ></v-combobox>
            </v-col>
            <v-col cols="12" sm="4">
              <v-combobox
                v-model="editForm.location_shelf"
                label="Shelf"
                :items="shelfOptions"
                :custom-filter="locationFilter"
                variant="outlined"
                density="comfortable"
                clearable
              ></v-combobox>
            </v-col>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="editForm.genres_tags"
                label="Genres / Tags"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="4">
              <v-select
                v-model="editForm.formats"
                label="Format"
                :items="formatItems"
                variant="outlined"
                density="comfortable"
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model="editForm.cover_url"
                label="Cover Image URL"
                variant="outlined"
                density="comfortable"
                clearable
              ></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="editForm.summary"
                label="Summary / Notes"
                rows="2"
                variant="outlined"
                density="comfortable"
              ></v-textarea>
            </v-col>
          </v-row>
        </v-form>

        <v-row v-else>
          <v-col cols="12" sm="4" class="d-flex justify-center">
            <v-img
              :src="book.cover_url || 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&auto=format&fit=crop&q=60'"
              max-height="220"
              max-width="160"
              cover
              class="rounded elevation-2"
            >
              <template #placeholder>
                <div class="d-flex align-center justify-center fill-height bg-grey-lighten-3">
                  <v-icon icon="mdi-book" size="large" color="grey"></v-icon>
                </div>
              </template>
            </v-img>
          </v-col>

          <v-col cols="12" sm="8">
            <div class="text-h6 font-weight-bold">{{ book.title }}</div>
            <div class="text-subtitle-1 text-grey-darken-2">{{ book.author }}</div>

            <div class="d-flex flex-wrap ga-1 my-2">
              <v-chip size="small" color="primary" variant="tonal" prepend-icon="mdi-map-marker">
                {{ [book.location_room, book.location_unit, book.location_shelf].filter(Boolean).join(' / ') || 'Unassigned Shelf' }}
              </v-chip>
              <v-chip size="small" color="secondary" variant="outlined">
                {{ book.formats || 'physical' }}
              </v-chip>
              <v-chip v-if="book.publication_year" size="small" variant="text">
                {{ book.publication_year }}
              </v-chip>
              <v-chip v-if="book.page_count" size="small" variant="text">
                {{ book.page_count }} pages
              </v-chip>
            </div>

            <div v-if="book.genres_tags" class="text-caption text-grey-darken-1 mb-1">
              <strong>Genres:</strong> {{ book.genres_tags }}
            </div>
            <div v-if="book.isbn" class="text-caption text-grey-darken-1 mb-1">
              <strong>ISBN:</strong> {{ book.isbn }}
            </div>
            <div class="text-caption text-grey-darken-1 mb-1">
              <strong>Total Times Read:</strong> {{ book.read_count }} time(s)
            </div>
          </v-col>
        </v-row>

        <template v-if="!isEditing">
          <v-divider class="my-3"></v-divider>

          <div v-if="book.summary" class="mb-3">
            <div class="text-subtitle-2 font-weight-bold mb-1">Summary / Notes</div>
            <p class="text-body-2 text-grey-darken-3">{{ book.summary }}</p>
          </div>

          <!-- Active and Past Readers for this Book -->
          <div v-if="bookSessions.length > 0" class="mb-3">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon icon="mdi-history" size="small" class="mr-1"></v-icon>
              Family Reading Log
            </div>
            <v-list density="compact" class="bg-grey-lighten-5 rounded pa-1">
              <v-list-item v-for="sess in bookSessions" :key="sess.id" class="py-1">
                <template #prepend>
                  <v-avatar size="28" color="primary" class="mr-2">
                    <v-icon :icon="sess.reader.avatar_icon || 'mdi-account'" size="small" color="white"></v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="text-caption font-weight-bold">
                  {{ sess.reader.name }} &bull;
                  <span v-if="sess.status === 'reading'" class="text-primary">Currently Reading (Page {{ sess.current_page }}/{{ book.page_count || '?' }})</span>
                  <span v-else-if="sess.status === 'finished'" class="text-success">Finished on {{ sess.finish_date || 'completed' }}</span>
                  <span v-else class="text-grey">{{ sess.status }}</span>
                </v-list-item-title>
                <v-list-item-subtitle v-if="sess.rating || sess.notes" class="text-caption">
                  <span v-if="sess.rating" class="text-amber-darken-3">{{ '★'.repeat(sess.rating) }} </span>
                  <span v-if="sess.notes" class="font-italic text-grey-darken-2">"{{ sess.notes }}"</span>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>

          <!-- Start Reading Section -->
          <v-card variant="outlined" class="pa-3 bg-grey-lighten-5">
            <div class="text-subtitle-2 font-weight-bold mb-2">
              <v-icon icon="mdi-account-clock-outline" size="small" class="mr-1"></v-icon>
              Start Reading This Book
            </div>
            <v-row density="compact" align="center">
              <v-col cols="12" sm="7">
                <v-select
                  v-model="selectedReaderId"
                  :items="readers"
                  item-title="name"
                  item-value="id"
                  label="Select Family Member"
                  density="compact"
                  variant="outlined"
                  hide-details
                ></v-select>
              </v-col>
              <v-col cols="12" sm="5">
                <v-btn
                  block
                  color="primary"
                  variant="flat"
                  prepend-icon="mdi-book-open-page-variant"
                  :disabled="!selectedReaderId || selectedReaderAlreadyReading"
                  :loading="isStarting"
                  @click="startReading"
                >
                  {{ selectedReaderAlreadyReading ? 'Already Reading' : 'Start Reading' }}
                </v-btn>
              </v-col>
            </v-row>
          </v-card>
        </template>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-3 justify-space-between">
        <v-btn v-if="!isEditing" color="error" variant="text" prepend-icon="mdi-delete-outline" @click="showDeleteConfirm = true">
          Delete
        </v-btn>
        <v-btn v-else variant="plain" @click="cancelEdit">
          Cancel
        </v-btn>
        <div>
          <v-btn v-if="!isEditing" color="primary" variant="tonal" prepend-icon="mdi-pencil" class="mr-2" @click="startEdit">
            Edit
          </v-btn>
          <v-btn v-if="isEditing" color="primary" variant="flat" :loading="isSaving" :disabled="isSaving || !editForm.title || hasIncompleteAuthors" @click="saveEdit">
            Save Changes
          </v-btn>
          <v-btn v-else color="primary" variant="tonal" @click="$emit('update:modelValue', false)">
            Close
          </v-btn>
        </div>
      </v-card-actions>
    </v-card>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-dialog>

  <v-dialog v-model="showDeleteConfirm" max-width="420" persistent>
    <v-card>
      <v-card-title class="text-subtitle-1 font-weight-bold">Delete this book?</v-card-title>
      <v-card-text>
        Are you sure you want to delete "{{ book?.title }}"? This cannot be undone.
      </v-card-text>
      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="plain" @click="showDeleteConfirm = false">Cancel</v-btn>
        <v-btn color="error" variant="flat" :loading="isDeleting" @click="confirmDelete">Delete</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import api from '../services/api'
import AuthorRows from './AuthorRows.vue'
import { authorsPayload, emptyAuthorRow, hasIncompleteAuthorRows, hydrateAuthorRows } from '../utils/authors'

const props = defineProps({
  modelValue: Boolean,
  book: Object,
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const readers = ref([])
const locations = ref([])
const bookSessions = ref([])
const selectedReaderId = ref(null)
const isStarting = ref(false)
const isEditing = ref(false)
const isSaving = ref(false)
const isDeleting = ref(false)
const isEditValid = ref(false)
const showDeleteConfirm = ref(false)
const editFormRef = ref(null)
const snackbar = ref({ show: false, text: '', color: 'error' })

const STANDARD_FORMATS = ['physical', 'kindle', 'epub', 'pdf']
const editForm = reactive(emptyEditForm())

const formatItems = computed(() => {
  const current = editForm.formats
  if (current && !STANDARD_FORMATS.includes(current)) {
    return [...STANDARD_FORMATS, current]
  }
  return STANDARD_FORMATS
})

function locationFilter(value, query) {
  if (!query || !String(query).trim()) return true
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .includes(String(query).trim().toLowerCase())
}

function uniqueNormalized(values) {
  const seen = new Set()
  const items = []
  for (const raw of values) {
    const value = raw == null ? '' : String(raw)
    const key = value.trim().toLowerCase()
    if (seen.has(key)) continue
    seen.add(key)
    items.push(value)
  }
  return items
}

const roomOptions = computed(() => {
  return uniqueNormalized(locations.value.map((loc) => loc.room).filter((room) => (room || '').trim()))
})

const unitOptions = computed(() => {
  const room = (editForm.location_room || '').trim().toLowerCase()
  if (!room) return []
  return uniqueNormalized(
    locations.value
      .filter((loc) => (loc.room || '').trim().toLowerCase() === room)
      .map((loc) => loc.unit ?? '')
  )
})

const shelfOptions = computed(() => {
  const room = (editForm.location_room || '').trim().toLowerCase()
  const unit = (editForm.location_unit || '').trim().toLowerCase()
  if (!room) return []
  return uniqueNormalized(
    locations.value
      .filter((loc) => {
        const sameRoom = (loc.room || '').trim().toLowerCase() === room
        const sameUnit = (loc.unit || '').trim().toLowerCase() === unit
        return sameRoom && sameUnit
      })
      .map((loc) => loc.shelf ?? '')
  )
})

async function loadLocationOptions() {
  try {
    const res = await api.getLocations()
    locations.value = res.data || []
  } catch {
    locations.value = []
  }
}

const selectedReaderAlreadyReading = computed(() => {
  if (!selectedReaderId.value) return false
  return bookSessions.value.some(
    (sess) => sess.reader_id === selectedReaderId.value && sess.status === 'reading'
  )
})

const hasIncompleteAuthors = computed(() => hasIncompleteAuthorRows(editForm.authors))

function emptyEditForm() {
  return {
    title: '',
    authors: [emptyAuthorRow()],
    publication_year: null,
    page_count: null,
    isbn: '',
    location_room: '',
    location_unit: '',
    location_shelf: '',
    genres_tags: '',
    formats: 'physical',
    cover_url: '',
    summary: '',
  }
}

function notify(text, color = 'error') {
  snackbar.value = { show: true, text, color }
}

function errorMessage(err, fallback) {
  const detail = err?.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}

function startEdit() {
  if (!props.book) return
  Object.assign(editForm, emptyEditForm(), {
    title: props.book.title || '',
    authors: hydrateAuthorRows(props.book.authors),
    publication_year: props.book.publication_year ?? null,
    page_count: props.book.page_count ?? null,
    isbn: props.book.isbn || '',
    location_room: props.book.location_room || '',
    location_unit: props.book.location_unit || '',
    location_shelf: props.book.location_shelf || '',
    genres_tags: props.book.genres_tags || '',
    formats: props.book.formats || 'physical',
    cover_url: props.book.cover_url || '',
    summary: props.book.summary || '',
  })
  isEditing.value = true
}

function cancelEdit() {
  isEditing.value = false
}

function updatePayload() {
  const { authors, ...rest } = editForm
  const payload = { ...rest, authors: authorsPayload(authors) }
  const textFields = [
    'isbn',
    'location_room',
    'location_unit',
    'location_shelf',
    'cover_url',
    'summary',
    'genres_tags',
  ]
  for (const key of textFields) {
    if (payload[key] === '') payload[key] = null
  }
  for (const key of ['publication_year', 'page_count']) {
    const value = payload[key]
    if (value === '' || value === null || Number.isNaN(value)) payload[key] = null
  }
  return payload
}

async function saveEdit() {
  if (!props.book || isSaving.value) return
  if (!editForm.title) {
    notify('Title is required')
    return
  }
  if (hasIncompleteAuthors.value) {
    notify('Each author needs a first and last name. Use a single space as the last name for a one-word name.')
    return
  }
  if (editFormRef.value) {
    const result = await editFormRef.value.validate()
    const valid = result === true || result?.valid === true
    if (!valid) {
      notify('Please fix the highlighted fields.')
      return
    }
  }
  isSaving.value = true
  try {
    const res = await api.updateBook(props.book.id, updatePayload())
    isEditing.value = false
    await loadLocationOptions()
    emit('refresh', res.data)
  } catch (err) {
    notify(errorMessage(err, 'Failed to update book'))
  } finally {
    isSaving.value = false
  }
}

async function loadData() {
  if (!props.book) return
  const bookId = props.book.id
  try {
    const readersRes = await api.getReaders()
    if (props.book?.id !== bookId) return
    readers.value = readersRes.data
    if (!readers.value.some((reader) => reader.id === selectedReaderId.value)) {
      selectedReaderId.value = readers.value[0]?.id ?? null
    }
  } catch (err) {
    readers.value = []
    notify(errorMessage(err, 'Failed to load family readers'))
  }
  try {
    const sessRes = await api.getBookSessions(bookId)
    if (props.book?.id !== bookId) return
    bookSessions.value = sessRes.data
  } catch (err) {
    if (props.book?.id !== bookId) return
    bookSessions.value = []
    notify(errorMessage(err, 'Failed to load reading history'))
  }
}

watch(
  () => [props.modelValue, props.book?.id],
  ([val, bookId]) => {
    if (val && bookId) {
      isEditing.value = false
      showDeleteConfirm.value = false
      loadLocationOptions()
      loadData()
    } else if (val) {
      loadLocationOptions()
    }
  },
  { immediate: true }
)

async function startReading() {
  if (!selectedReaderId.value || !props.book) return
  if (selectedReaderAlreadyReading.value) {
    notify('This family member is already reading this book', 'warning')
    return
  }
  isStarting.value = true
  try {
    await api.createSession({
      book_id: props.book.id,
      reader_id: selectedReaderId.value,
      status: 'reading',
      current_page: 0,
    })
    emit('refresh')
    await loadData()
  } catch (err) {
    notify(errorMessage(err, 'Failed to start reading session'))
  } finally {
    isStarting.value = false
  }
}

async function confirmDelete() {
  if (!props.book) return
  isDeleting.value = true
  try {
    await api.deleteBook(props.book.id)
    showDeleteConfirm.value = false
    emit('refresh')
    emit('update:modelValue', false)
  } catch (err) {
    notify(errorMessage(err, 'Failed to delete book'))
  } finally {
    isDeleting.value = false
  }
}
</script>
