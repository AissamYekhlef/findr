<template>
  <div class="home">
    <h1>Welcome to Findr</h1>
    <p>Data explorer for CSV, Excel, and database sources.</p>
    <p>Version 0.1.0 - Foundation Setup</p>
  </div>
</template>

<script setup lang="ts">
// Placeholder home page
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: var(--space-6);
  text-align: center;
}

h1 {
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: var(--space-4);
  color: var(--accent);
}

p {
  font-size: 1.125rem;
  color: var(--ink2);
  margin-bottom: var(--space-2);
}
</style>
