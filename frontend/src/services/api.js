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
  getBookSessions(bookId) {
    return apiClient.get(`/books/${bookId}/sessions`)
  },

  // Readers
  getReaders() {
    return apiClient.get('/readers')
  },
  getReader(id) {
    return apiClient.get(`/readers/${id}`)
  },
  createReader(readerData) {
    return apiClient.post('/readers', readerData)
  },
  updateReader(id, readerData) {
    return apiClient.put(`/readers/${id}`, readerData)
  },
  deleteReader(id) {
    return apiClient.delete(`/readers/${id}`)
  },
  getReaderActivity() {
    return apiClient.get('/readers/activity')
  },
  getReaderStats(readerId) {
    return apiClient.get(`/readers/${readerId}/stats`)
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
  deleteSession(sessionId) {
    return apiClient.delete(`/readers/sessions/${sessionId}`)
  },

  // Locations
  getLocations() {
    return apiClient.get('/locations')
  },
  createLocation(locationData) {
    return apiClient.post('/locations', locationData)
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
