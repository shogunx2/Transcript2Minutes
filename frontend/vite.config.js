import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    strictPort: true,
    proxy: {
      '/api/summarize': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        pathRewrite: {
          '^/api/summarize': '/summarize'
        },
        ws: true
      },
      '/api': {
        target: 'http://localhost:5002',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
