<template>
  <div class="chat-page chat-component">
    <div class="chat-container">
      <!-- Chat Header -->
      <div class="chat-header">
        <h4 class="mb-0">
          <i class="fas fa-comments text-primary me-2"></i>
          Chat with your documents
        </h4>
        <div class="chat-status">
          <span v-if="isWaitingForResponse" class="status-indicator typing">
            <i class="fas fa-circle"></i>
            AI is typing...
          </span>
          <span v-else class="status-indicator ready">
            <i class="fas fa-circle"></i>
            Ready
          </span>
        </div>
      </div>

      <!-- Chat Messages -->
      <div class="chat-messages" ref="messagesContainer">
        <div v-if="messages.length === 0" class="text-center text-muted py-5">
          <i class="fas fa-robot fa-3x mb-3"></i>
          <h5>Welcome to RAG Chatbot!</h5>
          <p>Upload a PDF document and start asking questions about it.</p>
        </div>

        <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
          <!-- User Message -->
          <div v-if="message.isUser" class="message user-message">
            <div class="message-avatar">
              <i class="fas fa-user"></i>
            </div>
            <div class="message-content">
              <div class="message-bubble user-bubble">
                {{ message.query }}
              </div>
              <div class="message-time">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>

          <!-- Bot Response -->
          <div v-else class="message bot-message">
            <div class="message-avatar">
              <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
              <div class="message-bubble bot-bubble">
                <div 
                  v-if="message.isTyping" 
                  class="typing-text"
                  v-html="message.displayText"
                ></div>
                <div v-else v-html="formatResponse(message.response)"></div>
              </div>
              <div class="message-time" v-if="!message.isTyping">
                {{ formatTime(message.timestamp) }}
              </div>
            </div>
          </div>

          <!-- Sources (only for bot messages) -->
          <div v-if="!message.isUser && message.sources && message.sources.length > 0 && !message.isTyping" class="sources-section">
            <button 
              class="btn btn-sm btn-outline-secondary"
              type="button"
              @click="toggleSources(index)"
            >
              <i class="fas fa-book me-1"></i>
              Sources ({{ message.sources.length }})
              <i :class="['fas', 'ms-1', showSources[index] ? 'fa-chevron-up' : 'fa-chevron-down']"></i>
            </button>
            
            <div v-if="showSources[index]" class="sources-list mt-2">
              <div v-for="(source, sourceIndex) in message.sources" :key="sourceIndex" class="source-item">
                <div class="source-header">
                  <strong>{{ source.source }}</strong>
                  <span v-if="source.page" class="badge bg-secondary ms-2">Page {{ source.page }}</span>
                  <span class="badge bg-primary ms-2">Score: {{ (source.score * 100).toFixed(1) }}%</span>
                </div>
                <div class="source-text">{{ source.text.substring(0, 200) }}...</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading indicator for initial response -->
        <div v-if="isWaitingForResponse" class="message bot-message">
          <div class="message-avatar">
            <i class="fas fa-robot"></i>
          </div>
          <div class="message-content">
            <div class="message-bubble bot-bubble">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input -->
      <div class="chat-input-container">
        <form @submit.prevent="sendMessage" class="chat-input-form">
          <div class="input-group">
            <input
              v-model="currentMessage"
              type="text"
              class="form-control"
              placeholder="Ask a question about your documents..."
              :disabled="isWaitingForResponse"
              ref="messageInput"
            >
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="!currentMessage.trim() || isWaitingForResponse"
            >
              <i class="fas fa-paper-plane"></i>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Web Search Permission Modal -->
    <div 
      v-if="showWebSearchModal" 
      class="modal-overlay" 
      @click="handleWebSearchDecision(false)"
    >
      <div class="permission-modal" @click.stop>
        <div class="modal-header">
          <h5 class="modal-title">
            <i class="fas fa-globe me-2"></i>
            Web Search Request
          </h5>
          <button 
            type="button" 
            class="btn-close" 
            @click="handleWebSearchDecision(false)"
          ></button>
        </div>
        <div class="modal-body">
          <p>I couldn't find sufficient information in your uploaded documents to answer your question.</p>
          <p><strong>Would you like me to search the web for additional information?</strong></p>
          <div class="search-query-preview">
            <small class="text-muted">Search query:</small>
            <div class="query-text">{{ pendingSearchQuery }}</div>
          </div>
        </div>
        <div class="modal-footer">
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="handleWebSearchDecision(false)"
          >
            <i class="fas fa-times me-1"></i>
            No, thanks
          </button>
          <button 
            type="button" 
            class="btn btn-primary" 
            @click="handleWebSearchDecision(true)"
          >
            <i class="fas fa-search me-1"></i>
            Yes, search web
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, nextTick, onMounted, onUnmounted } from 'vue'
import { apiService } from '@/services/api'
import { v4 as uuidv4 } from 'uuid'

export default {
  name: 'Chat',
  emits: ['update-chat-settings', 'new-conversation'],
  setup(props, { emit }) {
    const messages = ref([])
    const currentMessage = ref('')
    const isWaitingForResponse = ref(false)
    const conversationId = ref(null)
    const topK = ref(5)
    const typingSpeed = ref(50)
    const showSources = reactive({})
    const messagesContainer = ref(null)
    const messageInput = ref(null)
    const showWebSearchModal = ref(false)
    const pendingSearchQuery = ref('')

    const sendMessage = async () => {
      if (!currentMessage.value.trim()) return

      const userMessage = currentMessage.value.trim()
      const timestamp = new Date()
      
      // Add user message immediately
      const userMessageObj = {
        query: userMessage,
        response: '',
        sources: [],
        timestamp: timestamp,
        conversation_id: conversationId.value,
        isTyping: false,
        isUser: true
      }
      
      messages.value.push(userMessageObj)
      currentMessage.value = ''
      isWaitingForResponse.value = true
      scrollToBottom()
      updateParentSettings()

      try {
        // Send query to backend
        const response = await apiService.sendQuery(
          userMessage, 
          conversationId.value, 
          topK.value
        )

        // Update conversation ID if needed
        if (response.conversation_id) {
          conversationId.value = response.conversation_id
        }

        // Stop loading indicator
        isWaitingForResponse.value = false

        // Check if web search is needed
        if (response.needs_web_search && response.search_query) {
          pendingSearchQuery.value = response.search_query
          showWebSearchModal.value = true
          
          // Store the response temporarily (without typewriter effect)
          const botMessage = {
            query: userMessage,
            response: response.response,
            sources: response.sources || [],
            timestamp: new Date(),
            conversation_id: response.conversation_id,
            isTyping: false,
            isUser: false,
            needsWebSearch: true
          }
          
          messages.value.push(botMessage)
          scrollToBottom()
          updateParentSettings()
        } else {
          // Normal response with typewriter effect
          const botMessage = {
            query: userMessage,
            response: response.response,
            sources: response.sources || [],
            timestamp: new Date(),
            conversation_id: response.conversation_id,
            isTyping: true,
            displayText: '',
            isUser: false
          }

          messages.value.push(botMessage)
          scrollToBottom()
          
          // Start typewriter effect
          await typewriterEffect(botMessage, response.response)
          updateParentSettings()
        }

      } catch (error) {
        console.error('Error sending message:', error)
        isWaitingForResponse.value = false
        
        // Add error message as a separate bot message
        const errorMessage = {
          query: userMessage,
          response: `Sorry, I encountered an error: ${error.message}`,
          sources: [],
          timestamp: new Date(),
          conversation_id: conversationId.value,
          isTyping: false,
          isUser: false
        }
        
        messages.value.push(errorMessage)
        updateParentSettings()
        scrollToBottom()
      }
    }

    const typewriterEffect = async (messageObj, fullText) => {
      const words = fullText.split(' ')
      let currentText = ''
      
      for (let i = 0; i < words.length; i++) {
        currentText += (i > 0 ? ' ' : '') + words[i]
        messageObj.displayText = formatResponse(currentText)
        
        // Force reactivity update
        messages.value = [...messages.value]
        
        // Scroll to bottom as text appears
        await nextTick()
        scrollToBottom()
        
        // Wait before next word
        await new Promise(resolve => setTimeout(resolve, typingSpeed.value))
      }
      
      // Mark typing as complete
      messageObj.isTyping = false
      messages.value = [...messages.value]
      await nextTick()
      scrollToBottom()
    }

    const startNewConversation = () => {
      conversationId.value = uuidv4()
      messages.value = []
      Object.keys(showSources).forEach(key => delete showSources[key])
      updateParentSettings()
      emit('new-conversation')
    }

    const updateParentSettings = () => {
      // Count only user messages for the message count
      const userMessageCount = messages.value.filter(msg => msg.isUser).length
      
      emit('update-chat-settings', {
        topK: topK.value,
        typingSpeed: typingSpeed.value,
        conversationId: conversationId.value,
        messageCount: userMessageCount
      })
    }

    const toggleSources = (index) => {
      showSources[index] = !showSources[index]
    }

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleTimeString()
    }

    const formatResponse = (text) => {
      return text.replace(/\n/g, '<br>')
    }

    const scrollToBottom = () => {
      nextTick(() => {
        const container = messagesContainer.value
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }

    // Listen for settings changes from sidebar
    const handleSettingChange = (event) => {
      const { key, value } = event.detail
      if (key === 'topK') {
        topK.value = value
      } else if (key === 'typingSpeed') {
        typingSpeed.value = value
      }
    }

    // Listen for new conversation from sidebar
    const handleNewConversation = () => {
      startNewConversation()
    }

    const handleWebSearchDecision = async (approved) => {
      showWebSearchModal.value = false
      
      if (!approved) {
        // User declined web search - show a message
        const declineMessage = {
          query: '',
          response: 'I understand. I can only provide information based on your uploaded documents. Feel free to ask other questions!',
          sources: [],
          timestamp: new Date(),
          conversation_id: conversationId.value,
          isTyping: false,
          isUser: false
        }
        
        messages.value.push(declineMessage)
        scrollToBottom()
        updateParentSettings()
        return
      }

      // User approved web search
      isWaitingForResponse.value = true
      
      try {
        const response = await apiService.performWebSearch(conversationId.value, true)
        
        isWaitingForResponse.value = false
        
        // Replace the last bot message with web search results
        const lastBotMessageIndex = messages.value.length - 1
        if (lastBotMessageIndex >= 0 && !messages.value[lastBotMessageIndex].isUser) {
          // Create new message with typewriter effect
          const updatedMessage = {
            ...messages.value[lastBotMessageIndex],
            response: response.response,
            sources: response.sources || [],
            isTyping: true,
            displayText: '',
            needsWebSearch: false
          }
          
          messages.value[lastBotMessageIndex] = updatedMessage
          scrollToBottom()
          
          // Start typewriter effect for the updated response
          await typewriterEffect(updatedMessage, response.response)
          updateParentSettings()
        }
        
      } catch (error) {
        console.error('Error performing web search:', error)
        isWaitingForResponse.value = false
        
        // Add error message
        const errorMessage = {
          query: '',
          response: `Sorry, web search failed: ${error.message}`,
          sources: [],
          timestamp: new Date(),
          conversation_id: conversationId.value,
          isTyping: false,
          isUser: false
        }
        
        messages.value.push(errorMessage)
        updateParentSettings()
        scrollToBottom()
      }
    }

    onMounted(() => {
      // Initialize
      startNewConversation()
      nextTick(() => {
        messageInput.value?.focus()
      })

      // Add event listeners for sidebar communication
      const element = document.querySelector('.chat-component')
      if (element) {
        element.addEventListener('setting-changed', handleSettingChange)
        element.addEventListener('new-conversation', handleNewConversation)
      }
    })

    onUnmounted(() => {
      // Clean up event listeners
      const element = document.querySelector('.chat-component')
      if (element) {
        element.removeEventListener('setting-changed', handleSettingChange)
        element.removeEventListener('new-conversation', handleNewConversation)
      }
    })

    return {
      messages,
      currentMessage,
      isWaitingForResponse,
      conversationId,
      topK,
      typingSpeed,
      showSources,
      messagesContainer,
      messageInput,
      sendMessage,
      startNewConversation,
      toggleSources,
      formatTime,
      formatResponse,
      scrollToBottom,
      showWebSearchModal,
      pendingSearchQuery,
      handleWebSearchDecision
    }
  }
}
</script>

<style scoped>
.chat-page {
  height: 100vh;
  background-color: #f8f9fa;
}

.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.chat-header {
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chat-status {
  display: flex;
  align-items: center;
  font-size: 0.875rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-indicator.typing {
  color: #f39c12;
}

.status-indicator.ready {
  color: #27ae60;
}

.status-indicator i {
  font-size: 0.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
  background: white;
}

.message-wrapper {
  margin-bottom: 2rem;
}

.message {
  display: flex;
  margin-bottom: 1rem;
  animation: messageSlide 0.3s ease-out;
}

@keyframes messageSlide {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.user-message {
  justify-content: flex-end;
}

.bot-message {
  justify-content: flex-start;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  margin: 0 1rem;
}

.user-message .message-avatar {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  order: 2;
}

.bot-message .message-avatar {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
}

.message-content {
  max-width: 80%;
}

.message-bubble {
  padding: 1rem 1.5rem;
  border-radius: 1.5rem;
  word-wrap: break-word;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: relative;
}

.user-bubble {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-bottom-right-radius: 0.5rem;
}

.bot-bubble {
  background: #f8f9fa;
  color: #333;
  border: 1px solid #e9ecef;
  border-bottom-left-radius: 0.5rem;
}

.message-time {
  font-size: 0.75rem;
  color: #495057;
  text-align: center;
  margin-top: 0.5rem;
  font-weight: 500;
}

.typing-text {
  min-height: 1.2em;
}

.sources-section {
  margin-left: 3rem;
  margin-top: 1rem;
}

.sources-section .btn-outline-secondary {
  background: white;
  border-color: #6c757d;
  color: #6c757d;
  font-weight: 500;
}

.sources-section .btn-outline-secondary:hover {
  background: #6c757d;
  border-color: #6c757d;
  color: white;
}

.source-item {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0.5rem;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.source-header {
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
  color: #495057;
}

.source-text {
  font-size: 0.8rem;
  color: #6c757d;
  line-height: 1.4;
}

.chat-input-container {
  padding: 1.5rem 2rem;
  background: white;
  border-top: 1px solid #e9ecef;
}

.chat-input-form .form-control {
  border-radius: 25px;
  padding: 0.75rem 1.5rem;
  border: 2px solid #e9ecef;
  font-size: 1rem;
}

.chat-input-form .form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.chat-input-form .btn {
  border-radius: 50%;
  width: 50px;
  height: 50px;
  margin-left: 0.5rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

/* Typing indicator animation */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.typing-indicator span {
  display: inline-block;
  width: 8px;
  height: 8px;
  background-color: #6c757d;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .chat-header {
    padding: 1rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .chat-messages {
    padding: 1rem;
  }
  
  .chat-input-container {
    padding: 1rem;
  }
  
  .message-content {
    max-width: 85%;
  }
  
  .sources-section {
    margin-left: 1rem;
  }
}

/* Web Search Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1050;
  backdrop-filter: blur(3px);
}

.permission-modal {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  color: #495057;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f8f9fa;
  color: #495057;
}

.btn-close::before {
  content: '×';
}

.modal-body {
  padding: 1rem 1.5rem;
}

.modal-body p {
  margin-bottom: 1rem;
  color: #495057;
  line-height: 1.5;
}

.search-query-preview {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 0.5rem;
  padding: 1rem;
  margin-top: 1rem;
}

.query-text {
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 0.9rem;
  color: #495057;
  background: white;
  padding: 0.5rem;
  border-radius: 0.25rem;
  border: 1px solid #dee2e6;
  margin-top: 0.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem 1.5rem 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.modal-footer .btn {
  border-radius: 0.5rem;
  padding: 0.5rem 1.5rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .permission-modal {
    width: 95%;
  }
  
  .modal-footer {
    flex-direction: column;
  }
  
  .modal-footer .btn {
    width: 100%;
  }
}
</style> 