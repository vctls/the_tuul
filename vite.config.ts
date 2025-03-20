import { defineConfig, ConfigEnv } from 'vite';
import vue from '@vitejs/plugin-vue2';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig((config: ConfigEnv) => {
    const isDev = config.mode === 'development';

    return {
        root: 'frontend',
        plugins: [vue()],
        resolve: {
            alias: {
                '@': resolve(__dirname, './frontend'),
                'vue': 'vue/dist/vue.esm.js',
            },
        },
        define: {
            'process.env.API_HOSTNAME': JSON.stringify(process.env.API_HOSTNAME || ''),
            'process.env.DONATE_URL': JSON.stringify(process.env.DONATE_URL || 'https://ko-fi.com/incidentist')
        },
        build: {
            outDir: 'api/assets/bundles',
            emptyOutDir: true,
            sourcemap: isDev,
            rollupOptions: {
                output: {
                    entryFileNames: '[name]-[hash].js',
                    chunkFileNames: '[name]-[hash].js',
                    assetFileNames: '[name]-[hash].[ext]'
                }
            }
        },
        server: {
            port: 3000
        }
    }
});