// vite.config.dev.ts
import { defineConfig, mergeConfig } from 'vite'
import commonConfig from './vite.config.common'

export default mergeConfig(
    commonConfig,
    defineConfig({
        // Development-specific settings
        build: {
            minify: false, // Speeds up build time
            sourcemap: 'inline',
        },
        // server: {
        //     port: 3000,
        // }
    })
)