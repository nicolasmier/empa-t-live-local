import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Panel de administración: LAN, puerto :8080 (spec v10 §9).
  server: { port: 8080, strictPort: true },
})
