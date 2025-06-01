<template>
  <div id="app">
    <!-- Left Sidebar -->
    <nav class="sidebar">
      <div class="sidebar-header">
        <h4 class="sidebar-title">
          <i class="fas fa-robot me-2"></i>
          RAG Chatbot
        </h4>
      </div>
      
      <div class="sidebar-nav">
        <router-link 
          to="/" 
          class="nav-item"
          :class="{ active: $route.path === '/' }"
        >
          <i class="fas fa-comments"></i>
          <span>Chat</span>
        </router-link>
        
        <router-link 
          to="/upload" 
          class="nav-item"
          :class="{ active: $route.path === '/upload' }"
        >
          <i class="fas fa-upload"></i>
          <span>Upload</span>
        </router-link>
        
        <router-link 
          to="/history" 
          class="nav-item"
          :class="{ active: $route.path === '/history' }"
        >
          <i class="fas fa-history"></i>
          <span>History</span>
        </router-link>
      </div>

      <!-- Chat Settings (only visible on chat page) -->
      <div v-if="$route.path === '/'" class="sidebar-settings">
        <div class="settings-section">
          <h6 class="settings-title">
            <i class="fas fa-cog me-2"></i>
            Settings
          </h6>
          <div class="setting-item">
            <label for="topK" class="setting-label">Sources (top-k):</label>
            <input
              id="topK"
              :value="chatSettings.topK"
              @input="updateSetting('topK', $event.target.value)"
              type="number"
              class="form-control form-control-sm"
              min="1"
              max="10"
            >
          </div>
          
          <div class="setting-item">
            <label for="typingSpeed" class="setting-label">Typing speed (ms):</label>
            <input
              id="typingSpeed"
              :value="chatSettings.typingSpeed"
              @input="updateSetting('typingSpeed', $event.target.value)"
              type="number"
              class="form-control form-control-sm"
              min="10"
              max="200"
            >
          </div>
        </div>

        <div class="settings-section">
          <h6 class="settings-title">
            <i class="fas fa-info-circle me-2"></i>
            Session Info
          </h6>
          <div class="session-info">
            <div class="info-item">
              <span class="info-label">Conversation ID:</span>
              <code class="info-value">{{ chatSettings.conversationId?.substring(0, 8) }}...</code>
            </div>
            <div class="info-item">
              <span class="info-label">Messages:</span>
              <span class="info-value">{{ chatSettings.messageCount }}</span>
            </div>
          </div>
          <button 
            @click="startNewConversation" 
            class="btn btn-sm btn-outline-light w-100 mt-2"
          >
            <i class="fas fa-plus me-1"></i>
            New Chat
          </button>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="footer-item">
          <i class="fas fa-brain"></i>
          <small>AI-Powered</small>
        </div>
      </div>
    </nav>

    <!-- Main Content Area -->
    <main class="main-content">
      <router-view @update-chat-settings="updateChatSettings" @new-conversation="handleNewConversation" />
    </main>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'

export default {
  name: 'App',
  setup() {
    const chatSettings = reactive({
      topK: 5,
      typingSpeed: 50,
      conversationId: null,
      messageCount: 0
    })

    const updateSetting = (key, value) => {
      chatSettings[key] = parseInt(value) || value
      // Emit to chat component if it exists
      const chatComponent = document.querySelector('.chat-component')
      if (chatComponent) {
        chatComponent.dispatchEvent(new CustomEvent('setting-changed', {
          detail: { key, value: chatSettings[key] }
        }))
      }
    }

    const updateChatSettings = (settings) => {
      Object.assign(chatSettings, settings)
    }

    const startNewConversation = () => {
      // Emit to chat component
      const chatComponent = document.querySelector('.chat-component')
      if (chatComponent) {
        chatComponent.dispatchEvent(new CustomEvent('new-conversation'))
      }
    }

    const handleNewConversation = () => {
      chatSettings.conversationId = null
      chatSettings.messageCount = 0
    }

    return {
      chatSettings,
      updateSetting,
      updateChatSettings,
      startNewConversation,
      handleNewConversation
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Sidebar Styles */
.sidebar {
  width: 300px;
  background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.sidebar-header {
  padding: 2rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #ecf0f1;
}

.sidebar-nav {
  padding: 1rem 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  color: #bdc3c7;
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #ecf0f1;
  transform: translateX(5px);
}

.nav-item.active {
  background-color: rgba(52, 152, 219, 0.2);
  color: #3498db;
  border-left-color: #3498db;
}

.nav-item i {
  width: 20px;
  font-size: 1.1rem;
  margin-right: 1rem;
}

.nav-item span {
  font-size: 1rem;
  font-weight: 500;
}

/* Settings in Sidebar */
.sidebar-settings {
  flex: 1;
  padding: 0 1.5rem;
  overflow-y: auto;
}

.settings-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.settings-section:last-child {
  border-bottom: none;
}

.settings-title {
  color: #ecf0f1;
  font-weight: 600;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-label {
  display: block;
  color: #bdc3c7;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

.setting-item .form-control {
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 0.85rem;
}

.setting-item .form-control:focus {
  background-color: rgba(255, 255, 255, 0.15);
  border-color: #3498db;
  box-shadow: 0 0 0 0.2rem rgba(52, 152, 219, 0.25);
  color: white;
}

.session-info {
  margin-bottom: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.info-label {
  color: #bdc3c7;
  font-size: 0.8rem;
}

.info-value {
  color: #ecf0f1;
  font-size: 0.8rem;
  font-weight: 500;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-item {
  display: flex;
  align-items: center;
  color: #95a5a6;
  font-size: 0.9rem;
}

.footer-item i {
  margin-right: 0.5rem;
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: hidden;
  background-color: #f8f9fa;
}

/* Button Styles */
.btn-outline-light {
  color: #bdc3c7;
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-outline-light:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.5);
  color: #ecf0f1;
}

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Sidebar scrollbar */
.sidebar-settings::-webkit-scrollbar {
  width: 6px;
}

.sidebar-settings::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
}

.sidebar-settings::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.sidebar-settings::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

/* Responsive Design */
@media (max-width: 768px) {
  .sidebar {
    width: 70px;
  }
  
  .sidebar-header {
    padding: 1rem 0.5rem;
  }
  
  .sidebar-title {
    font-size: 0;
  }
  
  .sidebar-title i {
    font-size: 1.5rem;
  }
  
  .nav-item span {
    display: none;
  }
  
  .nav-item {
    padding: 1rem 0.5rem;
    justify-content: center;
  }
  
  .nav-item i {
    margin-right: 0;
  }
  
  .sidebar-settings {
    display: none;
  }
  
  .sidebar-footer {
    display: none;
  }
}

@media (max-width: 480px) {
  .sidebar {
    width: 60px;
  }
}

/* Smooth transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style> 