<template>
  <div id="app-layout">
    <AppSidebar />
    <div class="main-wrapper">
      <AppHeader />
      <main class="content-area">
        <router-view />
      </main>
      <AppFooter />
    </div>
  </div>
</template>

<script setup lang="ts">
import AppHeader from './components/layout/AppHeader.vue';
import AppSidebar from './components/layout/AppSidebar.vue';
import AppFooter from './components/layout/AppFooter.vue';
// RouterView is globally available if vue-router is installed and set up correctly in main.ts
// import { RouterView } from 'vue-router';
</script>

<style>
/* Global styles */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app { /* This is the mount point in index.html */
  height: 100%;
}

#app-layout {
  display: flex;
  height: 100vh; /* Ensure full viewport height */
  overflow: hidden; /* Prevent scrollbars on layout itself */
}

.main-wrapper {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  /* Allow main content area + footer to scroll if they overflow vertically */
  /* overflow-y: auto; - This might cause double scrollbars if content-area also has it */
}

.content-area {
  flex-grow: 1;
  padding: 20px;
  background-color: #fff;
  overflow-y: auto; /* Allow content itself to scroll if it overflows */
  /* color: #333;  Ensure text is visible on white background */
}

/* Reset default browser styles that might interfere */
ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

a {
  text-decoration: none;
}
</style>
