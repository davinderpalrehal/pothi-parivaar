<template>
  <v-card
    hover
    class="mx-auto my-2 d-flex flex-column"
    max-width="320"
    height="100%"
    @click="$emit('select', book)"
  >
    <v-img
      :src="book.cover_url || defaultCover"
      height="180"
      cover
      class="bg-grey-lighten-2 align-end text-white"
    >
      <v-card-title class="text-subtitle-1 font-weight-bold text-truncate bg-black-subtle px-2 py-1">
        {{ book.title }}
      </v-card-title>
    </v-img>

    <v-card-subtitle class="pt-2 text-truncate font-weight-medium">
      {{ book.author }}
    </v-card-subtitle>

    <v-card-text class="flex-grow-1 py-1">
      <div class="d-flex flex-wrap ga-1 my-1">
        <v-chip
          v-if="locationDisplay"
          size="x-small"
          color="primary"
          variant="tonal"
          prepend-icon="mdi-bookshelf"
        >
          {{ locationDisplay }}
        </v-chip>
        <v-chip
          size="x-small"
          color="secondary"
          variant="outlined"
          prepend-icon="mdi-book-outline"
        >
          {{ book.formats || 'physical' }}
        </v-chip>
        <v-chip
          v-if="book.read_count > 0"
          size="x-small"
          color="success"
          variant="flat"
          prepend-icon="mdi-check-circle-outline"
        >
          Read {{ book.read_count }}x
        </v-chip>
      </div>

      <p v-if="book.summary" class="text-caption text-grey-darken-1 text-truncate-2 mt-1">
        {{ book.summary }}
      </p>
    </v-card-text>

    <v-divider></v-divider>

    <v-card-actions class="px-3 py-2 justify-space-between">
      <span class="text-caption text-grey">ID: #{{ book.id }}</span>
      <v-btn
        size="small"
        color="primary"
        variant="text"
        append-icon="mdi-chevron-right"
      >
        Details
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  book: {
    type: Object,
    required: true,
  },
})

defineEmits(['select'])

const defaultCover = 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=400&auto=format&fit=crop&q=60'

const locationDisplay = computed(() => {
  const parts = [props.book.location_room, props.book.location_unit, props.book.location_shelf].filter(Boolean)
  return parts.length > 0 ? parts.join(' / ') : null
})
</script>

<style scoped>
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.bg-black-subtle {
  background: rgba(0, 0, 0, 0.65);
}
</style>
