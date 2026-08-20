<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="650">
    <v-card v-if="book">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title class="text-subtitle-1 font-weight-bold">
          Book Details
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="$emit('update:modelValue', false)"></v-btn>
      </v-toolbar>

      <v-card-text class="pt-4">
        <v-row>
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
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-3 justify-space-between">
        <v-btn color="error" variant="text" prepend-icon="mdi-delete-outline" @click="deleteBook">
          Delete
        </v-btn>
        <v-btn color="primary" variant="tonal" @click="$emit('update:modelValue', false)">
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  modelValue: Boolean,
  book: Object,
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const readers = ref([])
const bookSessions = ref([])
const selectedReaderId = ref(null)
const isStarting = ref(false)
const snackbar = ref({ show: false, text: '', color: 'error' })

const selectedReaderAlreadyReading = computed(() => {
  if (!selectedReaderId.value) return false
  return bookSessions.value.some(
    (sess) => sess.reader_id === selectedReaderId.value && sess.status === 'reading'
  )
})

function notify(text, color = 'error') {
  snackbar.value = { show: true, text, color }
}

function errorMessage(err, fallback) {
  const detail = err?.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
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
  () => [props.modelValue, props.book],
  ([val, book]) => {
    if (val && book) {
      loadData()
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

async function deleteBook() {
  if (!props.book) return
  if (confirm(`Are you sure you want to delete "${props.book.title}"?`)) {
    try {
      await api.deleteBook(props.book.id)
      emit('refresh')
      emit('update:modelValue', false)
    } catch (err) {
      notify(errorMessage(err, 'Failed to delete book'))
    }
  }
}
</script>
