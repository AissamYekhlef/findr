export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  ssr: false,
  modules: ['@pinia/nuxt', '@nuxt/eslint'],
  css: ['~/assets/css/tokens.css'],
  typescript: {
    typeCheck: false,
  },
  nitro: {
    prerender: {
      crawlLinks: false,
    },
  },
  devServer: {
    host: '0.0.0.0',
    port: 3000,
  },
})