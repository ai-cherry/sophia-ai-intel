import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
  server: {
    port: 3000,
    host: true,
  },
  define: {
    'import.meta.env.VITE_BUILD_ID': JSON.stringify(process.env.VITE_BUILD_ID || 'dev'),
    'import.meta.env.VITE_GIT_COMMIT': JSON.stringify(process.env.VITE_GIT_COMMIT || 'unknown'),
    'import.meta.env.VITE_BUILD_TIMESTAMP': JSON.stringify(new Date().toISOString()),
  },
})

