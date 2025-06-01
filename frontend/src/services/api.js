import axios from 'axios'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// API service methods
export const apiService = {
  // Upload PDF file
  async uploadPDF(file) {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  // Send query to get AI response
  async sendQuery(query, conversationId = null, topK = 5) {
    const response = await api.post('/query', {
      query,
      conversation_id: conversationId,
      top_k: topK
    })
    return response.data
  },

  // Request web search permission and perform search
  async performWebSearch(conversationId, approved) {
    const response = await api.post('/web-search', {
      conversation_id: conversationId,
      approved: approved
    })
    return response.data
  },

  // Get conversation history
  async getConversationHistory(conversationId) {
    const response = await api.get(`/conversations/${conversationId}`)
    return response.data
  },

  // Get all conversations
  async getAllConversations() {
    const response = await api.get('/conversations')
    return response.data
  },

  // Delete conversation
  async deleteConversation(conversationId) {
    const response = await api.delete(`/conversations/${conversationId}`)
    return response.data
  },

  // Health check
  async healthCheck() {
    const response = await api.get('/health')
    return response.data
  }
}

// Response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error)
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail)
    }
    throw error
  }
)

export default api 