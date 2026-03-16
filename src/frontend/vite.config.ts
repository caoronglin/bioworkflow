import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    vue(),
    // 构建分析工具（生产环境禁用）
    visualizer({
      open: false,
      gzipSize: true,
      brotliSize: true,
      emitFile: true,
      filename: 'dist/stats.html',
    }),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
  // 依赖预优化
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'axios',
      'element-plus',
      '@element-plus/icons-vue',
      '@vueuse/core',
      'pinia',
      '@vue-flow/core',
      'monaco-editor',
      '@monaco-editor/loader',
    ],
    exclude: ['@vue-flow/core'], // 大型库不预优化
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks: {
          // 核心框架
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // HTTP 和工具库
          'utils-vendor': ['axios', '@vueuse/core', 'lodash-es', 'dayjs'],
          // UI 组件库（单独分包）
          'element-plus': ['element-plus'],
          'element-icons': ['@element-plus/icons-vue'],
          // 工作流编辑器
          'vue-flow': [
            '@vue-flow/core',
            '@vue-flow/background',
            '@vue-flow/controls',
            '@vue-flow/minimap',
            '@vue-flow/additional-components',
          ],
          // Monaco Editor（大型组件，单独分包）
          'monaco': ['monaco-editor', '@monaco-editor/loader'],
          // 可视化
          'charts': ['echarts', 'vue-echarts'],
          // Markdown 处理
          'markdown': ['marked', 'dompurify'],
          // 其他工具
          'misc': ['nprogress', 'splitpanes', 'vue3-perfect-scrollbar'],
        },
        // 文件名哈希
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]',
        // 内联小资源
        assetFileNames: (assetInfo) => {
          const name = assetInfo.name || ''
          // 小图片转 base64
          if (/\.(png|jpe?g|gif|svg|webp)$/i.test(name)) {
            return 'assets/images/[name].[hash][extname]'
          }
          // 字体文件
          if (/\.(woff2?|eot|ttf|otf)$/i.test(name)) {
            return 'assets/fonts/[name].[hash][extname]'
          }
          return 'assets/[name].[hash][ext]'
        },
      },
    },
  },
  // Terser 压缩优化
  esbuild: {
    drop: process.env.NODE_ENV === 'production' ? ['console', 'debugger'] : [],
  },
})
