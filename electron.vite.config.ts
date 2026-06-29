import { resolve } from 'path'
import { defineConfig } from 'electron-vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  main: {
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'app/main/index.ts')
        }
      }
    }
  },
  preload: {
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'app/preload/index.ts')
        }
      }
    }
  },
  renderer: {
    root: 'app/renderer',
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'app/renderer/index.html')
        }
      }
    },
    plugins: [svelte()]
  }
})
