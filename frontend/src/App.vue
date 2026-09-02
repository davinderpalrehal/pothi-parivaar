<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer v-model="drawer" temporary>
      <v-list-item
        prepend-icon="mdi-book-open-page-variant"
        title="Pothi Parivaar"
        subtitle="Family Home Library"
        class="py-4"
      ></v-list-item>
      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-bookshelf"
          title="Catalog & Search"
          :active="currentView === 'catalog'"
          @click="currentView = 'catalog'; drawer = false"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-account-group"
          title="Reading Tracker"
          :active="currentView === 'tracker'"
          @click="currentView = 'tracker'; drawer = false"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-map-marker-path"
          title="Shelf & Locations"
          :active="currentView === 'shelves'"
          @click="currentView = 'shelves'; drawer = false"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-account-tie"
          title="Honorifics"
          :active="currentView === 'honorifics'"
          @click="currentView = 'honorifics'; drawer = false"
        ></v-list-item>
        <v-list-item
          prepend-icon="mdi-robot"
          title="Hermes AI Assistant"
          :active="currentView === 'hermes'"
          @click="currentView = 'hermes'; drawer = false"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar color="primary" elevation="2">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title class="font-weight-bold">
        <v-icon icon="mdi-book-open-page-variant" class="mr-2"></v-icon>
        Pothi Parivaar
      </v-toolbar-title>

      <!-- Desktop View Switcher Tabs -->
      <v-tabs v-model="shellView" color="white" class="d-none d-md-flex">
        <v-tab value="catalog" prepend-icon="mdi-bookshelf">Catalog</v-tab>
        <v-tab value="tracker" prepend-icon="mdi-account-group">Reading Tracker</v-tab>
        <v-tab value="shelves" prepend-icon="mdi-map-marker-path">Shelves</v-tab>
        <v-tab value="honorifics" prepend-icon="mdi-account-tie">Honorifics</v-tab>
        <v-tab value="hermes" prepend-icon="mdi-robot">Hermes AI</v-tab>
      </v-tabs>

      <v-spacer></v-spacer>

      <v-btn
        prepend-icon="mdi-plus"
        variant="flat"
        color="white"
        class="text-primary font-weight-bold mr-2"
        @click="goToAddBook"
      >
        Add Book
      </v-btn>
    </v-app-bar>

    <!-- Main Content -->
    <v-main class="bg-grey-lighten-4">
      <v-container fluid class="pa-4">
        <!-- View: Catalog -->
        <div v-if="currentView === 'catalog'">
          <!-- Search & Filter Bar -->
          <v-card class="mb-4 pa-3" elevation="1">
            <v-row density="compact" align="center">
              <v-col cols="12" sm="10" md="11">
                <v-text-field
                  v-model="searchQuery"
                  label="Search by title, author, tag, or ISBN..."
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="2" md="1">
                <v-btn
                  block
                  color="primary"
                  variant="tonal"
                  height="44"
                  icon="mdi-refresh"
                  aria-label="Refresh catalog"
                  @click="fetchBooks"
                ></v-btn>
              </v-col>
            </v-row>
            <v-row density="compact" align="center" class="mt-1">
              <v-col cols="6" sm="4" md="2">
                <v-text-field
                  v-model="genreFilter"
                  label="Tag/Genre"
                  prepend-inner-icon="mdi-tag-outline"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-text-field>
              </v-col>
              <v-col cols="6" sm="4" md="2">
                <v-select
                  v-model="formatFilter"
                  label="Format"
                  :items="formatOptions"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-select>
              </v-col>
              <v-col cols="6" sm="4" md="2">
                <v-select
                  v-model="statusFilter"
                  label="Status"
                  :items="statusOptions"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-select>
              </v-col>
              <v-col cols="6" sm="4" md="2">
                <v-text-field
                  v-model="roomFilter"
                  label="Room"
                  prepend-inner-icon="mdi-map-marker-outline"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-text-field>
              </v-col>
              <v-col cols="6" sm="4" md="2">
                <v-select
                  v-model="languageFilter"
                  label="Language"
                  :items="languageOptions"
                  prepend-inner-icon="mdi-translate"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  @update:model-value="fetchBooks"
                ></v-select>
              </v-col>
            </v-row>
          </v-card>

          <!-- Books Grid -->
          <div v-if="loading" class="text-center py-12">
            <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
            <div class="text-subtitle-1 text-grey-darken-1 mt-3">Loading your library...</div>
          </div>

          <div v-else-if="books.length === 0" class="text-center py-12 bg-white rounded elevation-1">
            <v-icon icon="mdi-book-open-page-variant-outline" size="64" color="grey-lighten-1"></v-icon>
            <div class="text-h6 text-grey-darken-2 mt-2">No books found</div>
            <div class="text-body-2 text-grey mb-4">Add your first book manually or lookup via ISBN barcode!</div>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="goToAddBook">
              Add a Book
            </v-btn>
          </div>

          <v-row v-else dense>
            <v-col
              v-for="book in books"
              :key="book.id"
              cols="12"
              sm="6"
              md="4"
              lg="3"
            >
              <BookCard
                :book="book"
                :active-readers="activeReadersByBook[book.id] || []"
                @select="openBookDetail"
              />
            </v-col>
          </v-row>
        </div>

        <!-- View: Tracker -->
        <div v-else-if="currentView === 'tracker'">
          <ReaderTracker ref="trackerRef" @refresh="handleReadingUpdated" />
        </div>

        <!-- View: Shelves -->
        <div v-else-if="currentView === 'shelves'">
          <ShelfManager
            ref="shelvesRef"
            @filter-room="handleFilterRoom"
          />
        </div>

        <div v-else-if="currentView === 'honorifics'">
          <HonorificManager
            ref="honorificsRef"
            @changed="handleHonorificsChanged"
          />
        </div>

        <div v-else-if="currentView === ADD_BOOK_VIEW" class="pb-16 pb-md-4">
          <AddBookDialog
            @saved="handleBookSaved"
            @done="currentView = viewAfterAddBookPersist({ addNext: false })"
            @cancel="currentView = viewAfterAddBookCancel()"
          />
        </div>

        <!-- View: Hermes AI Assistant Overview -->
        <div v-else-if="currentView === 'hermes'">
          <v-card class="pa-4" elevation="1">
            <v-card-title class="d-flex align-center">
              <v-icon icon="mdi-robot" color="primary" class="mr-2"></v-icon>
              <span class="text-h6 font-weight-bold">Hermes AI Agent Local Status</span>
            </v-card-title>
            <v-divider class="my-2"></v-divider>

            <v-alert
              type="info"
              variant="tonal"
              density="comfortable"
              class="mb-4"
              text="Hermes interacts with Pothi Parivaar via localhost REST API at /api/v1/hermes/*. Use the standalone skill in hermes_skill/pothi_skill.py for your VPS bot."
            ></v-alert>

            <div v-if="hermesLoading" class="text-center py-6">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
            </div>

            <div v-else-if="hermesStatus">
              <v-row>
                <v-col cols="12" sm="4">
                  <v-card variant="tonal" color="primary" class="pa-3 text-center">
                    <div class="text-h4 font-weight-bold">{{ hermesStatus.total_catalog_books }}</div>
                    <div class="text-caption text-uppercase">Total Catalog Books</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card variant="tonal" color="success" class="pa-3 text-center">
                    <div class="text-h4 font-weight-bold">{{ hermesStatus.total_readers }}</div>
                    <div class="text-caption text-uppercase">Family Readers</div>
                  </v-card>
                </v-col>
                <v-col cols="12" sm="4">
                  <v-card variant="tonal" color="info" class="pa-3 text-center">
                    <div class="text-h4 font-weight-bold">{{ hermesStatus.active_reading_count }}</div>
                    <div class="text-caption text-uppercase">Active Reading Sessions</div>
                  </v-card>
                </v-col>
              </v-row>

              <div class="mt-4">
                <div class="text-subtitle-1 font-weight-bold mb-2">Active Reading Sessions (Live Hermes View)</div>
                <v-table density="compact" class="elevation-1">
                  <thead>
                    <tr>
                      <th>Reader</th>
                      <th>Book</th>
                      <th>Page</th>
                      <th>Location</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in hermesStatus.currently_reading" :key="idx">
                      <td class="font-weight-medium">{{ item.reader }}</td>
                      <td>{{ item.book_title }}</td>
                      <td>{{ item.current_page }} / {{ item.total_pages || '?' }}</td>
                      <td>{{ item.location }}</td>
                    </tr>
                    <tr v-if="hermesStatus.currently_reading.length === 0">
                      <td colspan="4" class="text-center text-grey py-3">No active sessions</td>
                    </tr>
                  </tbody>
                </v-table>
              </div>
            </div>
          </v-card>
        </div>
      </v-container>
    </v-main>

    <!-- Bottom Navigation on Mobile -->
    <v-bottom-navigation v-model="shellView" grow color="primary" class="d-flex d-md-none">
      <v-btn value="catalog">
        <v-icon>mdi-bookshelf</v-icon>
        <span>Catalog</span>
      </v-btn>
      <v-btn value="tracker">
        <v-icon>mdi-account-group</v-icon>
        <span>Tracker</span>
      </v-btn>
      <v-btn value="shelves">
        <v-icon>mdi-map-marker-path</v-icon>
        <span>Shelves</span>
      </v-btn>
      <v-btn value="honorifics">
        <v-icon>mdi-account-tie</v-icon>
        <span>Honorifics</span>
      </v-btn>
      <v-btn value="hermes">
        <v-icon>mdi-robot</v-icon>
        <span>Hermes</span>
      </v-btn>
    </v-bottom-navigation>

    <!-- Dialogs -->
    <BookDetailDialog
      v-model="showBookDetail"
      :book="selectedBook"
      @refresh="handleBookSaved"
    />
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import api from './services/api'
import { languageFilterOptions, languageFilterParams } from './utils/languages.js'
import BookCard from './components/BookCard.vue'
import AddBookDialog from './components/AddBookDialog.vue'
import BookDetailDialog from './components/BookDetailDialog.vue'
import ReaderTracker from './components/ReaderTracker.vue'
import ShelfManager from './components/ShelfManager.vue'
import HonorificManager from './components/HonorificManager.vue'
import {
  ADD_BOOK_VIEW,
  SHELL_VIEWS,
  shellNavValue,
  viewAfterAddBookCancel,
  viewAfterAddBookPersist,
} from './utils/addBookView.js'

const drawer = ref(false)
const currentView = ref('catalog')
const suppressShellNullSync = ref(false)

function goToAddBook() {
  currentView.value = ADD_BOOK_VIEW
  suppressShellNullSync.value = true
  nextTick(() => {
    setTimeout(() => {
      suppressShellNullSync.value = false
    }, 50)
  })
}

const shellView = computed({
  get: () => shellNavValue(currentView.value),
  set: (value) => {
    if (!value || !SHELL_VIEWS.includes(value)) return
    // Vuetify writes the first tab/nav item when the bound model is null.
    // Ignore that sync so opening Add Book does not bounce to catalog.
    if (currentView.value === ADD_BOOK_VIEW && suppressShellNullSync.value) return
    currentView.value = value
  },
})

const books = ref([])
const activeReadersByBook = ref({})
const loading = ref(false)
const searchQuery = ref('')
const genreFilter = ref('')
const formatFilter = ref(null)
const statusFilter = ref(null)
const roomFilter = ref('')
const languageFilter = ref(null)
// Derived from the catalog, not from the entry-form shortlist, so a free-entry
// code is still filterable and no empty language is ever offered.
const languageOptions = ref([])
const formatOptions = [
  { title: 'Physical', value: 'physical' },
  { title: 'Kindle', value: 'kindle' },
  { title: 'EPUB', value: 'epub' },
  { title: 'PDF', value: 'pdf' },
]
const statusOptions = [
  { title: 'Available', value: 'available' },
  { title: 'Reading', value: 'reading' },
  { title: 'Finished', value: 'finished' },
]

const showBookDetail = ref(false)
const selectedBook = ref(null)

const trackerRef = ref(null)
const shelvesRef = ref(null)
const honorificsRef = ref(null)

const hermesLoading = ref(false)
const hermesStatus = ref(null)

async function fetchBooks() {
  loading.value = true
  try {
    const params = {}
    if (searchQuery.value) params.q = searchQuery.value
    if (genreFilter.value) params.genre = genreFilter.value
    if (formatFilter.value) params.format = formatFilter.value
    const room = (roomFilter.value || '').trim()
    if (room) params.room = room
    if (statusFilter.value) params.status = statusFilter.value
    Object.assign(params, languageFilterParams(languageFilter.value))
    const booksRes = await api.getBooks(params)
    books.value = booksRes.data
    if (selectedBook.value) {
      const fresh = books.value.find((b) => b.id === selectedBook.value.id)
      if (fresh) selectedBook.value = fresh
    }
  } catch (err) {
    console.error('Failed to fetch books', err)
  } finally {
    loading.value = false
  }

  try {
    const activityRes = await api.getReaderActivity()
    activeReadersByBook.value = activityRes.data.reduce((byBook, activity) => {
      const readers = byBook[activity.book_id] || []
      readers.push(activity.reader.name)
      byBook[activity.book_id] = readers
      return byBook
    }, {})
  } catch (err) {
    activeReadersByBook.value = {}
    console.error('Failed to fetch reader activity', err)
  }
}

async function fetchHermesStatus() {
  hermesLoading.value = true
  try {
    const res = await api.getHermesStatus()
    hermesStatus.value = res.data
  } catch (err) {
    console.error('Failed to fetch Hermes status', err)
  } finally {
    hermesLoading.value = false
  }
}

watch(currentView, (newVal) => {
  if (newVal === 'catalog') fetchBooks()
  else if (newVal === 'tracker' && trackerRef.value) trackerRef.value.loadData()
  else if (newVal === 'shelves' && shelvesRef.value) shelvesRef.value.loadLocations()
  else if (newVal === 'honorifics' && honorificsRef.value) honorificsRef.value.loadHonorifics()
  else if (newVal === 'hermes') fetchHermesStatus()
})

function openBookDetail(book) {
  selectedBook.value = book
  showBookDetail.value = true
}

async function loadLanguageOptions() {
  try {
    const res = await api.getCatalogLanguages()
    languageOptions.value = languageFilterOptions(res.data)

    // A selection can outlive its option -- give the last unset book a language
    // and "No language set" disappears from the list. Drop the stale selection
    // instead of leaving the control showing a value it no longer offers while
    // filtering the grid to nothing.
    const stillOffered = languageOptions.value.some(
      (item) => item.value === languageFilter.value
    )
    if (languageFilter.value != null && !stillOffered) {
      languageFilter.value = null
      fetchBooks()
    }
  } catch (err) {
    console.error('Failed to fetch catalog languages', err)
  }
}

function handleBookSaved(updatedBook) {
  if (updatedBook?.id) {
    selectedBook.value = { ...(selectedBook.value || {}), ...updatedBook }
  }
  fetchBooks()
  // Editing a language changes the counts, so the dropdown is rebuilt here
  // rather than going stale until a page reload.
  loadLanguageOptions()
  if (trackerRef.value) trackerRef.value.loadData()
  if (shelvesRef.value) shelvesRef.value.loadLocations()
}

function handleReadingUpdated() {
  fetchBooks()
}

function handleFilterRoom(room) {
  currentView.value = 'catalog'
  roomFilter.value = room
  fetchBooks()
}

function handleHonorificsChanged() {
  fetchBooks()
}

onMounted(() => {
  fetchBooks()
  loadLanguageOptions()
})
</script>
