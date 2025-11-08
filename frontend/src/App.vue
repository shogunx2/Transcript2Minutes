<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <h1 class="app-title">Transcript2Minutes</h1>
    </header>

    <!-- Main Content -->
    <div class="app-container">
      <!-- Left Panel: Input -->
      <div class="panel">
        <div class="panel-header">
          <h1 class="panel-title">Meeting Transcript</h1>
          <p class="panel-subtitle">Paste or type your transcript below</p>
        </div>
        <div class="panel-content">
          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>
          <textarea 
            v-model="transcript"
            class="transcript-input" 
            placeholder="Paste or type meeting transcript here..."
            spellcheck="false"
            @input="handleTextInput"
          ></textarea>
          <div class="word-counter" :class="{ 'over-limit': isOverLimit }">
            {{ wordCount }} / 1500 words
          </div>
          <input 
            ref="fileInput"
            type="file" 
            class="file-input"
            accept=".txt,.pdf,.doc,.docx"
            @change="handleFileSelect"
          />
          <button 
            class="attach-button"
            @click="triggerFileInput"
            :disabled="isProcessing"
          >
            <svg class="attach-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
            {{ isProcessing ? 'Processing...' : 'Attach File' }}
          </button>
          <button 
            class="summarize-button"
            @click="handleSummarize"
            :disabled="!canSummarize || isSummarizing"
          >
            <svg class="summarize-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            {{ isSummarizing ? 'Processing...' : 'Summarize' }}
          </button>
        </div>
      </div>

      <!-- Right Panel: Output -->
      <div class="panel">
        <div class="panel-header">
          <h1 class="panel-title">Summary</h1>
          <p class="panel-subtitle">AI-generated summary will appear here</p>
        </div>
        <div class="panel-content">
          <div class="summary-output">
            {{ summaryText }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      transcript: '',
      summaryText: 'Summary will appear here...',
      errorMessage: '',
      isProcessing: false,
      wordCount: 0,
      isOverLimit: false,
      isSummarizing: false,
      canSummarize: false,
      WORD_LIMIT: 1500
    }
  },
  methods: {
    triggerFileInput() {
      this.$refs.fileInput.click()
    },
    clearError() {
      this.errorMessage = ''
    },
    countWords(text) {
      if (!text || text.trim() === '') return 0
      const words = text.trim().split(/\s+/).filter(word => word.length > 0)
      return words.length
    },
    updateWordCount(text) {
      this.wordCount = this.countWords(text)
      this.isOverLimit = this.wordCount > this.WORD_LIMIT
      this.canSummarize = text.trim().length > 0 && !this.isOverLimit
    },
    handleTextInput() {
      this.updateWordCount(this.transcript)
      
      if (this.isOverLimit) {
        this.showError('Text exceeds 1500 word limit. Please shorten your input.')
      } else {
        this.clearError()
      }
    },
    showError(message) {
      this.errorMessage = message
      setTimeout(() => {
        this.errorMessage = ''
      }, 5000)
    },
    async handleFileSelect(event) {
      this.clearError()
      const file = event.target.files[0]
      
      if (!file) return

      const fileName = file.name.toLowerCase()
      const extension = fileName.substring(fileName.lastIndexOf('.'))

      const validExtensions = ['.txt', '.pdf', '.doc', '.docx']
      if (!validExtensions.includes(extension)) {
        this.showError('Unsupported file type. Please use .txt, .pdf, .doc, or .docx files.')
        this.$refs.fileInput.value = ''
        return
      }

      this.isProcessing = true

      try {
        if (extension === '.txt') {
          await this.handleTextFile(file)
        } else if (extension === '.pdf') {
          await this.handlePdfFile(file)
        } else if (extension === '.doc' || extension === '.docx') {
          this.handleDocFile()
        }
      } catch (error) {
        this.showError(`Error processing file: ${error.message}`)
      } finally {
        this.isProcessing = false
        this.$refs.fileInput.value = ''
      }
    },
    handleTextFile(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        
        reader.onload = (e) => {
          const extractedText = e.target.result
          const count = this.countWords(extractedText)
          
          if (count > this.WORD_LIMIT) {
            this.showError(`Text exceeds 1500 word limit. Please shorten your input. Current count: ${count} words.`)
            reject(new Error('Word limit exceeded'))
          } else {
            this.transcript = extractedText
            this.updateWordCount(extractedText)
            resolve()
          }
        }
        
        reader.onerror = () => {
          reject(new Error('Failed to read text file'))
        }
        
        reader.readAsText(file)
      })
    },
    async handlePdfFile(file) {
      if (typeof pdfjsLib === 'undefined') {
        this.showError('PDF processing library not loaded. Please refresh the page.')
        return
      }

      try {
        const arrayBuffer = await file.arrayBuffer()
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise
        let fullText = ''

        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i)
          const textContent = await page.getTextContent()
          const pageText = textContent.items.map(item => item.str).join(' ')
          fullText += pageText + '\n\n'
        }

        if (fullText.trim()) {
          const extractedText = fullText.trim()
          const count = this.countWords(extractedText)
          
          if (count > this.WORD_LIMIT) {
            this.showError(`Text exceeds 1500 word limit. Please shorten your input. Current count: ${count} words.`)
          } else {
            this.transcript = extractedText
            this.updateWordCount(extractedText)
          }
        } else {
          this.showError('No text found in PDF. The PDF might be image-based.')
        }
      } catch (error) {
        this.showError('Failed to extract text from PDF. The file might be corrupted or encrypted.')
      }
    },
    handleDocFile() {
      this.showError('Microsoft Word files (.doc/.docx) are not supported. Please convert to .txt or .pdf format and try again.')
    },
    async handleSummarize() {
      if (!this.canSummarize || this.isSummarizing) return
      
      this.isSummarizing = true
      this.clearError()
      this.summaryText = 'Generating summary...'

      try {
        const response = await axios.post('http://localhost:5002/summarize', {
          transcript: this.transcript
        })

        let summary = response.data.minutes || response.data.summary || 'Summary generated'
        
        // Remove mock summary prefix if present
        if (summary.includes('📝 Mock Summary')) {
          const keyPointsIndex = summary.indexOf('Key Points:')
          if (keyPointsIndex !== -1) {
            summary = summary.substring(keyPointsIndex)
          }
        }
        
        this.summaryText = summary
      } catch (error) {
        this.summaryText = 'Error generating summary. Please try again.'
        this.showError(error.response?.data?.error || 'Failed to generate summary.')
        console.error('Error:', error)
      } finally {
        this.isSummarizing = false
      }
    }
  }
}
</script>

<style scoped>
/* Design System */
:root {
  --color-white: rgba(255, 255, 255, 1);
  --color-black: rgba(0, 0, 0, 1);
  --color-gray-200: rgba(245, 245, 245, 1);
  --color-gray-300: rgba(167, 169, 169, 1);
  --color-gray-400: rgba(119, 124, 124, 1);
  --color-charcoal-700: rgba(31, 33, 33, 1);
  --color-charcoal-800: rgba(38, 40, 40, 1);
  --color-slate-900: rgba(19, 52, 59, 1);
  --color-teal-300: rgba(50, 184, 198, 1);
  --color-teal-400: rgba(45, 166, 178, 1);
  --color-red-400: rgba(255, 84, 89, 1);

  --color-background: var(--color-charcoal-700);
  --color-surface: var(--color-charcoal-800);
  --color-text: var(--color-gray-200);
  --color-text-secondary: rgba(167, 169, 169, 0.7);
  --color-primary: var(--color-teal-300);
  --color-primary-hover: var(--color-teal-400);

  --font-family-base: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 18px;
  --font-weight-medium: 500;
  --font-weight-semibold: 550;

  --space-8: 8px;
  --space-12: 12px;
  --space-16: 16px;
  --space-24: 24px;
  --space-32: 32px;

  --radius-lg: 12px;
  --radius-xl: 16px;

  --duration-normal: 250ms;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-family-base);
  color: var(--color-text);
  background-color: var(--color-background);
}

#app {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  width: 100%;
  height: 65px;
  background-color: #181A1B;
  border-bottom: 1px solid #2a2d30;
  display: flex;
  align-items: center;
  padding: 0 var(--space-32);
}

.app-title {
  font-size: 1.9rem;
  font-weight: 550;
  color: #E8EAED;
  letter-spacing: 0.75px;
}

.app-container {
  display: flex;
  flex: 1;
  padding: var(--space-24);
  gap: var(--space-24);
  overflow: hidden;
}

.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--color-surface);
  border: 1px solid rgba(119, 124, 124, 0.2);
  border-radius: var(--radius-xl);
  padding: var(--space-32);
  overflow: hidden;
  transition: box-shadow var(--duration-normal);
}

.panel:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.panel-header {
  margin-bottom: var(--space-24);
}

.panel-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
}

.panel-subtitle {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  margin-top: var(--space-8);
}

.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-16);
  overflow: hidden;
}

.transcript-input {
  flex: 1;
  width: 100%;
  padding: var(--space-16);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  color: var(--color-text);
  background-color: var(--color-background);
  border: 1px solid rgba(119, 124, 124, 0.3);
  border-radius: 12px;
  resize: none;
  outline: none;
  transition: border-color var(--duration-normal);
}

.transcript-input:focus {
  border-color: var(--color-primary);
}

.transcript-input::placeholder {
  color: var(--color-text-secondary);
}

.word-counter {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  text-align: right;
  transition: color var(--duration-normal);
}

.word-counter.over-limit {
  color: var(--color-red-400);
  font-weight: var(--font-weight-semibold);
}

.file-input {
  display: none;
}

.attach-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-24);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-slate-900);
  background-color: var(--color-primary);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-normal);
  gap: var(--space-8);
}

.attach-button:hover:not(:disabled) {
  background-color: var(--color-primary-hover);
  transform: translateY(-1px);
}

.attach-button:active:not(:disabled) {
  transform: translateY(0);
}

.attach-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.attach-icon {
  width: 18px;
  height: 18px;
}

.summarize-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-24);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: #FFFFFF;
  background-color: #43A047;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-normal);
  gap: var(--space-8);
  margin-top: var(--space-12);
}

.summarize-button:hover:not(:disabled) {
  background-color: #388E3C;
  transform: translateY(-1px);
}

.summarize-button:active:not(:disabled) {
  background-color: #2E7D32;
  transform: translateY(0);
}

.summarize-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #43A047;
}

.summarize-icon {
  width: 18px;
  height: 18px;
}

.summary-output {
  flex: 1;
  width: 100%;
  padding: var(--space-16);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  background-color: var(--color-background);
  border: 1px solid rgba(119, 124, 124, 0.3);
  border-radius: 12px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.error-message {
  padding: var(--space-12) var(--space-16);
  background-color: rgba(255, 84, 89, 0.15);
  color: var(--color-red-400);
  border: 1px solid rgba(255, 84, 89, 0.25);
  border-radius: 8px;
  font-size: var(--font-size-base);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Custom scrollbar */
.summary-output::-webkit-scrollbar {
  width: 8px;
}

.summary-output::-webkit-scrollbar-track {
  background: transparent;
}

.summary-output::-webkit-scrollbar-thumb {
  background: rgba(119, 124, 124, 0.5);
  border-radius: 4px;
}

.summary-output::-webkit-scrollbar-thumb:hover {
  background: rgba(119, 124, 124, 0.7);
}

/* Responsive */
@media (max-width: 768px) {
  .app-header {
    padding: 0 var(--space-16);
  }

  .app-title {
    font-size: 1.5rem;
  }

  .app-container {
    flex-direction: column;
    padding: var(--space-16);
  }

  .panel {
    padding: var(--space-20);
    min-height: 45vh;
  }
}
</style>
