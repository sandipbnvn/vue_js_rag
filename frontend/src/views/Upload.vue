<template>
  <div class="upload-page">
    <div class="upload-header">
      <h4 class="mb-0">
        <i class="fas fa-upload me-2"></i>
        Upload PDF Documents
      </h4>
      <p class="text-muted mb-0">
        Upload your documents to enable AI-powered conversations
      </p>
    </div>

    <div class="upload-content">
      <div class="upload-container">
        <!-- Upload Area -->
        <div 
          class="upload-area"
          :class="{ 'drag-over': isDragOver, 'uploading': isUploading }"
          @dragover.prevent="handleDragOver"
          @dragleave.prevent="handleDragLeave"
          @drop.prevent="handleDrop"
          @click="triggerFileInput"
        >
          <div class="upload-content-inner">
            <div v-if="!isUploading">
              <i class="fas fa-cloud-upload-alt fa-4x text-primary mb-3"></i>
              <h5>Drag & Drop PDF Files Here</h5>
              <p class="text-muted">or click to browse files</p>
              <div class="mt-3">
                <span class="badge bg-info me-2">
                  <i class="fas fa-file-pdf me-1"></i>
                  PDF Only
                </span>
                <span class="badge bg-secondary">
                  <i class="fas fa-weight-hanging me-1"></i>
                  Max 50MB
                </span>
              </div>
            </div>
            <div v-else class="text-center">
              <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Uploading...</span>
              </div>
              <h5>Processing your document...</h5>
              <p class="text-muted">{{ uploadStatus }}</p>
              <div class="progress" style="height: 10px;">
                <div 
                  class="progress-bar progress-bar-striped progress-bar-animated"
                  role="progressbar"
                  :style="{ width: uploadProgress + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".pdf"
          @change="handleFileSelect"
          style="display: none"
          multiple
        >

        <!-- Upload Results -->
        <div v-if="uploadResults.length > 0" class="results-section">
          <h6 class="results-title">
            <i class="fas fa-check-circle text-success me-2"></i>
            Upload Results
          </h6>
          <div class="upload-results">
            <div 
              v-for="(result, index) in uploadResults" 
              :key="index"
              class="result-item"
              :class="{ 'success': result.success, 'error': !result.success }"
            >
              <div class="result-icon">
                <i :class="result.success ? 'fas fa-check-circle text-success' : 'fas fa-exclamation-triangle text-danger'"></i>
              </div>
              <div class="result-content">
                <div class="result-filename">{{ result.filename }}</div>
                <div class="result-message">{{ result.message }}</div>
                <div v-if="result.success && result.chunks_count" class="result-stats">
                  <span class="badge bg-primary">{{ result.chunks_count }} chunks</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button 
            @click="$router.push('/')" 
            class="btn btn-success me-3"
            :disabled="uploadResults.length === 0"
          >
            <i class="fas fa-comments me-2"></i>
            Start Chatting
          </button>
          <button 
            @click="clearResults" 
            class="btn btn-outline-secondary"
            :disabled="uploadResults.length === 0"
          >
            <i class="fas fa-trash me-2"></i>
            Clear Results
          </button>
        </div>
      </div>

      <!-- Instructions Sidebar -->
      <div class="instructions-panel">
        <div class="instructions-content">
          <h6 class="instructions-title">
            <i class="fas fa-info-circle me-2"></i>
            How it works
          </h6>
          <div class="instruction-steps">
            <div class="step">
              <div class="step-number">1</div>
              <div class="step-content">
                <h6>Upload Documents</h6>
                <p>Drag and drop or click to upload your PDF files</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">2</div>
              <div class="step-content">
                <h6>AI Processing</h6>
                <p>The system extracts text and creates vector embeddings</p>
              </div>
            </div>
            <div class="step">
              <div class="step-number">3</div>
              <div class="step-content">
                <h6>Start Chatting</h6>
                <p>Ask questions and get intelligent answers based on your documents</p>
              </div>
            </div>
          </div>

          <div class="features-list">
            <h6 class="features-title">Features</h6>
            <ul>
              <li><i class="fas fa-check text-success me-2"></i>Multiple PDF support</li>
              <li><i class="fas fa-check text-success me-2"></i>Intelligent text chunking</li>
              <li><i class="fas fa-check text-success me-2"></i>Vector similarity search</li>
              <li><i class="fas fa-check text-success me-2"></i>Source attribution</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { apiService } from '@/services/api'

export default {
  name: 'Upload',
  setup() {
    const isDragOver = ref(false)
    const isUploading = ref(false)
    const uploadProgress = ref(0)
    const uploadStatus = ref('')
    const uploadResults = ref([])
    const fileInput = ref(null)

    const handleDragOver = (event) => {
      event.preventDefault()
      isDragOver.value = true
    }

    const handleDragLeave = (event) => {
      event.preventDefault()
      isDragOver.value = false
    }

    const handleDrop = (event) => {
      event.preventDefault()
      isDragOver.value = false
      const files = Array.from(event.dataTransfer.files)
      processFiles(files)
    }

    const triggerFileInput = () => {
      if (!isUploading.value) {
        fileInput.value?.click()
      }
    }

    const handleFileSelect = (event) => {
      const files = Array.from(event.target.files)
      processFiles(files)
    }

    const processFiles = async (files) => {
      if (files.length === 0) return

      // Filter PDF files
      const pdfFiles = files.filter(file => file.type === 'application/pdf')
      
      if (pdfFiles.length === 0) {
        alert('Please select PDF files only.')
        return
      }

      // Check file sizes (50MB limit)
      const oversizedFiles = pdfFiles.filter(file => file.size > 50 * 1024 * 1024)
      if (oversizedFiles.length > 0) {
        alert(`Files too large: ${oversizedFiles.map(f => f.name).join(', ')}. Maximum size is 50MB.`)
        return
      }

      isUploading.value = true
      uploadProgress.value = 0
      
      for (let i = 0; i < pdfFiles.length; i++) {
        const file = pdfFiles[i]
        uploadStatus.value = `Processing ${file.name} (${i + 1}/${pdfFiles.length})`
        
        try {
          const result = await apiService.uploadPDF(file)
          uploadResults.value.push({
            filename: file.name,
            success: true,
            message: result.message,
            chunks_count: result.chunks_count,
            document_id: result.document_id
          })
        } catch (error) {
          uploadResults.value.push({
            filename: file.name,
            success: false,
            message: error.message || 'Upload failed'
          })
        }
        
        uploadProgress.value = ((i + 1) / pdfFiles.length) * 100
      }

      isUploading.value = false
      uploadStatus.value = ''
      
      // Reset file input
      if (fileInput.value) {
        fileInput.value.value = ''
      }
    }

    const clearResults = () => {
      uploadResults.value = []
    }

    return {
      isDragOver,
      isUploading,
      uploadProgress,
      uploadStatus,
      uploadResults,
      fileInput,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      triggerFileInput,
      handleFileSelect,
      clearResults
    }
  }
}
</script>

<style scoped>
.upload-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f8f9fa;
}

.upload-header {
  padding: 1.5rem 2rem;
  background: white;
  border-bottom: 1px solid #e9ecef;
}

.upload-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.upload-container {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  max-width: calc(100vw - 350px);
}

.upload-area {
  border: 3px dashed #dee2e6;
  border-radius: 1rem;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  margin-bottom: 2rem;
}

.upload-area:hover {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05), rgba(118, 75, 162, 0.05));
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.upload-area.drag-over {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  transform: scale(1.02);
}

.upload-area.uploading {
  cursor: not-allowed;
  opacity: 0.8;
}

.upload-content-inner {
  pointer-events: none;
}

.results-section {
  margin-bottom: 2rem;
}

.results-title {
  color: #495057;
  font-weight: 600;
  margin-bottom: 1rem;
}

.upload-results {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  align-items: flex-start;
  padding: 1rem;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s;
}

.result-item:hover {
  background-color: #f8f9fa;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item.success {
  border-left: 4px solid #28a745;
}

.result-item.error {
  border-left: 4px solid #dc3545;
}

.result-icon {
  margin-right: 1rem;
  font-size: 1.2rem;
}

.result-content {
  flex: 1;
}

.result-filename {
  font-weight: 600;
  margin-bottom: 0.25rem;
  color: #495057;
}

.result-message {
  font-size: 0.875rem;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.result-stats .badge {
  font-size: 0.75rem;
}

.action-buttons {
  text-align: center;
  padding: 1rem 0;
}

.action-buttons .btn {
  border-radius: 25px;
  padding: 0.75rem 2rem;
  font-weight: 500;
}

.instructions-panel {
  width: 350px;
  background: white;
  border-left: 1px solid #e9ecef;
  overflow-y: auto;
}

.instructions-content {
  padding: 2rem;
}

.instructions-title {
  color: #495057;
  font-weight: 600;
  margin-bottom: 1.5rem;
}

.instruction-steps {
  margin-bottom: 2rem;
}

.step {
  display: flex;
  align-items: flex-start;
  margin-bottom: 1.5rem;
}

.step-number {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.875rem;
  margin-right: 1rem;
  flex-shrink: 0;
}

.step-content h6 {
  margin-bottom: 0.25rem;
  color: #495057;
  font-weight: 600;
}

.step-content p {
  margin: 0;
  font-size: 0.875rem;
  color: #6c757d;
  line-height: 1.4;
}

.features-list {
  padding-top: 1.5rem;
  border-top: 1px solid #e9ecef;
}

.features-title {
  color: #495057;
  font-weight: 600;
  margin-bottom: 1rem;
}

.features-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features-list li {
  padding: 0.5rem 0;
  font-size: 0.875rem;
  color: #6c757d;
}

.progress {
  background-color: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

/* Responsive Design */
@media (max-width: 1200px) {
  .instructions-panel {
    width: 300px;
  }
  
  .upload-container {
    max-width: calc(100vw - 300px);
  }
}

@media (max-width: 992px) {
  .upload-content {
    flex-direction: column;
  }
  
  .instructions-panel {
    width: 100%;
    height: 250px;
    border-left: none;
    border-top: 1px solid #e9ecef;
  }
  
  .upload-container {
    max-width: 100%;
  }
  
  .instructions-content {
    padding: 1rem;
  }
  
  .instruction-steps {
    display: flex;
    gap: 1rem;
  }
  
  .step {
    flex: 1;
    flex-direction: column;
    text-align: center;
    margin-bottom: 0;
  }
  
  .step-number {
    margin: 0 auto 0.5rem auto;
  }
}

@media (max-width: 768px) {
  .upload-header {
    padding: 1rem;
  }
  
  .upload-container {
    padding: 1rem;
  }
  
  .upload-area {
    padding: 2rem 1rem;
  }
  
  .upload-area .fa-4x {
    font-size: 2.5rem !important;
  }
  
  .action-buttons .btn {
    display: block;
    width: 100%;
    margin-bottom: 0.5rem;
  }
  
  .instruction-steps {
    flex-direction: column;
  }
}
</style> 