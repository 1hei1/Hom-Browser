<template>
  <div class="api-docs-view">
    <h1>API Documentation</h1>
    <p>API documentation (e.g., embedded Swagger UI or link) will be here.</p>
    <p>Backend API docs are typically available at <a href="http://localhost:8000/api/v1/openapi.json" target="_blank">/api/v1/openapi.json</a> (Schema), <a href="http://localhost:8000/docs" target="_blank">/docs</a> (Swagger UI), or <a href="http://localhost:8000/redoc" target="_blank">/redoc</a> (ReDoc) when the backend is running.</p>
    <p>Note: The OpenAPI URL for this project is configured to <a href="http://localhost:8000/api/v1/openapi.json" target="_blank">/api/v1/openapi.json</a>. The UI paths /docs and /redoc are FastAPI defaults if not changed.</p>
  </div>
</template>
<script setup lang="ts"></script>
<style scoped>.api-docs-view { padding: 1em; } a { color: #1890ff; }</style>
