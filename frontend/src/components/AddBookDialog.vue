<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="650" persistent>
    <v-card>
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title class="text-subtitle-1 font-weight-bold">
          <v-icon icon="mdi-book-plus" class="mr-2"></v-icon>
          Add Book to Library
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-toolbar>

      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="manual">
          <v-icon start icon="mdi-form-textbox"></v-icon>
          Manual Entry
        </v-tab>
        <v-tab value="isbn">
          <v-icon start icon="mdi-barcode-scan"></v-icon>
          ISBN Lookup
        </v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <!-- ISBN Tab -->
        <v-window-item value="isbn">
          <v-card-text class="pt-4">
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
              text="Enter a 10 or 13 digit ISBN to fetch book details from Open Library automatically."
            ></v-alert>

            <v-row density="compact">
              <v-col cols="12" sm="8">
                <v-text-field
                  v-model="isbnInput"
                  label="ISBN Code"
                  placeholder="e.g. 9780547928227"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-barcode"
                  clearable
                  @keyup.enter="handleLookupISBN"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="4">
                <v-btn
                  block
                  color="primary"
                  height="44"
                  :loading="isLookingUp"
                  @click="handleLookupISBN"
                >
                  Lookup
                </v-btn>
              </v-col>
            </v-row>

            <v-alert
              v-if="lookupError"
              type="warning"
              variant="tonal"
              density="compact"
              class="mt-2"
              :text="lookupError"
            ></v-alert>
          </v-card-text>
        </v-window-item>

        <!-- Manual Form Tab (Shared for submission) -->
        <v-window-item value="manual" eager>
          <v-card-text class="pt-4">
            <v-form ref="formRef" v-model="isFormValid">
              <v-row density="compact">
                <v-col cols="12">
                  <v-text-field
                    v-model="form.title"
                    label="Book Title *"
                    :rules="[v => !!v || 'Title is required']"
                    variant="outlined"
                    density="comfortable"
                    required
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <AuthorRows v-model="form.authors" />
                </v-col>

                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model.number="form.publication_year"
                    label="Publication Year"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model.number="form.page_count"
                    label="Page Count"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="form.isbn"
                    label="ISBN"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>

                <!-- Location Fields -->
                <v-col cols="12">
                  <div class="text-subtitle-2 font-weight-bold text-grey-darken-2 mb-1">
                    <v-icon icon="mdi-map-marker-radius" size="small" class="mr-1"></v-icon>
                    Physical Shelf Placement
                  </div>
                </v-col>

                <v-col cols="12" sm="4">
                  <v-combobox
                    v-model="form.location_room"
                    label="Room (e.g. Living Room)"
                    :items="roomOptions"
                    :custom-filter="locationFilter"
                    variant="outlined"
                    density="comfortable"
                    clearable
                  ></v-combobox>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-combobox
                    v-model="form.location_unit"
                    label="Unit (e.g. Main Shelf)"
                    :items="unitOptions"
                    :custom-filter="locationFilter"
                    variant="outlined"
                    density="comfortable"
                    clearable
                  ></v-combobox>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-combobox
                    v-model="form.location_shelf"
                    label="Shelf (e.g. Top Shelf)"
                    :items="shelfOptions"
                    :custom-filter="locationFilter"
                    variant="outlined"
                    density="comfortable"
                    clearable
                  ></v-combobox>
                </v-col>

                <!-- Metadata -->
                <v-col cols="12" sm="8">
                  <v-text-field
                    v-model="form.genres_tags"
                    label="Genres / Tags (comma separated)"
                    placeholder="e.g. Fiction, Punjabi, Children, History"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-select
                    v-model="form.formats"
                    label="Format"
                    :items="['physical', 'kindle', 'epub', 'pdf']"
                    variant="outlined"
                    density="comfortable"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-combobox
                    v-model="form.language"
                    label="Language"
                    :items="languageOptions"
                    :rules="[languageRule]"
                    item-title="label"
                    item-value="code"
                    placeholder="e.g. pan"
                    hint="ISO 639-3 code; pick one or type your own"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                    clearable
                  ></v-combobox>
                </v-col>
                <v-col cols="12" sm="8">
                  <v-text-field
                    v-model="form.additional_languages"
                    label="Additional Languages (comma separated)"
                    placeholder="e.g. san, hin"
                    hint="ISO 639-3 codes, separated by commas"
                    persistent-hint
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <v-text-field
                    v-model="form.cover_url"
                    label="Cover Image URL"
                    variant="outlined"
                    density="comfortable"
                    clearable
                  ></v-text-field>
                </v-col>

                <v-col cols="12">
                  <v-textarea
                    v-model="form.summary"
                    label="Summary / Notes"
                    rows="2"
                    variant="outlined"
                    density="comfortable"
                  ></v-textarea>
                </v-col>
              </v-row>
            </v-form>
          </v-card-text>
        </v-window-item>
      </v-window>

      <v-divider></v-divider>

      <v-alert
        v-if="submitError"
        type="error"
        variant="tonal"
        density="compact"
        class="mx-3 mt-3"
        :text="submitError"
      ></v-alert>

      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="plain" @click="close">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="tonal"
          :loading="isSaving"
          :disabled="isSaving || !form.title || hasIncompleteAuthors"
          @click="submitAndAddNext"
        >
          Save & Add Next
        </v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="isSaving"
          :disabled="isSaving || !form.title || hasIncompleteAuthors"
          @click="submit"
        >
          Save to Library
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import api from '../services/api'
import AuthorRows from './AuthorRows.vue'
import { authorsPayload, emptyAuthorRow, hasIncompleteAuthorRows } from '../utils/authors'
import { LANGUAGE_OPTIONS, languageRule, normalizeLanguage } from '../utils/languages'

const props = defineProps({
  modelValue: Boolean,
})

const emit = defineEmits(['update:modelValue', 'saved'])
const locations = ref([])

const tab = ref('manual')
const isFormValid = ref(false)
const formRef = ref(null)
const isSaving = ref(false)
const isLookingUp = ref(false)
const isbnInput = ref('')
const lookupError = ref('')
const submitError = ref('')

const defaultForm = () => ({
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
  language: null,
  additional_languages: '',
  cover_url: '',
  summary: '',
})

const form = reactive(defaultForm())
const languageOptions = LANGUAGE_OPTIONS

const hasIncompleteAuthors = computed(() => hasIncompleteAuthorRows(form.authors))

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
  const room = (form.location_room || '').trim().toLowerCase()
  if (!room) return []
  return uniqueNormalized(
    locations.value
      .filter((loc) => (loc.room || '').trim().toLowerCase() === room)
      .map((loc) => loc.unit ?? '')
  )
})

const shelfOptions = computed(() => {
  const room = (form.location_room || '').trim().toLowerCase()
  const unit = (form.location_unit || '').trim().toLowerCase()
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

watch(
  () => props.modelValue,
  (open) => {
    if (open) loadLocationOptions()
  },
  { immediate: true }
)

async function handleLookupISBN() {
  if (!isbnInput.value) return
  isLookingUp.value = true
  lookupError.value = ''

  try {
    const res = await api.lookupISBN(isbnInput.value)
    if (res.data) {
      const data = res.data
      form.title = data.title || form.title
      form.publication_year = data.publication_year || form.publication_year
      form.page_count = data.page_count || form.page_count
      form.isbn = data.isbn || isbnInput.value
      form.genres_tags = data.genres_tags || form.genres_tags
      form.cover_url = data.cover_url || form.cover_url
      form.summary = data.summary || form.summary
      form.formats = data.formats || form.formats

      // Switch to manual tab so user can review and select location
      tab.value = 'manual'
    }
  } catch (err) {
    lookupError.value = 'Book metadata could not be fetched for this ISBN. You can fill details manually.'
    form.isbn = isbnInput.value
    tab.value = 'manual'
  } finally {
    isLookingUp.value = false
  }
}

function createPayload() {
  const { authors, ...rest } = form
  const payload = { ...rest, authors: authorsPayload(authors) }
  const textFields = [
    'isbn',
    'location_room',
    'location_unit',
    'location_shelf',
    'genres_tags',
    'language',
    'additional_languages',
    'cover_url',
    'summary',
  ]
  for (const key of textFields) {
    if (payload[key] === '') payload[key] = null
  }
  for (const key of ['publication_year', 'page_count']) {
    const value = payload[key]
    if (value === '' || value === null || Number.isNaN(value)) payload[key] = null
  }
  payload.language = normalizeLanguage(payload.language)
  return payload
}

async function persistBook() {
  if (isSaving.value) return false
  tab.value = 'manual'
  submitError.value = ''

  if (!form.title) {
    submitError.value = 'Title is required.'
    return false
  }
  if (hasIncompleteAuthors.value) {
    submitError.value = 'Each author needs a first and last name. Use a single space as the last name for a one-word name.'
    return false
  }
  if (formRef.value) {
    const result = await formRef.value.validate()
    const valid = result === true || result?.valid === true
    if (!valid) {
      submitError.value = 'Please fix the highlighted fields.'
      return false
    }
  }

  isSaving.value = true
  try {
    await api.createBook(createPayload())
    await loadLocationOptions()
    emit('saved')
    return true
  } catch (err) {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string') {
      submitError.value = detail
    } else if (Array.isArray(detail) && detail[0]?.msg) {
      submitError.value = detail[0].msg
    } else {
      submitError.value = 'Failed to save book. You can keep editing and try again.'
    }
    return false
  } finally {
    isSaving.value = false
  }
}

async function submit() {
  const ok = await persistBook()
  if (ok) close()
}

async function submitAndAddNext() {
  const ok = await persistBook()
  if (ok) resetForm()
}

function resetForm() {
  Object.assign(form, defaultForm())
  isbnInput.value = ''
  lookupError.value = ''
  submitError.value = ''
  tab.value = 'manual'
  formRef.value?.resetValidation?.()
}

function close() {
  emit('update:modelValue', false)
  resetForm()
}
</script>
