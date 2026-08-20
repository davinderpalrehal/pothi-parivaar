import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

export default {
  // Health
  getHealth() {
    return axios.get('/api/health')
  },

  // Books
  getBooks(params = {}) {
    return apiClient.get('/books', { params })
  },
  getBook(id) {
    return apiClient.get(`/books/${id}`)
  },
  createBook(bookData) {
    return apiClient.post('/books', bookData)
  },
  updateBook(id, bookData) {
    return apiClient.put(`/books/${id}`, bookData)
  },
  deleteBook(id) {
    return apiClient.delete(`/books/${id}`)
  },

  // Readers
  getReaders() {
    return apiClient.get('/readers')
  },
  createReader(readerData) {
    return apiClient.post('/readers', readerData)
  },
  getReaderSessions(readerId, status = null) {
    const params = status ? { status } : {}
    return apiClient.get(`/readers/${readerId}/sessions`, { params })
  },
  createSession(sessionData) {
    return apiClient.post('/readers/sessions', sessionData)
  },
  updateSession(sessionId, sessionData) {
    return apiClient.put(`/readers/sessions/${sessionId}`, sessionData)
  },

  // Locations
  getLocations() {
    return apiClient.get('/locations')
  },
  getLocationsSummary() {
    return apiClient.get('/locations/summary')
  },

  // ISBN Lookup
  lookupISBN(isbn) {
    return apiClient.get(`/isbn/${isbn}`)
  },

  // Hermes Agent
  getHermesStatus() {
    return apiClient.get('/hermes/status')
  },
  getHermesRecommend(params = {}) {
    return apiClient.get('/hermes/recommend', { params })
  },
  locateBook(query) {
    return apiClient.get(`/hermes/locate/${encodeURIComponent(query)}`)
  },
}
