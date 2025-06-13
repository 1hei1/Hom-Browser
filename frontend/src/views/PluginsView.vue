<template>
  <div class="plugins-view">
    <h1>Plugin Management</h1>

    <div v-if="loading" class="loading-container">
      <p>Loading plugins...</p>
    </div>

    <div v-else-if="error && !error.includes('not yet implemented')" class="error-container"> <!-- Hide generic error if it's the 501 message -->
      <p style="color: red;">Error loading plugins: {{ error }}</p>
      <button @click="fetchPlugins" class="primary-button">Retry</button>
    </div>

    <!-- Special handling for 501 Not Implemented -->
    <div v-else-if="isNotImplemented" class="not-implemented-container">
        <p>{{ error }}</p> <!-- Display the "not yet implemented" message -->
        <p>This feature is planned for future development.</p>
        <button @click="handleInstallPlugin" class="primary-button">Attempt to Open Install Plugin Dialog</button>
    </div>

    <div v-else-if="plugins.length === 0 && !loading" class="no-data-container">
      <p>暂无数据 (No Data Available)</p>
      <button @click="handleInstallPlugin" class="primary-button">安装插件 (Install Plugin)</button>
    </div>

    <div v-else>
      <div class="top-operations">
        <button @click="handleInstallPlugin" class="primary-button">安装插件 (Install Plugin)</button>
        <!-- Add other operations like search if needed later -->
      </div>
      <table class="plugins-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Version</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="plugin in plugins" :key="plugin.id">
            <td>{{ plugin.id }}</td>
            <td>{{ plugin.name }}</td>
            <td>{{ plugin.version || '-' }}</td>
            <td>{{ plugin.enabled ? 'Enabled' : 'Disabled' }}</td>
            <td>
              <button @click="handleToggleEnable(plugin)" class="action-button">
                {{ plugin.enabled ? 'Disable' : 'Enable' }}
              </button>
              <button @click="handleDeletePlugin(plugin.id)" class="action-button danger">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
      <!-- Pagination if needed -->
    </div>

    <!-- Install Plugin Modal (Placeholder) -->
    <div v-if="showInstallModal" class="modal-overlay" @click.self="showInstallModal = false">
      <div class="modal-content">
        <h2>Install Plugin</h2>
        <p>Plugin installation functionality (e.g., file upload or URL) will be implemented here.</p>
        <p>Currently, backend plugin endpoints return 501 (Not Implemented), so this dialog is a placeholder.</p>
        <div class="modal-actions">
              <button type="button" @click="showInstallModal = false">Close</button> <!-- Removed primary-button class -->
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, computed } from 'vue'; // Added computed

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Plugin {
  id: number;
  name: string;
  version?: string | null;
  source_path?: string | null;
  enabled: boolean;
  created_at: string;
}

// Paginated response structure is not used yet as backend returns 501
// interface PaginatedPluginsResponse {
//   items: Plugin[];
//   total: number;
//   page: number;
//   page_size: number;
//   pages: number;
// }

const plugins = ref<Plugin[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showInstallModal = ref(false);

const isNotImplemented = computed(() => error.value && error.value.includes('not yet implemented'));

const fetchPlugins = async () => {
  loading.value = true;
  error.value = null;
  plugins.value = []; // Clear previous plugins before fetch attempt
  try {
    const response = await fetch(`${API_BASE_URL}/plugins`);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      if (response.status === 501) {
        error.value = errData.detail || 'Plugin functionality is not yet implemented on the server.';
      } else {
        throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
      }
    } else {
      // This part likely won't be reached if backend is 501
      const data: { items: Plugin[] } = await response.json(); // Assuming PaginatedResponse structure if it were implemented
      plugins.value = data.items;
    }
  } catch (e: any) {
    if (!error.value) { // Don't overwrite specific 501 message
        error.value = e.message || 'Failed to fetch plugins.';
    }
  } finally {
    loading.value = false;
  }
};

const handleInstallPlugin = () => {
  showInstallModal.value = true;
};

const handleToggleEnable = (plugin: Plugin) => {
  alert(`Placeholder: Toggle enable for plugin ID ${plugin.id} (${plugin.name}). Backend not implemented (501).`);
  // Future: Call PUT /api/v1/plugins/${plugin.id} { enabled: !plugin.enabled }
  // And then refresh: fetchPlugins();
};

const handleDeletePlugin = (pluginId: number) => {
  if (window.confirm('Are you sure you want to delete this plugin (record)?')) {
    alert(`Placeholder: Delete plugin ID ${pluginId}. Backend not implemented (501).`);
    // Future: Call DELETE /api/v1/plugins/${pluginId}
    // And then refresh: fetchPlugins();
  }
};

onMounted(() => {
  fetchPlugins();
});
</script>

<style scoped>
.plugins-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.top-operations {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px; /* Adjusted */
}
.primary-button {
  background-color: #1890ff;
  color: white;
  border: 1px solid #1890ff;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}
.primary-button:hover {
  background-color: #40a9ff;
}
.no-data-container, .loading-container, .error-container, .not-implemented-container {
  text-align: center;
  padding: 30px 20px; /* Adjusted padding */
  border: 1px dashed #d9d9d9; /* Ant Design dashed border */
  border-radius: 4px;
  background-color: #fafafa; /* Lighter background */
  color: rgba(0,0,0,.65);
}
.not-implemented-container p {
    margin-bottom: 15px;
}

.plugins-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.plugins-table th,
.plugins-table td {
  border: 1px solid #e8e8e8;
  padding: 10px 12px;
  text-align: left;
}
.plugins-table th {
  background-color: #fafafa; /* Ant Design table header */
  font-weight: 500;
  color: rgba(0,0,0,.85);
}
.plugins-table tbody tr:hover {
  background-color: #f5f5f5;
}
.action-button {
  padding: 4px 8px;
  font-size: 13px;
  margin-right: 6px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  cursor: pointer;
  background-color: #fff;
  transition: color 0.3s, border-color 0.3s;
}
.action-button:hover {
  border-color: #1890ff;
  color: #1890ff;
}
.action-button.danger {
  color: #ff4d4f;
  border-color: #ff4d4f;
}
.action-button.danger:hover {
  color: #fff;
  background-color: #ff4d4f;
}

.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex; justify-content: center; align-items: center; z-index: 1000;
}
.modal-content {
  background: white; padding: 24px; border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15); width: 90%; max-width: 480px; /* Adjusted width */
  color: rgba(0,0,0,.85);
}
.modal-content h2 {
    margin-top: 0;
    margin-bottom: 20px;
    font-size: 18px;
    font-weight: 500;
}
.modal-content p {
    margin-bottom: 10px;
    font-size: 14px;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 8px; margin-top: 24px;
}
.modal-actions button { /* Style for default button in modal actions */
    padding: 8px 15px;
    font-size: 14px;
    border-radius: 4px;
    cursor: pointer;
    background-color: #fff;
    border: 1px solid #dcdfe6; /* Ant/Element-like default border */
    color: #606266; /* Ant/Element-like default text color */
}
.modal-actions button:hover {
    color: #409eff;
    border-color: #c6e2ff;
    background-color: #ecf5ff;
}
/* .primary-button can be added if a primary action exists in this modal later */
</style>
