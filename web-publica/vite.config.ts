import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Web pública / pantalla del recinto: LAN, puerto :8081 (spec v10 §9).
  server: { port: 8081, strictPort: true },
})
