import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发: npm run dev (:5173, /api 代理到 Spring Boot :8080)
// 构建: npm run build -> 产物直接落到 backend 静态资源目录, 由 :8080 同源 serving
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://127.0.0.1:8080', changeOrigin: true } }
  },
  build: {
    outDir: '../backend/src/main/resources/static',
    emptyOutDir: true,
    chunkSizeWarningLimit: 1600
  }
})