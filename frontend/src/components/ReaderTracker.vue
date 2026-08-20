<template>
  <v-card variant="outlined" class="pa-3 my-2">
    <v-card-title class="d-flex justify-space-between align-center px-1 py-1">
      <div class="d-flex align-center">
        <v-icon icon="mdi-account-group" color="primary" class="mr-2"></v-icon>
        <span class="text-subtitle-1 font-weight-bold">Family Reading Tracker</span>
      </div>
      <v-btn
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-account-plus"
        @click="showAddReader = true"
      >
        Add Reader
      </v-btn>
    </v-card-title>

    <v-divider class="my-2"></v-divider>

    <!-- Active Sessions -->
    <div v-if="loading" class="text-center py-4">
      <v-progress-circular indeterminate color="primary" size="28"></v-progress-circular>
    </div>

    <div v-else-if="activeReadingList.length === 0" class="text-center py-4 text-grey">
      <v-icon icon="mdi-book-open-blank-variant" size="large" class="mb-1"></v-icon>
      <div class="text-caption">No one is currently reading a book. Pick one from the catalog!</div>
    </div>

    <v-list v-else lines="two" class="pa-0">
      <v-list-item
        v-for="item in activeReadingList"
        :key="item.id"
        class="px-2 py-1 mb-2 rounded bg-grey-lighten-5"
      >
        <template #prepend>
          <v-avatar color="primary" size="36">
            <v-icon :icon="item.reader.avatar_icon || 'mdi-account'" color="white"></v-icon>
          </v-avatar>
        </template>

        <v-list-item-title class="font-weight-bold text-subtitle-2">
          {{ item.reader.name }} &bull; <span class="text-grey-darken-2">{{ item.book.title }}</span>
        </v-list-item-title>

        <v-list-item-subtitle class="mt-1">
          <div class="d-flex align-center ga-2 mb-1">
            <span class="text-caption">Page {{ item.current_page }} of {{ item.book.page_count || '?' }}</span>
            <v-progress-linear
              :model-value="item.book.page_count ? (item.current_page / item.book.page_count) * 100 : 50"
              color="primary"
              height="6"
              rounded
              class="flex-grow-1"
            ></v-progress-linear>
          </div>
        </v-list-item-subtitle>

        <template #append>
          <div class="d-flex ga-1">
            <v-btn
              size="x-small"
              variant="outlined"
              color="primary"
              @click="promptUpdatePage(item)"
            >
              Update Page
            </v-btn>
            <v-btn
              size="x-small"
              variant="flat"
              color="success"
              @click="finishSession(item)"
            >
              Finish!
            </v-btn>
          </div>
        </template>
      </v-list-item>
    </v-list>

    <!-- Dialog: Add Reader -->
    <v-dialog v-model="showAddReader" max-width="400">
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1">Add Family Member</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="showAddReader = false"></v-btn>
        </v-toolbar>
        <v-card-text class="pt-4">
          <v-text-field
            v-model="newReaderName"
            label="Name (e.g. Papa, Mum, Kid)"
            variant="outlined"
            density="comfortable"
            @keyup.enter="saveReader"
          ></v-text-field>
          <v-select
            v-model="newReaderAvatar"
            :items="['mdi-account', 'mdi-face-woman', 'mdi-face-man', 'mdi-star', 'mdi-heart', 'mdi-emoticon-happy']"
            label="Avatar Icon"
            variant="outlined"
            density="comfortable"
          >
            <template #item="{ props, item }">
              <v-list-item v-bind="props" :prepend-icon="item.value" :title="item.value"></v-list-item>
            </template>
          </v-select>
        </v-card-text>
        <v-card-actions class="pa-3">
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="showAddReader = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!newReaderName" @click="saveReader">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const emit = defineEmits(['refresh'])

const loading = ref(false)
const activeReadingList = ref([])
const showAddReader = ref(false)
const newReaderName = ref('')
const newReaderAvatar = ref('mdi-account')

async function loadData() {
  loading.value = true
  try {
    const readersRes = await api.getReaders()
    const readers = readersRes.data
    const sessions = []

    for (const reader of readers) {
      const sessRes = await api.getReaderSessions(reader.id, 'reading')
      for (const sess of sessRes.data) {
        try {
          const bookRes = await api.getBook(sess.book_id)
          sessions.push({
            ...sess,
            reader,
            book: bookRes.data,
          })
        } catch (e) {
          // ignore book load error
        }
      }
    }
    activeReadingList.value = sessions
  } catch (err) {
    console.error('Failed to load reader tracker data', err)
  } finally {
    loading.value = false
  }
}

async function saveReader() {
  if (!newReaderName.value) return
  try {
    await api.createReader({
      name: newReaderName.value,
      avatar_icon: newReaderAvatar.value,
    })
    newReaderName.value = ''
    showAddReader.value = false
    await loadData()
    emit('refresh')
  } catch (err) {
    console.error('Failed to save reader', err)
  }
}

async function promptUpdatePage(item) {
  const pageStr = prompt(`Enter current page number for ${item.reader.name}:`, item.current_page)
  if (pageStr !== null) {
    const page = parseInt(pageStr, 10)
    if (!isNaN(page)) {
      try {
        await api.updateSession(item.id, { current_page: page })
        await loadData()
        emit('refresh')
      } catch (err) {
        console.error('Failed to update page', err)
      }
    }
  }
}

async function finishSession(item) {
  if (confirm(`Congratulations! Mark "${item.book.title}" as finished for ${item.reader.name}?`)) {
    try {
      await api.updateSession(item.id, {
        status: 'finished',
        current_page: item.book.page_count || item.current_page,
      })
      await loadData()
      emit('refresh')
    } catch (err) {
      console.error('Failed to finish session', err)
    }
  }
}

onMounted(() => {
  loadData()
})

defineExpose({ loadData })
</script>
