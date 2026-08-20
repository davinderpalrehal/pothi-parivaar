<template>
  <v-card variant="outlined" class="pa-3 my-2">
    <v-card-title class="d-flex align-center px-1 py-1">
      <v-icon icon="mdi-bookshelf" color="primary" class="mr-2"></v-icon>
      <span class="text-subtitle-1 font-weight-bold">Shelf & Physical Location Map</span>
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
            {{ room }}
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
                {{ s.unit }} / {{ s.shelf }} ({{ s.book_count }} books)
              </v-chip>
            </v-chip-group>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

defineEmits(['filter-room'])

const loading = ref(false)
const locationData = ref({})

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
