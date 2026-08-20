<template>
  <v-card variant="outlined" class="pa-3 my-2">
    <v-card-title class="d-flex align-center px-1 py-1">
      <v-icon icon="mdi-bookshelf" color="primary" class="mr-2"></v-icon>
      <span class="text-subtitle-1 font-weight-bold">Shelf & Physical Location Map</span>
      <v-spacer></v-spacer>
      <v-btn
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-plus"
        @click="openCreate"
      >
        Add Shelf
      </v-btn>
    </v-card-title>

    <v-divider class="my-2"></v-divider>

    <div v-if="loading" class="text-center py-4">
      <v-progress-circular indeterminate color="primary" size="28"></v-progress-circular>
    </div>

    <div v-else-if="Object.keys(locationData).length === 0" class="text-center py-4 text-grey">
      <div class="text-caption">No physical location data found.</div>
    </div>

    <v-row v-else dense>
      <v-col
        v-for="(shelves, room) in locationData"
        :key="room"
        cols="12"
        sm="6"
        md="4"
      >
        <v-card variant="tonal" color="primary" class="pa-2 h-100">
          <v-card-title class="text-subtitle-2 font-weight-bold d-flex align-center">
            <v-icon icon="mdi-home-outline" size="small" class="mr-1"></v-icon>
            {{ roomTitle(room) }}
          </v-card-title>

          <v-card-text class="pa-1">
            <v-chip-group column>
              <v-chip
                v-for="s in shelves"
                :key="s.shelf_key"
                size="small"
                variant="outlined"
                color="primary"
                @click="$emit('filter-room', room)"
              >
                {{ chipLabel(s) }} ({{ s.book_count }} books)
              </v-chip>
            </v-chip-group>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-card>

  <v-dialog v-model="showCreate" max-width="480">
    <v-card>
      <v-card-title class="text-subtitle-1 font-weight-bold">Add Shelf</v-card-title>
      <v-card-text>
        <v-alert
          v-if="createError"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-3"
          :text="createError"
        ></v-alert>
        <v-text-field
          v-model="createForm.room"
          label="Room *"
          variant="outlined"
          density="comfortable"
        ></v-text-field>
        <v-text-field
          v-model="createForm.unit"
          label="Unit"
          variant="outlined"
          density="comfortable"
        ></v-text-field>
        <v-text-field
          v-model="createForm.shelf"
          label="Shelf"
          variant="outlined"
          density="comfortable"
        ></v-text-field>
      </v-card-text>
      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="plain" @click="showCreate = false">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="isCreating"
          :disabled="isCreating || !(createForm.room || '').trim()"
          @click="submitCreate"
        >
          Save Shelf
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

defineEmits(['filter-room'])

const loading = ref(false)
const locationData = ref({})
const showCreate = ref(false)
const isCreating = ref(false)
const createError = ref('')
const createForm = ref(emptyCreateForm())

function emptyCreateForm() {
  return { room: '', unit: '', shelf: '' }
}

function roomTitle(room) {
  if (room === '__occupancy_unassigned__') return 'Unassigned'
  return room
}

function chipLabel(s) {
  if (s.label) return s.label
  const unit = (s.unit || '').trim()
  const shelf = (s.shelf || '').trim()
  if (unit && shelf) return `${unit} / ${shelf}`
  if (unit) return unit
  if (shelf) return shelf
  return 'Room'
}

function openCreate() {
  createForm.value = emptyCreateForm()
  createError.value = ''
  showCreate.value = true
}

async function submitCreate() {
  const room = (createForm.value.room || '').trim()
  if (!room || isCreating.value) return
  isCreating.value = true
  createError.value = ''
  try {
    await api.createLocation({
      room,
      unit: (createForm.value.unit || '').trim(),
      shelf: (createForm.value.shelf || '').trim(),
    })
    showCreate.value = false
    await loadLocations()
  } catch (err) {
    const detail = err?.response?.data?.detail
    if (typeof detail === 'string') {
      createError.value = detail
    } else if (Array.isArray(detail) && detail[0]?.msg) {
      createError.value = detail[0].msg
    } else {
      createError.value = 'Failed to create shelf.'
    }
  } finally {
    isCreating.value = false
  }
}

async function loadLocations() {
  loading.value = true
  try {
    const res = await api.getLocationsSummary()
    locationData.value = res.data.locations || {}
  } catch (err) {
    console.error('Failed to load locations', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLocations()
})

defineExpose({ loadLocations })
</script>
