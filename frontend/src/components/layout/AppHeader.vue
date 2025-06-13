<template>
  <header class="app-header">
    <div class="breadcrumbs">Breadcrumbs > Here</div>
    <div class="user-menu">
      <span>Notifications</span> | <span>User Avatar</span>
    </div>
  </header>
</template>

<script setup lang="ts">
</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background-color: #f0f2f5;
  border-bottom: 1px solid #d9d9d9;
}
.user-menu span {
  margin-left: 15px;
}
</style>
