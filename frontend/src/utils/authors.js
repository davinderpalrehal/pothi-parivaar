let rowKey = 0

function nextRowKey() {
  rowKey += 1
  return `author-${rowKey}`
}

export function emptyAuthorRow() {
  return { _key: nextRowKey(), first_name: '', last_name: '', middle_name: '' }
}

export function hydrateAuthorRows(authors) {
  if (!authors?.length) return [emptyAuthorRow()]
  return authors.filter((author) => author && typeof author === 'object').map((author) => ({
    _key: nextRowKey(),
    first_name: author.first_name || '',
    last_name: author.last_name ?? '',
    middle_name: author.middle_name || '',
  }))
}

function isBlank(value) {
  return !(value || '').trim()
}

export function isAuthorRowEmpty(row) {
  if (!row) return true
  const last = row.last_name
  const lastEmpty = last == null || last === '' || (last !== ' ' && isBlank(last))
  return isBlank(row.first_name) && isBlank(row.middle_name) && lastEmpty
}

export function lastNameIsPresent(value) {
  if (value === ' ') return true
  return !isBlank(value)
}

export function isAuthorRowIncomplete(row) {
  if (isAuthorRowEmpty(row)) return false
  return isBlank(row.first_name) || !lastNameIsPresent(row.last_name)
}

export function hasIncompleteAuthorRows(rows) {
  return (rows || []).some(isAuthorRowIncomplete)
}

export function authorsPayload(rows) {
  return (rows || [])
    .filter((row) => !isAuthorRowEmpty(row) && !isAuthorRowIncomplete(row))
    .map((row) => {
      const author = {
        first_name: (row.first_name || '').trim(),
        last_name: row.last_name === ' ' ? ' ' : (row.last_name || '').trim(),
      }
      const middle = (row.middle_name || '').trim()
      if (middle) author.middle_name = middle
      return author
    })
}
