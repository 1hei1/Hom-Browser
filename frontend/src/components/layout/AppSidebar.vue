<template>
  <aside class="app-sidebar">
    <div class="logo">homBrowser</div>
    <nav>
      <ul>
        <li>
          <router-link to="/profiles">浏览器 (Browser) -> 列表 (List)</router-link>
        </li>
        <li>
          <router-link to="/groups">分组管理 (Group Management)</router-link>
        </li>
        <li>
          <router-link to="/plugins">插件管理 (Plugin Management)</router-link>
        </li>
        <li>
          <router-link to="/proxies">代理管理 (Proxy Management)</router-link>
        </li>
        <li>
          <router-link to="/api-docs">API列表 (API List)</router-link>
        </li>
      </ul>
    </nav>
  </aside>
</template>

<script setup lang="ts">
// Import RouterLink if you are using it explicitly,
// but it's often globally available in Vue Router projects.
// import { RouterLink } from 'vue-router';
</script>

<style scoped>
.app-sidebar {
  width: 220px;
  background-color: #001529;
  color: white;
  height: 100vh;
  padding: 15px;
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* Prevent sidebar from shrinking */
}
.logo {
  font-size: 1.5em;
  font-weight: bold;
  text-align: center;
  margin-bottom: 20px;
  padding: 10px 0;
  border-bottom: 1px solid #000c17;
}
nav ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
nav li a {
  display: block;
  padding: 10px 15px;
  color: rgba(255, 255, 255, 0.65);
  text-decoration: none;
  border-radius: 4px;
}
nav li a:hover,
nav li a.router-link-exact-active {
  background-color: #1890ff;
  color: white;
}
</style>
