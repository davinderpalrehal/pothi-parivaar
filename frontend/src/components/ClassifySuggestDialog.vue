<template>
  <v-dialog :model-value="modelValue" @update:model-value="handleModelValue" max-width="480" persistent>
    <v-card v-if="book">
      <v-toolbar color="primary" density="compact">
        <v-toolbar-title class="text-subtitle-1 font-weight-bold">
          <v-icon icon="mdi-bookshelf" class="mr-2"></v-icon>
          Classify "{{ book.title }}"
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-toolbar>

      <v-card-text class="pt-4">
        <div v-if="isLoading" class="text-center py-6">
          <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>

        <template v-else-if="needsAuthorChoice">
          <v-alert type="info" variant="tonal" density="compact" class="mb-3">
            This book has multiple authors. Pick the one the shelf key should be
            based on.
          </v-alert>
          <v-radio-group v-model="selectedAuthorId" hide-details>
            <v-radio
              v-for="author in authorChoices"
              :key="author.id"
              :value="author.id"
              :label="authorDisplayName(author)"
            ></v-radio>
          </v-radio-group>
        </template>

        <template v-else>
          <v-alert
            v-if="hasNoClassSignal"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-3"
            text="Nothing in this book's title or genres matched the classification table, so the LCC class below is only a fallback. Please set it yourself before confirming."
          ></v-alert>
          <v-alert
            v-else-if="alreadyClassified"
            type="info"
            variant="tonal"
            density="compact"
            class="mb-3"
            text="Suggested from the book's current title, genres, and authors. Confirm to replace the saved shelf key."
          ></v-alert>
          <v-alert
            v-else
            type="info"
            variant="tonal"
            density="compact"
            class="mb-3"
            text="Review the suggested shelf key, edit if needed, then confirm to save it."
          ></v-alert>
          <v-row density="compact">
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="editableLcc"
                label="LCC Class"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="editableCutter"
                label="Cutter Number"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
          </v-row>
        </template>

        <v-alert v-if="errorText" type="error" variant="tonal" density="compact" class="mt-2">
          {{ errorText }}
        </v-alert>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-3 justify-end">
        <v-btn variant="plain" @click="close">Cancel</v-btn>
        <v-btn
          v-if="needsAuthorChoice"
          color="primary"
          variant="flat"
          :disabled="!selectedAuthorId"
          :loading="isLoading"
          @click="fetchSuggestion(selectedAuthorId)"
        >
          Suggest
        </v-btn>
        <v-btn
          v-else
          color="primary"
          variant="flat"
          :disabled="!editableLcc.trim() || !editableCutter.trim()"
          :loading="isSaving"
          @click="confirm"
        >
          {{ alreadyClassified ? 'Replace shelf key' : 'Confirm' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import api from '../services/api'
import { hasNoClassSignal as classSourceHasNoSignal } from '../utils/classification'

const props = defineProps({
  modelValue: Boolean,
  book: Object,
})

const emit = defineEmits(['update:modelValue', 'refresh'])

const isLoading = ref(false)
const isSaving = ref(false)
const needsAuthorChoice = ref(false)
const authorChoices = ref([])
const selectedAuthorId = ref(null)
const editableLcc = ref('')
const editableCutter = ref('')
const errorText = ref('')
// Set by a completed suggest fetch (never copied from stored LCC/Cutter).
const classSource = ref('')

const hasNoClassSignal = computed(() => classSourceHasNoSignal(classSource.value))
const alreadyClassified = computed(
  () => !!(props.book?.lcc_call_number && props.book?.cutter_number)
)

function authorDisplayName(author) {
  return [author.first_name, author.middle_name, author.last_name]
    .filter((part) => part && part.trim())
    .join(' ')
}

function errorMessage(err, fallback) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object' && typeof detail.message === 'string') return detail.message
  return fallback
}

function resetState() {
  isLoading.value = false
  isSaving.value = false
  needsAuthorChoice.value = false
  authorChoices.value = []
  selectedAuthorId.value = null
  editableLcc.value = ''
  editableCutter.value = ''
  errorText.value = ''
  classSource.value = ''
}

async function fetchSuggestion(primaryAuthorId = null) {
  if (!props.book) return
  isLoading.value = true
  errorText.value = ''
  // Cleared up front: a re-fetch that fails (e.g. the 422 author re-pick)
  // must not leave the previous fetch's warning standing next to the error.
  classSource.value = ''
  try {
    const res = await api.suggestClassification(props.book.id, primaryAuthorId)
    needsAuthorChoice.value = false
    editableLcc.value = res.data.lcc_call_number
    editableCutter.value = res.data.cutter_number
    classSource.value = res.data.class_source || ''
  } catch (err) {
    const detail = err?.response?.data?.detail
    if (err?.response?.status === 422 && detail?.authors) {
      needsAuthorChoice.value = true
      authorChoices.value = detail.authors
      selectedAuthorId.value = null
    } else {
      errorText.value = errorMessage(err, 'Failed to compute a classification suggestion')
    }
  } finally {
    isLoading.value = false
  }
}

async function confirm() {
  if (!props.book || isSaving.value) return
  isSaving.value = true
  errorText.value = ''
  try {
    const res = await api.updateBook(props.book.id, {
      lcc_call_number: editableLcc.value.trim(),
      cutter_number: editableCutter.value.trim(),
    })
    emit('refresh', res.data)
    emit('update:modelValue', false)
  } catch (err) {
    errorText.value = errorMessage(err, 'Failed to save the classification')
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('update:modelValue', false)
}

function handleModelValue(value) {
  emit('update:modelValue', value)
}

watch(
  () => [props.modelValue, props.book?.id],
  ([open]) => {
    if (!open) return
    resetState()
    fetchSuggestion()
  }
)
</script>
