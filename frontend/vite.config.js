import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      // Browser talks to :5173, Vite forwards /api -> FastAPI
      // Same-origin from the browser's POV -> no CORS at all
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})