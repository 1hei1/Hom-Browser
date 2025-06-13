<template>
  <footer class="app-footer">
    <div class="pagination-placeholder">
      <!-- Pagination is handled within specific list views (e.g., ProfilesView) -->
    </div>
    <div class="copyright">
      HomBrowser &copy; 2024. All rights reserved.
    </div>
  </footer>
</template>

<script setup lang="ts">
// No script logic needed for this simple footer yet
</script>

<style scoped>
.app-footer {
  height: 50px; /* Adjusted height */
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  color: rgba(0,0,0,.65);
  background: #f0f2f5;
  border-top: 1px solid #e8e8e8; /* A bit lighter border */
  font-size: 13px; /* Slightly smaller font */
}
.copyright {
  text-align: right;
}
.pagination-placeholder {
  flex-grow: 1; /* Takes up space so copyright is pushed to the right */
}
</style>
