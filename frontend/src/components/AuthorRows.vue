<template>
  <v-row density="compact">
    <v-col cols="12">
      <div class="text-subtitle-2 font-weight-bold text-grey-darken-2 mb-1">
        <v-icon icon="mdi-account-multiple" size="small" class="mr-1"></v-icon>
        Authors
      </div>
    </v-col>

    <template v-for="(row, index) in modelValue" :key="row._key || index">
      <v-col cols="12" sm="4">
        <v-text-field
          :model-value="row.first_name"
          label="First"
          :rules="firstRules(row)"
          variant="outlined"
          density="comfortable"
          @update:model-value="patch(index, 'first_name', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="3">
        <v-text-field
          :model-value="row.middle_name"
          label="Middle"
          variant="outlined"
          density="comfortable"
          @update:model-value="patch(index, 'middle_name', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4">
        <v-text-field
          :model-value="row.last_name"
          label="Last"
          hint="Type a single space for a one-word name"
          persistent-hint
          :rules="lastRules(row)"
          variant="outlined"
          density="comfortable"
          @update:model-value="patch(index, 'last_name', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="1" class="d-flex align-start justify-end">
        <v-btn
          icon="mdi-close"
          variant="text"
          aria-label="Remove author"
          @click="remove(index)"
        ></v-btn>
      </v-col>
    </template>

    <v-col cols="12">
      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-plus"
        @click="add"
      >
        Add author
      </v-btn>
    </v-col>
  </v-row>
</template>

<script setup>
import { emptyAuthorRow, isAuthorRowEmpty, lastNameIsPresent } from '../utils/authors'

const props = defineProps({
  modelValue: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['update:modelValue'])

function replace(next) {
  emit('update:modelValue', next)
}

function patch(index, field, value) {
  replace(
    props.modelValue.map((row, i) => (i === index ? { ...row, [field]: value } : row))
  )
}

function add() {
  replace([...props.modelValue, emptyAuthorRow()])
}

function remove(index) {
  const next = props.modelValue.filter((_, i) => i !== index)
  replace(next.length ? next : [emptyAuthorRow()])
}

function firstRules(row) {
  if (isAuthorRowEmpty(row)) return []
  return [(v) => !!(v || '').trim() || 'First name is required']
}

function lastRules(row) {
  if (isAuthorRowEmpty(row)) return []
  return [(v) => lastNameIsPresent(v) || 'Last name is required']
}
</script>
