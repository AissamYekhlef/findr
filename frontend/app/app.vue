<template>
  <div class="app">
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useThemeStore } from '~/stores/theme';

const themeStore = useThemeStore();

onMounted(() => {
  themeStore.loadTheme();
});
</script>

<style scoped>
.app {
  width: 100%;
  min-height: 100vh;
  background-color: var(--ground);
  color: var(--ink);
}
</style>
