// Development proxy keeps frontend requests same-origin and offline.
import { defineConfig } from 'vite';
export default defineConfig({server: {proxy: {'/api': 'http://127.0.0.1:8000'}}, build:{rollupOptions:{output:{manualChunks:{charts:['recharts'],icons:['lucide-react']}}}}, test: {environment: 'jsdom', globals: true}});
