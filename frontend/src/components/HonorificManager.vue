<template>
  <v-card variant="outlined" class="pa-3 my-2">
    <v-card-title class="d-flex align-center px-1 py-1">
      <v-icon icon="mdi-account-tie" color="primary" class="mr-2"></v-icon>
      <span class="text-subtitle-1 font-weight-bold">Author honorifics</span>
      <v-spacer></v-spacer>
      <v-btn
        size="small"
        color="primary"
        variant="tonal"
        prepend-icon="mdi-plus"
        @click="openCreate"
      >
        Add honorific
      </v-btn>
    </v-card-title>

    <v-divider class="my-2"></v-divider>

    <div class="text-body-2 text-medium-emphasis mb-2 px-1">
      Titles stay in first, middle, and last name. This list only changes the catalog short form.
    </div>

    <v-alert
      v-if="listError"
      type="error"
      variant="tonal"
      density="compact"
      class="mb-2"
      :text="listError"
    ></v-alert>

    <div v-if="loading" class="text-center py-4">
      <v-progress-circular indeterminate color="primary" size="28"></v-progress-circular>
    </div>

    <div v-else-if="loadError" class="text-center py-4 text-error text-caption">
      {{ loadError }}
    </div>

    <div v-else-if="rows.length === 0" class="text-center py-4 text-grey">
      <div class="text-caption">No honorifics yet. Add a prefix or suffix.</div>
    </div>

    <v-table v-else density="compact">
      <thead>
        <tr>
          <th>Tokens</th>
          <th>Role</th>
          <th>Abbreviation</th>
          <th>Enabled</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="row.id">
          <td>{{ row.tokens }}</td>
          <td>{{ row.role }}</td>
          <td>{{ row.abbreviation || '—' }}</td>
          <td>
            <v-switch
              :model-value="row.enabled"
              hide-details
              density="compact"
              color="primary"
              @update:model-value="toggleEnabled(row, $event)"
            ></v-switch>
          </td>
          <td class="text-right">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              size="small"
              aria-label="Edit honorific"
              @click="openEdit(row)"
            ></v-btn>
            <v-btn
              icon="mdi-delete"
              variant="text"
              size="small"
              color="error"
              aria-label="Delete honorific"
              @click="confirmDelete(row)"
            ></v-btn>
          </td>
        </tr>
      </tbody>
    </v-table>
  </v-card>

  <v-dialog v-model="showDialog" max-width="480">
    <v-card>
      <v-card-title class="text-subtitle-1 font-weight-bold">
        {{ editingId ? 'Edit honorific' : 'Add honorific' }}
      </v-card-title>
      <v-card-text>
        <v-alert
          v-if="formError"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-3"
          :text="formError"
        ></v-alert>
        <v-text-field
          v-model="form.tokens"
          label="Tokens *"
          hint="Space-separated, match order"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        ></v-text-field>
        <v-select
          v-model="form.role"
          label="Role"
          :items="roleOptions"
          variant="outlined"
          density="comfortable"
          class="mb-2"
        ></v-select>
        <v-text-field
          v-model="form.abbreviation"
          label="Abbreviation"
          hint="Leave empty to omit from the card"
          persistent-hint
          variant="outlined"
          density="comfortable"
          class="mb-2"
        ></v-text-field>
        <v-switch
          v-model="form.enabled"
          label="Enabled"
          color="primary"
          hide-details
        ></v-switch>
      </v-card-text>
      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="plain" @click="showDialog = false">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="saving"
          :disabled="saving || !(form.tokens || '').trim()"
          @click="submitForm"
        >
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const emit = defineEmits(['changed'])

const loading = ref(false)
const loadError = ref('')
const listError = ref('')
const rows = ref([])
const showDialog = ref(false)
const saving = ref(false)
const formError = ref('')
const editingId = ref(null)
const form = ref(emptyForm())
const roleOptions = [
  { title: 'Prefix', value: 'prefix' },
  { title: 'Suffix', value: 'suffix' },
]

function emptyForm() {
  return { tokens: '', role: 'prefix', abbreviation: '', enabled: true }
}

function errorMessage(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return 'Could not save honorific.'
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  formError.value = ''
  showDialog.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.value = {
    tokens: row.tokens,
    role: row.role,
    abbreviation: row.abbreviation || '',
    enabled: row.enabled,
  }
  formError.value = ''
  showDialog.value = true
}

async function submitForm() {
  const tokens = (form.value.tokens || '').trim()
  if (!tokens || saving.value) return
  saving.value = true
  formError.value = ''
  const payload = {
    tokens,
    role: form.value.role,
    abbreviation: (form.value.abbreviation || '').trim(),
    enabled: form.value.enabled,
  }
  try {
    if (editingId.value) {
      await api.updateHonorific(editingId.value, payload)
    } else {
      await api.createHonorific(payload)
    }
    showDialog.value = false
    await loadHonorifics()
    emit('changed')
  } catch (err) {
    formError.value = errorMessage(err)
  } finally {
    saving.value = false
  }
}

async function toggleEnabled(row, enabled) {
  try {
    await api.updateHonorific(row.id, { enabled })
    await loadHonorifics()
    emit('changed')
  } catch (err) {
    console.error('Failed to update honorific', err)
    await loadHonorifics()
  }
}

async function confirmDelete(row) {
  if (!window.confirm('Delete this honorific? Catalog short forms will update.')) return
  listError.value = ''
  try {
    await api.deleteHonorific(row.id)
    await loadHonorifics()
    emit('changed')
  } catch (err) {
    listError.value = errorMessage(err)
  }
}

async function loadHonorifics() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.getHonorifics()
    rows.value = res.data || []
  } catch (err) {
    loadError.value = errorMessage(err)
    rows.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHonorifics()
})

defineExpose({ loadHonorifics })
</script>
