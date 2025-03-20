// https://vitejs.dev/config/

import { defineConfig, UserConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'

const commonConfig: UserConfig = {
    root: resolve(__dirname, './frontend'),
    base: '/bundles/',
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, './frontend'),
            'vue': 'vue/dist/vue.esm.js',
        },
    },
    build: {
        outDir: '../api/assets/bundles',
        emptyOutDir: true,
        manifest: true,
        sourcemap: false,
        rollupOptions: {
            input: resolve(__dirname, 'frontend/index.ts'),
        }
    }
}

export default commonConfig