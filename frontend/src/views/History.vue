<template>
  <div class="container mt-4">
    <div class="row">
      <div class="col-12">
        <div class="card shadow">
          <div class="card-header bg-primary text-white">
            <h4 class="mb-0">
              <i class="fas fa-history me-2"></i>
              Conversation History
            </h4>
          </div>
          <div class="card-body">
            
            <!-- Loading State -->
            <div v-if="isLoading" class="text-center py-5">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <p class="mt-3 text-muted">Loading conversation history...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="conversations.length === 0" class="text-center py-5">
              <i class="fas fa-comments fa-3x text-muted mb-3"></i>
              <h5 class="text-muted">No conversations yet</h5>
              <p class="text-muted">Start a chat to see your conversation history here.</p>
              <router-link to="/" class="btn btn-primary">
                <i class="fas fa-plus me-2"></i>
                Start New Conversation
              </router-link>
            </div>

            <!-- Conversations List -->
            <div v-else>
              <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                  <span class="text-muted">{{ conversations.length }} conversation(s) found</span>
                </div>
                <div>
                  <button 
                    @click="refreshHistory" 
                    class="btn btn-sm btn-outline-primary me-2"
                    :disabled="isLoading"
                  >
                    <i class="fas fa-sync-alt me-1"></i>
                    Refresh
                  </button>
                </div>
              </div>

              <div class="conversations-list">
                <div 
                  v-for="conversation in conversations" 
                  :key="conversation.conversation_id"
                  class="conversation-item"
                  @click="viewConversation(conversation.conversation_id)"
                >
                  <div class="conversation-content">
                    <div class="conversation-header">
                      <div class="conversation-id">
                        <i class="fas fa-comments me-2"></i>
                        {{ conversation.conversation_id ? conversation.conversation_id.substring(0, 8) + '...' : 'N/A' }}
                      </div>
                      <div class="conversation-date">
                        {{ formatDate(conversation.updated_at) }}
                      </div>
                    </div>
                    <div class="conversation-preview">
                      {{ conversation.first_query || 'No preview available' }}
                    </div>
                  </div>
                  <div class="conversation-actions">
                    <button 
                      @click.stop="deleteConversation(conversation.conversation_id)"
                      class="btn btn-sm btn-outline-danger"
                      title="Delete conversation"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Conversation Detail Modal -->
    <div 
      v-if="selectedConversation"
      class="modal fade show"
      style="display: block; background-color: rgba(0,0,0,0.5);"
      @click.self="closeModal"
    >
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="fas fa-eye me-2"></i>
              Conversation Details
            </h5>
            <button 
              type="button" 
              class="btn-close" 
              @click="closeModal"
            ></button>
          </div>
          <div class="modal-body">
            <div v-if="isLoadingDetails" class="text-center py-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
            </div>
            <div v-else-if="conversationDetails.length === 0" class="text-center py-4">
              <p class="text-muted">No messages found in this conversation.</p>
            </div>
            <div v-else>
              <div 
                v-for="(message, index) in conversationDetails" 
                :key="index"
                class="message-detail"
              >
                <!-- User Message -->
                <div class="message user-message-detail">
                  <div class="message-header">
                    <i class="fas fa-user me-2"></i>
                    <strong>You</strong>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  <div class="message-content">{{ message.query }}</div>
                </div>

                <!-- Bot Response -->
                <div class="message bot-message-detail">
                  <div class="message-header">
                    <i class="fas fa-robot me-2"></i>
                    <strong>Assistant</strong>
                    <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  </div>
                  <div class="message-content" v-html="formatResponse(message.response)"></div>
                  
                  <!-- Sources -->
                  <div v-if="message.sources && message.sources.length > 0" class="message-sources">
                    <details class="sources-details">
                      <summary>
                        <i class="fas fa-book me-1"></i>
                        Sources ({{ message.sources.length }})
                      </summary>
                      <div class="sources-content">
                        <div 
                          v-for="(source, sourceIndex) in message.sources" 
                          :key="sourceIndex"
                          class="source-badge"
                        >
                          {{ source }}
                        </div>
                      </div>
                    </details>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">
              Close
            </button>
            <button 
              type="button" 
              class="btn btn-primary"
              @click="continueConversation"
            >
              <i class="fas fa-arrow-right me-2"></i>
              Continue Conversation
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/services/api'

export default {
  name: 'History',
  setup() {
    const router = useRouter()
    const conversations = ref([])
    const isLoading = ref(false)
    const selectedConversation = ref(null)
    const conversationDetails = ref([])
    const isLoadingDetails = ref(false)

    const loadConversations = async () => {
      isLoading.value = true
      try {
        const data = await apiService.getAllConversations()
        conversations.value = data.conversations || []
      } catch (error) {
        console.error('Error loading conversations:', error)
      } finally {
        isLoading.value = false
      }
    }

    const refreshHistory = () => {
      loadConversations()
    }

    const viewConversation = async (conversationId) => {
      selectedConversation.value = conversationId
      isLoadingDetails.value = true
      try {
        const details = await apiService.getConversationHistory(conversationId)
        conversationDetails.value = details
      } catch (error) {
        console.error('Error loading conversation details:', error)
        conversationDetails.value = []
      } finally {
        isLoadingDetails.value = false
      }
    }

    const deleteConversation = async (conversationId) => {
      if (!confirm('Are you sure you want to delete this conversation?')) {
        return
      }

      try {
        await apiService.deleteConversation(conversationId)
        conversations.value = conversations.value.filter(
          conv => conv.conversation_id !== conversationId
        )
      } catch (error) {
        console.error('Error deleting conversation:', error)
        alert('Failed to delete conversation. Please try again.')
      }
    }

    const closeModal = () => {
      selectedConversation.value = null
      conversationDetails.value = []
    }

    const continueConversation = () => {
      router.push({
        path: '/',
        query: { conversation_id: selectedConversation.value }
      })
    }

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
    }

    const formatTime = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleTimeString()
    }

    const formatResponse = (text) => {
      return text.replace(/\n/g, '<br>')
    }

    onMounted(() => {
      loadConversations()
    })

    return {
      conversations,
      isLoading,
      selectedConversation,
      conversationDetails,
      isLoadingDetails,
      refreshHistory,
      viewConversation,
      deleteConversation,
      closeModal,
      continueConversation,
      formatDate,
      formatTime,
      formatResponse
    }
  }
}
</script>

<style scoped>
.conversations-list {
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  max-height: 600px;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  cursor: pointer;
  transition: background-color 0.2s;
}

.conversation-item:hover {
  background-color: #f8f9fa;
}

.conversation-item:last-child {
  border-bottom: none;
}

.conversation-content {
  flex: 1;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.conversation-id {
  font-weight: 600;
  color: #495057;
}

.conversation-date {
  font-size: 0.875rem;
  color: #6c757d;
}

.conversation-preview {
  color: #6c757d;
  font-size: 0.9rem;
  line-height: 1.4;
}

.conversation-actions {
  margin-left: 1rem;
}

.message-detail {
  margin-bottom: 1.5rem;
}

.message {
  border-radius: 0.5rem;
  padding: 1rem;
  margin-bottom: 0.5rem;
}

.user-message-detail {
  background-color: #e3f2fd;
  border-left: 4px solid #2196f3;
}

.bot-message-detail {
  background-color: #f5f5f5;
  border-left: 4px solid #4caf50;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.message-time {
  margin-left: auto;
  color: #6c757d;
  font-size: 0.8rem;
}

.message-content {
  line-height: 1.5;
  word-wrap: break-word;
}

.message-sources {
  margin-top: 1rem;
}

.sources-details summary {
  cursor: pointer;
  font-size: 0.9rem;
  color: #6c757d;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
}

.sources-content {
  padding: 0.5rem;
  margin-top: 0.5rem;
}

.source-badge {
  display: inline-block;
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  margin: 0.25rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .conversation-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .conversation-date {
    margin-top: 0.25rem;
  }
  
  .modal-dialog {
    margin: 0.5rem;
  }
}
</style> 