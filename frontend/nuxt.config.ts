export default defineNuxtConfig({
  ssr: false,
  typescript: {
    strict: true,
    typeCheck: true,
  },
  modules: ['@pinia/nuxt'],
  srcDir: 'app',
  css: ['~/assets/css/tokens.css'],
  app: {
    layoutTransitionDuration: { enter: 0, leave: 0 },
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
});
