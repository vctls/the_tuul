// https://vitejs.dev/config/

import { defineConfig, UserConfig } from 'vite'
import vue from '@vitejs/plugin-vue2'
import { resolve } from 'path'

const commonConfig: UserConfig = {
    root: resolve(__dirname, './frontend'),
    // URL prefix for assets, should be the same as DJANGO_VITE.static_url_prefix
    // in settings.py
    base: '/bundles/',
    // Env vars prefixed with TUUL_ will be available in the frontend
    envDir: process.cwd(),
    envPrefix: 'TUUL_',
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