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
        <v-window-item value="manual">
          <v-card-text class="pt-4">
            <v-form ref="formRef" v-model="isFormValid">
              <v-row density="compact">
                <v-col cols="12" sm="8">
                  <v-text-field
                    v-model="form.title"
                    label="Book Title *"
                    :rules="[v => !!v || 'Title is required']"
                    variant="outlined"
                    density="comfortable"
                    required
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="form.author"
                    label="Author *"
                    :rules="[v => !!v || 'Author is required']"
                    variant="outlined"
                    density="comfortable"
                    required
                  ></v-text-field>
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
                  <v-text-field
                    v-model="form.location_room"
                    label="Room (e.g. Living Room)"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="form.location_unit"
                    label="Unit (e.g. Main Shelf)"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="form.location_shelf"
                    label="Shelf (e.g. Top Shelf)"
                    variant="outlined"
                    density="comfortable"
                  ></v-text-field>
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
                    :items="['physical', 'pdf', 'epub', 'audiobook']"
                    variant="outlined"
                    density="comfortable"
                  ></v-select>
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

      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="plain" @click="close">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="isSaving"
          :disabled="!form.title || !form.author"
          @click="submit"
        >
          Save to Library
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import api from '../services/api'

defineProps({
  modelValue: Boolean,
})

const emit = defineEmits(['update:modelValue', 'saved'])

const tab = ref('manual')
const isFormValid = ref(false)
const formRef = ref(null)
const isSaving = ref(false)
const isLookingUp = ref(false)
const isbnInput = ref('')
const lookupError = ref('')

const defaultForm = () => ({
  title: '',
  author: '',
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
})

const form = reactive(defaultForm())

async function handleLookupISBN() {
  if (!isbnInput.value) return
  isLookingUp.value = true
  lookupError.value = ''

  try {
    const res = await api.lookupISBN(isbnInput.value)
    if (res.data) {
      const data = res.data
      form.title = data.title || form.title
      form.author = data.author || form.author
      form.publication_year = data.publication_year || form.publication_year
      form.page_count = data.page_count || form.page_count
      form.isbn = data.isbn || isbnInput.value
      form.genres_tags = data.genres_tags || form.genres_tags
      form.cover_url = data.cover_url || form.cover_url
      form.summary = data.summary || form.summary

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

async function submit() {
  if (!form.title || !form.author) return
  isSaving.value = true

  try {
    const payload = { ...form }
    await api.createBook(payload)
    emit('saved')
    close()
  } catch (err) {
    console.error('Failed to create book', err)
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('update:modelValue', false)
  Object.assign(form, defaultForm())
  isbnInput.value = ''
  lookupError.value = ''
  tab.value = 'manual'
}
</script>
