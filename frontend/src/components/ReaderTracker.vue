<template>
  <v-card variant="outlined" class="pa-4 my-2">
    <!-- Header & Family Profiles Bar -->
    <div class="d-flex flex-wrap justify-space-between align-center ga-2 mb-3">
      <div class="d-flex align-center">
        <v-icon icon="mdi-account-group" color="primary" class="mr-2" size="large"></v-icon>
        <div>
          <div class="text-h6 font-weight-bold">Family Reading Tracker</div>
          <div class="text-caption text-grey">Track reading journeys, page milestones, and book finishes</div>
        </div>
      </div>
      <div class="d-flex ga-2">
        <v-btn
          size="small"
          color="primary"
          variant="outlined"
          prepend-icon="mdi-book-plus"
          @click="openStartReadingDialog"
        >
          Start Reading
        </v-btn>
        <v-btn
          size="small"
          color="primary"
          variant="flat"
          prepend-icon="mdi-account-plus"
          @click="openAddReaderDialog"
        >
          Add Reader
        </v-btn>
      </div>
    </div>

    <!-- Reader Selector Chips -->
    <div class="d-flex flex-wrap align-center ga-2 mb-4 pb-2 border-b">
      <v-chip
        :variant="selectedReaderId === null ? 'flat' : 'outlined'"
        color="primary"
        size="comfortable"
        prepend-icon="mdi-account-multiple"
        class="font-weight-medium"
        @click="selectReader(null)"
      >
        All Family ({{ activeSessions.length }})
      </v-chip>

      <v-chip
        v-for="reader in readers"
        :key="reader.id"
        :variant="selectedReaderId === reader.id ? 'flat' : 'outlined'"
        color="primary"
        size="comfortable"
        class="font-weight-medium"
        @click="selectReader(reader.id)"
      >
        <template #prepend>
          <v-icon :icon="reader.avatar_icon || 'mdi-account'" class="mr-1"></v-icon>
        </template>
        {{ reader.name }}
        <span v-if="reader.age_group" class="ml-1 text-caption opacity-80">({{ formatAgeGroup(reader.age_group) }})</span>
      </v-chip>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-6">
      <v-progress-circular indeterminate color="primary" size="36"></v-progress-circular>
      <div class="text-caption text-grey mt-2">Loading reading progress...</div>
    </div>

    <!-- Individual Reader Detail View -->
    <div v-else-if="selectedReaderId !== null && selectedReaderStats">
      <!-- Reader Header & Stats -->
      <v-card variant="tonal" color="primary" class="pa-3 mb-4">
        <div class="d-flex flex-wrap justify-space-between align-center ga-2">
          <div class="d-flex align-center ga-3">
            <v-avatar color="primary" size="48">
              <v-icon :icon="selectedReaderStats.reader.avatar_icon || 'mdi-account'" size="large" color="white"></v-icon>
            </v-avatar>
            <div>
              <div class="text-h6 font-weight-bold text-high-emphasis">
                {{ selectedReaderStats.reader.name }}
              </div>
              <div class="text-caption text-grey-darken-1">
                {{ selectedReaderStats.reader.age_group ? formatAgeGroup(selectedReaderStats.reader.age_group) : 'Family Reader' }}
              </div>
            </div>
          </div>
          <div class="d-flex ga-1">
            <v-btn
              size="small"
              variant="text"
              icon="mdi-pencil"
              color="grey-darken-2"
              title="Edit Profile"
              @click="openEditReaderDialog(selectedReaderStats.reader)"
            ></v-btn>
            <v-btn
              size="small"
              variant="text"
              icon="mdi-delete"
              color="error"
              title="Delete Reader"
              @click="confirmDeleteReader(selectedReaderStats.reader)"
            ></v-btn>
          </div>
        </div>

        <!-- 3 Metric Cards -->
        <v-row class="mt-2" dense>
          <v-col cols="4">
            <v-card variant="flat" class="pa-2 text-center bg-white rounded">
              <div class="text-caption text-grey">Currently Reading</div>
              <div class="text-h6 font-weight-bold text-primary">{{ selectedReaderStats.total_reading }}</div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="flat" class="pa-2 text-center bg-white rounded">
              <div class="text-caption text-grey">Books Completed</div>
              <div class="text-h6 font-weight-bold text-success">{{ selectedReaderStats.total_finished }} 🏆</div>
            </v-card>
          </v-col>
          <v-col cols="4">
            <v-card variant="flat" class="pa-2 text-center bg-white rounded">
              <div class="text-caption text-grey">Total Pages Read</div>
              <div class="text-h6 font-weight-bold text-secondary">{{ selectedReaderStats.total_pages_read }}</div>
            </v-card>
          </v-col>
        </v-row>
      </v-card>

      <!-- Active Sessions for Selected Reader -->
      <div class="mb-4">
        <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
          <v-icon icon="mdi-book-open-page-variant" color="primary" class="mr-2" size="small"></v-icon>
          In Progress ({{ selectedReaderStats.active_sessions.length }})
        </div>

        <div v-if="selectedReaderStats.active_sessions.length === 0" class="text-center py-4 text-grey bg-grey-lighten-5 rounded">
          <v-icon icon="mdi-book-open-blank-variant" size="large" class="mb-1"></v-icon>
          <div class="text-caption">No books currently being read by {{ selectedReaderStats.reader.name }}.</div>
          <v-btn size="small" variant="text" color="primary" class="mt-1" @click="openStartReadingDialog">Pick a book to start</v-btn>
        </div>

        <v-row v-else dense>
          <v-col v-for="item in selectedReaderStats.active_sessions" :key="item.id" cols="12" sm="6">
            <v-card variant="outlined" class="pa-3 h-100 d-flex flex-column justify-space-between">
              <div>
                <div class="d-flex ga-3 mb-2">
                  <v-img
                    :src="item.book.cover_url || '/placeholder-book.png'"
                    width="50"
                    height="75"
                    cover
                    class="rounded bg-grey-lighten-3 flex-shrink-0"
                  >
                    <template #placeholder>
                      <div class="d-flex align-center justify-center fill-height">
                        <v-icon icon="mdi-book" color="grey-lighten-1"></v-icon>
                      </div>
                    </template>
                  </v-img>

                  <div class="flex-grow-1 overflow-hidden">
                    <div class="font-weight-bold text-subtitle-2 text-truncate" :title="item.book.title">{{ item.book.title }}</div>
                    <div class="text-caption text-grey text-truncate">{{ item.book.author }}</div>
                    <v-chip
                      v-if="item.book.location_room || item.book.location_unit || item.book.location_shelf"
                      size="x-small"
                      color="secondary"
                      variant="tonal"
                      class="mt-1"
                    >
                      📍 {{ [item.book.location_room, item.book.location_unit, item.book.location_shelf].filter(Boolean).join(' / ') }}
                    </v-chip>
                  </div>
                </div>

                <!-- Progress Bar -->
                <div class="mb-2">
                  <div class="d-flex justify-space-between text-caption font-weight-medium mb-1">
                    <span>Page {{ item.current_page }} of {{ item.book.page_count || '?' }}</span>
                    <span class="text-primary">{{ item.progress_percent }}%</span>
                  </div>
                  <v-progress-linear
                    :model-value="item.progress_percent"
                    color="primary"
                    height="8"
                    rounded
                  ></v-progress-linear>
                </div>
              </div>

              <!-- Actions -->
              <div class="d-flex justify-space-between align-center pt-2 border-t">
                <v-btn
                  size="small"
                  variant="outlined"
                  color="primary"
                  prepend-icon="mdi-bookmark-check"
                  @click="openUpdatePageDialog(item)"
                >
                  Update Page
                </v-btn>
                <v-btn
                  size="small"
                  variant="flat"
                  color="success"
                  prepend-icon="mdi-check-circle"
                  @click="openFinishDialog(item)"
                >
                  Finished!
                </v-btn>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </div>

      <!-- Completed History for Selected Reader -->
      <div>
        <div class="text-subtitle-1 font-weight-bold mb-2 d-flex align-center">
          <v-icon icon="mdi-trophy-outline" color="amber-darken-2" class="mr-2" size="small"></v-icon>
          Finished Books Log ({{ selectedReaderStats.history.length }})
        </div>

        <div v-if="selectedReaderStats.history.length === 0" class="text-center py-4 text-grey bg-grey-lighten-5 rounded">
          <v-icon icon="mdi-trophy-broken" size="large" class="mb-1"></v-icon>
          <div class="text-caption">No completed books yet. Finish a book to record reading milestones!</div>
        </div>

        <v-list v-else lines="two" class="pa-0">
          <v-list-item
            v-for="item in selectedReaderStats.history"
            :key="item.id"
            class="px-3 py-2 mb-2 rounded bg-grey-lighten-5 border"
          >
            <template #prepend>
              <v-avatar rounded size="40" class="bg-grey-lighten-3 mr-2">
                <v-img :src="item.book.cover_url" cover>
                  <template #placeholder>
                    <v-icon icon="mdi-book" color="grey"></v-icon>
                  </template>
                </v-img>
              </v-avatar>
            </template>

            <v-list-item-title class="font-weight-bold text-subtitle-2">
              {{ item.book.title }}
            </v-list-item-title>

            <v-list-item-subtitle class="mt-1">
              <div class="d-flex flex-wrap align-center ga-2">
                <span class="text-caption text-grey">{{ item.book.author }}</span>
                <span v-if="item.finish_date" class="text-caption text-success">
                  &bull; Completed {{ item.finish_date }}
                </span>
                <span v-if="item.rating" class="text-caption text-amber-darken-3">
                  &bull; {{ '★'.repeat(item.rating) }}
                </span>
              </div>
              <div v-if="item.notes" class="text-caption text-grey-darken-2 font-italic mt-1">
                "{{ item.notes }}"
              </div>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </div>
    </div>

    <!-- All Family Active Sessions View -->
    <div v-else>
      <div v-if="activeSessions.length === 0" class="text-center py-6 text-grey bg-grey-lighten-5 rounded">
        <v-icon icon="mdi-book-open-blank-variant" size="x-large" class="mb-2 text-grey-lighten-1"></v-icon>
        <div class="text-subtitle-2 font-weight-medium">No one is currently reading a book</div>
        <div class="text-caption">Select any book in the catalog and tap "Start Reading" to begin tracking!</div>
        <v-btn
          color="primary"
          variant="tonal"
          size="small"
          class="mt-3"
          prepend-icon="mdi-book-plus"
          @click="openStartReadingDialog"
        >
          Pick a Book to Read
        </v-btn>
      </div>

      <v-row v-else dense>
        <v-col v-for="item in activeSessions" :key="item.id" cols="12" md="6">
          <v-card variant="outlined" class="pa-3 h-100 d-flex flex-column justify-space-between bg-white">
            <div>
              <div class="d-flex justify-space-between align-center mb-2">
                <v-chip size="small" color="primary" variant="flat">
                  <template #prepend>
                    <v-icon :icon="item.reader.avatar_icon || 'mdi-account'" size="small" class="mr-1"></v-icon>
                  </template>
                  {{ item.reader.name }}
                </v-chip>
                <span class="text-caption text-grey">Started {{ item.start_date || 'recently' }}</span>
              </div>

              <div class="d-flex ga-3 mb-2">
                <v-img
                  :src="item.book.cover_url || '/placeholder-book.png'"
                  width="50"
                  height="75"
                  cover
                  class="rounded bg-grey-lighten-3 flex-shrink-0"
                >
                  <template #placeholder>
                    <div class="d-flex align-center justify-center fill-height">
                      <v-icon icon="mdi-book" color="grey-lighten-1"></v-icon>
                    </div>
                  </template>
                </v-img>

                <div class="flex-grow-1 overflow-hidden">
                  <div class="font-weight-bold text-subtitle-2 text-truncate" :title="item.book.title">{{ item.book.title }}</div>
                  <div class="text-caption text-grey text-truncate">{{ item.book.author }}</div>
                  <v-chip
                    v-if="item.book.location_room || item.book.location_unit || item.book.location_shelf"
                    size="x-small"
                    color="secondary"
                    variant="tonal"
                    class="mt-1"
                  >
                    📍 {{ [item.book.location_room, item.book.location_unit, item.book.location_shelf].filter(Boolean).join(' / ') }}
                  </v-chip>
                </div>
              </div>

              <!-- Progress Bar -->
              <div class="mb-2">
                <div class="d-flex justify-space-between text-caption font-weight-medium mb-1">
                  <span>Page {{ item.current_page }} of {{ item.book.page_count || '?' }}</span>
                  <span class="text-primary font-weight-bold">{{ item.progress_percent }}%</span>
                </div>
                <v-progress-linear
                  :model-value="item.progress_percent"
                  color="primary"
                  height="8"
                  rounded
                ></v-progress-linear>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="d-flex justify-space-between align-center pt-2 border-t mt-2">
              <v-btn
                size="small"
                variant="outlined"
                color="primary"
                prepend-icon="mdi-bookmark-check"
                @click="openUpdatePageDialog(item)"
              >
                Update Page
              </v-btn>
              <v-btn
                size="small"
                variant="flat"
                color="success"
                prepend-icon="mdi-check-circle"
                @click="openFinishDialog(item)"
              >
                Finished!
              </v-btn>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </div>

    <!-- DIALOG: Update Page Progress -->
    <v-dialog v-model="showUpdatePageDialog" max-width="450">
      <v-card v-if="selectedSession">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            Update Page Progress
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="showUpdatePageDialog = false"></v-btn>
        </v-toolbar>

        <v-card-text class="pt-4">
          <div class="text-subtitle-2 font-weight-bold mb-1">{{ selectedSession.book.title }}</div>
          <div class="text-caption text-grey mb-3">Reader: {{ selectedSession.reader.name }}</div>

          <v-text-field
            v-model.number="pageInputValue"
            label="Current Page Number"
            type="number"
            min="0"
            :max="selectedSession.book.page_count || 2000"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-book-open-page-variant"
            class="mb-2"
          ></v-text-field>

          <v-alert
            v-if="pageWouldBeCapped"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-2"
          >
            That page is past the end of the book. It will be saved as page {{ selectedSession.book.page_count }}.
          </v-alert>

          <div v-if="selectedSession.book.page_count" class="mb-3">
            <div class="text-caption text-grey mb-1">Slide to adjust bookmark:</div>
            <v-slider
              v-model="pageInputValue"
              min="0"
              :max="selectedSession.book.page_count"
              step="1"
              color="primary"
              thumb-label
            ></v-slider>
          </div>

          <!-- Quick Jump Buttons -->
          <div class="d-flex ga-2 justify-center">
            <v-btn size="x-small" variant="tonal" @click="adjustPage(-10)">-10</v-btn>
            <v-btn size="x-small" variant="tonal" @click="adjustPage(-5)">-5</v-btn>
            <v-btn size="x-small" variant="tonal" @click="adjustPage(5)">+5</v-btn>
            <v-btn size="x-small" variant="tonal" @click="adjustPage(10)">+10</v-btn>
            <v-btn size="x-small" variant="tonal" @click="adjustPage(25)">+25</v-btn>
          </div>
        </v-card-text>

        <v-card-actions class="pa-3 border-t">
          <v-btn
            size="small"
            color="error"
            variant="text"
            prepend-icon="mdi-trash-can-outline"
            @click="confirmDropSession(selectedSession)"
          >
            Remove Session
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="showUpdatePageDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="savePageUpdate">
            Save Page
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Finish Book Celebration -->
    <v-dialog v-model="showFinishDialog" max-width="480">
      <v-card v-if="selectedSession" class="text-center">
        <div class="bg-success py-4 px-3 text-white">
          <v-icon icon="mdi-trophy" size="48" class="mb-1"></v-icon>
          <div class="text-h6 font-weight-bold">Congratulations! 🎉</div>
          <div class="text-caption opacity-90">{{ selectedSession.reader.name }} finished reading:</div>
          <div class="text-subtitle-1 font-weight-bold mt-1">{{ selectedSession.book.title }}</div>
        </div>

        <v-card-text class="pt-4 text-left">
          <v-text-field
            v-model="finishDateValue"
            label="Completion Date"
            type="date"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-calendar-check"
            class="mb-2"
          ></v-text-field>

          <div class="mb-3">
            <div class="text-caption text-grey mb-1">Family Star Rating:</div>
            <v-rating
              v-model="finishRatingValue"
              color="amber-darken-3"
              density="compact"
              hover
            ></v-rating>
          </div>

          <v-textarea
            v-model="finishNotesValue"
            label="Reading Reflection or Memory (Optional)"
            rows="2"
            variant="outlined"
            density="comfortable"
            placeholder="e.g., Harleen loved chapter 4; read together at bedtime"
          ></v-textarea>
        </v-card-text>

        <v-card-actions class="pa-3 border-t">
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="showFinishDialog = false">Cancel</v-btn>
          <v-btn color="success" variant="flat" prepend-icon="mdi-check" @click="saveFinishSession">
            Record Finish & Milestone
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Add / Edit Reader -->
    <v-dialog v-model="showReaderDialog" max-width="420">
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            {{ isEditingReader ? 'Edit Family Reader' : 'Add Family Reader' }}
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="showReaderDialog = false"></v-btn>
        </v-toolbar>

        <v-card-text class="pt-4">
          <v-text-field
            v-model="readerForm.name"
            label="Name (e.g. Harleen, Fateh, Davinderpal)"
            variant="outlined"
            density="comfortable"
            class="mb-2"
          ></v-text-field>

          <v-select
            v-model="readerForm.age_group"
            :items="ageGroupOptions"
            item-title="title"
            item-value="value"
            label="Age Group / Role"
            variant="outlined"
            density="comfortable"
            class="mb-2"
          ></v-select>

          <div class="text-caption text-grey mb-2">Select Avatar Icon:</div>
          <div class="d-flex flex-wrap ga-2">
            <v-btn
              v-for="icon in avatarOptions"
              :key="icon"
              icon
              size="small"
              :variant="readerForm.avatar_icon === icon ? 'flat' : 'outlined'"
              color="primary"
              @click="readerForm.avatar_icon = icon"
            >
              <v-icon :icon="icon"></v-icon>
            </v-btn>
          </div>
        </v-card-text>

        <v-card-actions class="pa-3 border-t">
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="showReaderDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" :disabled="!readerForm.name" @click="saveReader">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DIALOG: Start Reading A Book -->
    <v-dialog v-model="showStartReadingDialog" max-width="480">
      <v-card>
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="text-subtitle-1 font-weight-bold">
            Start Reading a Book
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon="mdi-close" variant="text" @click="showStartReadingDialog = false"></v-btn>
        </v-toolbar>

        <v-card-text class="pt-4">
          <v-select
            v-model="startReadingForm.reader_id"
            :items="readers"
            item-title="name"
            item-value="id"
            label="Who is reading?"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-account"
            class="mb-2"
          ></v-select>

          <v-autocomplete
            v-model="startReadingForm.book_id"
            :items="availableBooks"
            item-title="title"
            item-value="id"
            label="Select Book from Catalog"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-book"
            :loading="booksLoading"
            placeholder="Type to search books..."
            class="mb-2"
            @update:search="onBookSearch"
          >
            <template #item="{ props, item }">
              <v-list-item v-bind="props" :subtitle="item.raw.author"></v-list-item>
            </template>
          </v-autocomplete>

          <v-text-field
            v-model.number="startReadingForm.start_page"
            label="Start Page (default: 0)"
            type="number"
            min="0"
            variant="outlined"
            density="comfortable"
            prepend-inner-icon="mdi-bookmark-outline"
          ></v-text-field>
        </v-card-text>

        <v-card-actions class="pa-3 border-t">
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="showStartReadingDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :disabled="!startReadingForm.reader_id || !startReadingForm.book_id"
            @click="submitStartReading"
          >
            Start Reading
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="confirmDialog.show" max-width="420">
      <v-card>
        <v-card-title class="text-subtitle-1 font-weight-bold">
          {{ confirmDialog.title }}
        </v-card-title>
        <v-card-text>{{ confirmDialog.message }}</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="plain" @click="confirmDialog.show = false">Cancel</v-btn>
          <v-btn :color="confirmDialog.color" variant="flat" @click="runConfirmAction">
            {{ confirmDialog.confirmText }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '../services/api'

const emit = defineEmits(['refresh'])

const loading = ref(false)
const readers = ref([])
const activeSessions = ref([])
const selectedReaderId = ref(null)
const selectedReaderStats = ref(null)

// Dialog states
const showUpdatePageDialog = ref(false)
const showFinishDialog = ref(false)
const showReaderDialog = ref(false)
const showStartReadingDialog = ref(false)
const isEditingReader = ref(false)
const editingReaderId = ref(null)

// Selection & Form values
const selectedSession = ref(null)
const pageInputValue = ref(0)
const finishDateValue = ref('')
const finishRatingValue = ref(5)
const finishNotesValue = ref('')

const readerForm = reactive({
  name: '',
  avatar_icon: 'mdi-account',
  age_group: 'child-10',
})

const startReadingForm = reactive({
  reader_id: null,
  book_id: null,
  start_page: 0,
})

const availableBooks = ref([])
const booksLoading = ref(false)
let statsReqId = 0
let bookSearchTimer = null

const snackbar = reactive({
  show: false,
  text: '',
  color: 'error',
})

const confirmDialog = reactive({
  show: false,
  title: '',
  message: '',
  confirmText: 'Confirm',
  color: 'error',
  onConfirm: null,
})

const pageWouldBeCapped = computed(() => {
  const max = selectedSession.value?.book?.page_count
  return Boolean(max && Number(pageInputValue.value) > max)
})

const avatarOptions = [
  'mdi-account',
  'mdi-face-woman',
  'mdi-face-man',
  'mdi-school',
  'mdi-star',
  'mdi-heart',
  'mdi-emoticon-happy',
  'mdi-rocket-launch',
  'mdi-book-open-page-variant',
  'mdi-palette',
]

const ageGroupOptions = [
  { title: 'Child (10yo - Eldest)', value: 'child-10' },
  { title: 'Child (7yo - Middle)', value: 'child-7' },
  { title: 'Toddler (2yo - Youngest)', value: 'child-2' },
  { title: 'Parent / Adult', value: 'adult' },
  { title: 'Grandparent', value: 'grandparent' },
]

function formatAgeGroup(val) {
  if (!val) return ''
  const opt = ageGroupOptions.find(o => o.value === val)
  return opt ? opt.title : val
}

function notify(text, color = 'error') {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}

function errorMessage(err, fallback) {
  const detail = err?.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}

function localDateISO() {
  const d = new Date()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

function openConfirm({ title, message, confirmText = 'Confirm', color = 'error', onConfirm }) {
  confirmDialog.title = title
  confirmDialog.message = message
  confirmDialog.confirmText = confirmText
  confirmDialog.color = color
  confirmDialog.onConfirm = onConfirm
  confirmDialog.show = true
}

async function runConfirmAction() {
  const action = confirmDialog.onConfirm
  confirmDialog.show = false
  confirmDialog.onConfirm = null
  if (action) await action()
}

async function loadData() {
  loading.value = true
  try {
    const readersRes = await api.getReaders()
    readers.value = readersRes.data
  } catch (err) {
    notify(errorMessage(err, 'Failed to load family readers'))
  }
  try {
    const activityRes = await api.getReaderActivity()
    activeSessions.value = activityRes.data
  } catch (err) {
    activeSessions.value = []
    notify(errorMessage(err, 'Failed to load family activity'))
  }
  if (selectedReaderId.value !== null) {
    await loadReaderStats(selectedReaderId.value)
  }
  loading.value = false
}

async function selectReader(readerId) {
  selectedReaderId.value = readerId
  if (readerId === null) {
    selectedReaderStats.value = null
  } else {
    await loadReaderStats(readerId)
  }
}

async function loadReaderStats(readerId) {
  const req = ++statsReqId
  try {
    const statsRes = await api.getReaderStats(readerId)
    if (req !== statsReqId) return
    selectedReaderStats.value = statsRes.data
  } catch (err) {
    if (req !== statsReqId) return
    selectedReaderStats.value = null
    notify(errorMessage(err, 'Failed to load reader stats'))
  }
}

function openAddReaderDialog() {
  isEditingReader.value = false
  editingReaderId.value = null
  readerForm.name = ''
  readerForm.avatar_icon = 'mdi-account'
  readerForm.age_group = 'child-10'
  showReaderDialog.value = true
}

function openEditReaderDialog(reader) {
  isEditingReader.value = true
  editingReaderId.value = reader.id
  readerForm.name = reader.name
  readerForm.avatar_icon = reader.avatar_icon || 'mdi-account'
  readerForm.age_group = reader.age_group || 'child-10'
  showReaderDialog.value = true
}

async function saveReader() {
  const name = (readerForm.name || '').trim()
  if (!name) {
    notify('Reader name is required', 'warning')
    return
  }
  try {
    if (isEditingReader.value && editingReaderId.value) {
      await api.updateReader(editingReaderId.value, {
        name,
        avatar_icon: readerForm.avatar_icon,
        age_group: readerForm.age_group,
      })
    } else {
      await api.createReader({
        name,
        avatar_icon: readerForm.avatar_icon,
        age_group: readerForm.age_group,
      })
    }
    showReaderDialog.value = false
    await loadData()
    emit('refresh')
  } catch (err) {
    notify(errorMessage(err, 'Failed to save reader'))
  }
}

function confirmDeleteReader(reader) {
  openConfirm({
    title: 'Delete reader profile?',
    message: `Delete "${reader.name}" and all their reading history?`,
    confirmText: 'Delete',
    onConfirm: async () => {
      try {
        await api.deleteReader(reader.id)
        selectedReaderId.value = null
        selectedReaderStats.value = null
        await loadData()
        emit('refresh')
      } catch (err) {
        notify(errorMessage(err, 'Failed to delete reader'))
      }
    },
  })
}

function openUpdatePageDialog(session) {
  selectedSession.value = session
  pageInputValue.value = session.current_page || 0
  showUpdatePageDialog.value = true
}

function adjustPage(delta) {
  const max = selectedSession.value?.book?.page_count || 9999
  pageInputValue.value = Math.max(0, Math.min(max, (pageInputValue.value || 0) + delta))
}

async function savePageUpdate() {
  if (!selectedSession.value) return
  const max = selectedSession.value.book?.page_count
  let page = Number(pageInputValue.value)
  if (Number.isNaN(page)) page = 0
  if (page < 0) page = 0
  if (max && page > max) {
    page = max
    pageInputValue.value = max
    notify(`Page was capped at ${max} (this book's last page).`, 'warning')
  }
  try {
    await api.updateSession(selectedSession.value.id, {
      current_page: page,
    })
    showUpdatePageDialog.value = false
    await loadData()
    emit('refresh')
  } catch (err) {
    notify(errorMessage(err, 'Failed to update page'))
  }
}

function confirmDropSession(session) {
  openConfirm({
    title: 'Remove reading session?',
    message: `Remove the reading session for "${session.book.title}"?`,
    confirmText: 'Remove',
    onConfirm: async () => {
      try {
        await api.deleteSession(session.id)
        showUpdatePageDialog.value = false
        await loadData()
        emit('refresh')
      } catch (err) {
        notify(errorMessage(err, 'Failed to delete session'))
      }
    },
  })
}

function openFinishDialog(session) {
  selectedSession.value = session
  finishDateValue.value = localDateISO()
  finishRatingValue.value = 5
  finishNotesValue.value = ''
  showFinishDialog.value = true
}

async function saveFinishSession() {
  if (!selectedSession.value) return
  try {
    await api.updateSession(selectedSession.value.id, {
      status: 'finished',
      current_page: selectedSession.value.book?.page_count || selectedSession.value.current_page,
      finish_date: finishDateValue.value || localDateISO(),
      rating: finishRatingValue.value,
      notes: finishNotesValue.value || null,
    })
    showFinishDialog.value = false
    await loadData()
    emit('refresh')
  } catch (err) {
    notify(errorMessage(err, 'Failed to record finish'))
  }
}

async function searchAvailableBooks(query = '') {
  booksLoading.value = true
  try {
    const params = { limit: 500 }
    if (query) params.q = query
    const res = await api.getBooks(params)
    availableBooks.value = res.data
  } catch (err) {
    availableBooks.value = []
    notify(errorMessage(err, 'Failed to load books for start reading'))
  } finally {
    booksLoading.value = false
  }
}

function onBookSearch(query) {
  clearTimeout(bookSearchTimer)
  bookSearchTimer = setTimeout(() => {
    searchAvailableBooks(query)
  }, 250)
}

async function openStartReadingDialog() {
  startReadingForm.reader_id = selectedReaderId.value || (readers.value[0]?.id || null)
  startReadingForm.book_id = null
  startReadingForm.start_page = 0
  showStartReadingDialog.value = true
  await searchAvailableBooks()
}

async function submitStartReading() {
  if (!startReadingForm.reader_id || !startReadingForm.book_id) return
  const alreadyReading = activeSessions.value.some(
    (session) =>
      session.reader_id === startReadingForm.reader_id &&
      session.book_id === startReadingForm.book_id
  )
  if (alreadyReading) {
    notify('This family member is already reading this book', 'warning')
    return
  }
  try {
    await api.createSession({
      reader_id: startReadingForm.reader_id,
      book_id: startReadingForm.book_id,
      current_page: startReadingForm.start_page || 0,
      status: 'reading',
    })
    showStartReadingDialog.value = false
    await loadData()
    emit('refresh')
  } catch (err) {
    notify(errorMessage(err, 'Failed to start reading session'))
  }
}

onMounted(() => {
  loadData()
})

defineExpose({ loadData, openStartReadingDialog })
</script>
