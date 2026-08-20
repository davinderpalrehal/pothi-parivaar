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
            ></v-img>
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

            <div v-if="book.genres_tags" class="text-caption text-grey-darken-1 mb-2">
              <strong>Genres:</strong> {{ book.genres_tags }}
            </div>
            <div v-if="book.isbn" class="text-caption text-grey-darken-1 mb-2">
              <strong>ISBN:</strong> {{ book.isbn }}
            </div>
            <div class="text-caption text-grey-darken-1 mb-2">
              <strong>Read Count:</strong> {{ book.read_count }} time(s)
            </div>
          </v-col>
        </v-row>

        <v-divider class="my-3"></v-divider>

        <div v-if="book.summary" class="mb-4">
          <div class="text-subtitle-2 font-weight-bold mb-1">Summary / Notes</div>
          <p class="text-body-2 text-grey-darken-3">{{ book.summary }}</p>
        </div>

        <!-- Reader Assignment / Action -->
        <v-card variant="outlined" class="pa-3 bg-grey-lighten-5">
          <div class="text-subtitle-2 font-weight-bold mb-2">
            <v-icon icon="mdi-account-clock-outline" size="small" class="mr-1"></v-icon>
            Family Reader Action
          </div>
          <v-row density="compact" align="center">
            <v-col cols="12" sm="7">
              <v-select
                v-model="selectedReaderId"
                :items="readers"
                item-title="name"
                item-value="id"
                label="Select Reader"
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
                :disabled="!selectedReaderId"
                :loading="isStarting"
                @click="startReading"
              >
                Start Reading
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
  </v-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  modelValue: Boolean,
  book: Object,
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const readers = ref([])
const selectedReaderId = ref(null)
const isStarting = ref(false)

onMounted(async () => {
  try {
    const res = await api.getReaders()
    readers.value = res.data
    if (readers.value.length > 0) {
      selectedReaderId.value = readers.value[0].id
    }
  } catch (err) {
    console.error('Failed to load readers', err)
  }
})

async function startReading() {
  if (!selectedReaderId.value || !props.book) return
  isStarting.value = true
  try {
    await api.createSession({
      book_id: props.book.id,
      reader_id: selectedReaderId.value,
      status: 'reading',
      current_page: 0,
    })
    emit('refresh')
    emit('update:modelValue', false)
  } catch (err) {
    console.error('Failed to start reading session', err)
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
      console.error('Failed to delete book', err)
    }
  }
}
</script>
