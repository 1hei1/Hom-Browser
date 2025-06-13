<template>
  <div class="proxies-view">
    <h1>Proxy Management</h1>

    <div class="top-operations">
      <button @click="openCreateModal" class="primary-button">+ Add Proxy</button>
      <input type="text" v-model="searchQuery" @input="debouncedFetchProxies" placeholder="Search by name, host, type..." class="search-input" />
      <button @click="handleBatchDelete" :disabled="selectedProxies.length === 0">Batch Delete Selected</button>
    </div>

    <table class="proxies-table">
      <thead>
        <tr>
          <th><input type="checkbox" @change="toggleSelectAll" :checked="proxies.length > 0 && selectedProxies.length === proxies.length" /></th>
          <th>ID</th>
          <th>Name</th>
          <th>Type</th>
          <th>Host</th>
          <th>Port</th>
          <th>Username</th>
          <th>Notes</th>
          <th>Usage Count</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="10" style="text-align: center;">Loading...</td>
        </tr>
        <tr v-else-if="error">
          <td colspan="10" style="text-align: center; color: red;">{{ error }}</td>
        </tr>
        <tr v-for="proxy in proxies" :key="proxy.id">
          <td><input type="checkbox" :value="proxy.id" v-model="selectedProxies" /></td>
          <td>{{ proxy.id }}</td>
          <td>{{ proxy.name || '-' }}</td>
          <td>{{ proxy.type }}</td>
          <td>{{ proxy.host }}</td>
          <td>{{ proxy.port }}</td>
          <td>{{ proxy.username || '-' }}</td>
          <td>{{ proxy.notes || '-' }}</td>
          <td>{{ proxy.usage_count != null ? proxy.usage_count : '-' }}</td>
          <td>
            <button @click="openEditModal(proxy)" class="action-button">Edit</button>
            <button @click="confirmDeleteProxy(proxy.id)" class="action-button danger">Delete</button>
          </td>
        </tr>
        <tr v-if="!loading && !error && proxies.length === 0">
          <td colspan="10" style="text-align: center;">No proxies found.</td>
        </tr>
      </tbody>
    </table>

    <div v-if="!loading && pagination.total_pages > 1" class="pagination-controls">
      <button @click="fetchProxies(pagination.current_page - 1)" :disabled="pagination.current_page <= 1">&lt; Prev</button>
      <span>Page {{ pagination.current_page }} of {{ pagination.total_pages }}</span>
      <button @click="fetchProxies(pagination.current_page + 1)" :disabled="pagination.current_page >= pagination.total_pages">Next &gt;</button>
    </div>

    <!-- Create/Edit Proxy Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h2>{{ editMode ? 'Edit Proxy' : 'Add New Proxy' }}</h2>
        <form @submit.prevent="handleProxySubmit">
          <div>
            <label for="proxyName">Name (Optional):</label>
            <input type="text" id="proxyName" v-model="currentProxy.name" />
          </div>
          <div>
            <label for="proxyType">Type:</label>
            <select id="proxyType" v-model="currentProxy.type" required>
              <option value="HTTP">HTTP</option>
              <option value="SOCKS5">SOCKS5</option>
              <!-- Add other types if supported by backend -->
            </select>
          </div>
          <div>
            <label for="proxyHost">Host:</label>
            <input type="text" id="proxyHost" v-model="currentProxy.host" required />
          </div>
          <div>
            <label for="proxyPort">Port:</label>
            <input type="number" id="proxyPort" v-model.number="currentProxy.port" required min="1" max="65535" />
          </div>
          <div>
            <label for="proxyUsername">Username (Optional):</label>
            <input type="text" id="proxyUsername" v-model="currentProxy.username" />
          </div>
          <div>
            <label for="proxyPassword">Password (Optional):</label>
            <input type="password" id="proxyPassword" v-model="currentProxy.password" autocomplete="new-password" />
          </div>
          <div>
            <label for="proxyNotes">Notes (Optional):</label>
            <textarea id="proxyNotes" v-model="currentProxy.notes"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal">Cancel</button>
            <button type="submit" class="primary-button">{{ editMode ? 'Save Changes' : 'Add Proxy' }}</button>
          </div>
          <p v-if="modalError" class="modal-error">{{ modalError }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Proxy {
  id: number;
  name?: string | null;
  type: string;
  host: string;
  port: number;
  username?: string | null;
  password?: string | null;
  notes?: string | null;
  created_at: string;
  usage_count?: number;
}

interface PaginatedProxiesResponse {
  items: Proxy[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface BatchDeleteErrorDetail {
  id: number;
  error: string;
}

interface BatchDeleteResponse {
  message: string;
  deleted_count: number;
  errors: BatchDeleteErrorDetail[];
}

const proxies = ref<Proxy[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showModal = ref(false);
const editMode = ref(false);
const modalError = ref<string | null>(null);
const searchQuery = ref('');
const selectedProxies = ref<number[]>([]);

const initialProxyState = (): Partial<Proxy> => ({
  id: undefined,
  name: '',
  type: 'HTTP', // Default type
  host: '',
  port: undefined, // Explicitly undefined
  username: '',
  password: '',
  notes: '',
});

const currentProxy = reactive<Partial<Proxy>>(initialProxyState());

const pagination = reactive({
  current_page: 1,
  page_size: 10,
  total_items: 0,
  total_pages: 0,
});

// const formatDate = (dateString: string) => { // Not used in this version of table
//   if (!dateString) return '-';
//   return new Date(dateString).toLocaleString();
// };

let debounceTimer: number;
const debouncedFetchProxies = () => {
  clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    fetchProxies(1);
  }, 300); // Reduced debounce time
};

watch(searchQuery, () => {
    debouncedFetchProxies();
});

const fetchProxies = async (page = 1) => {
  loading.value = true;
  error.value = null;
  if (page < 1 && pagination.total_pages > 0) page = 1; // Boundary checks
  if (page > pagination.total_pages && pagination.total_pages > 0) page = pagination.total_pages;

  selectedProxies.value = [];
  try {
    let url = `${API_BASE_URL}/proxies?page=${page}&page_size=${pagination.page_size}`;
    if (searchQuery.value.trim()) {
      url += `&search=${encodeURIComponent(searchQuery.value.trim())}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    const data: PaginatedProxiesResponse = await response.json();
    proxies.value = data.items.map(p => ({...p, password: ''}));
    pagination.current_page = data.page;
    pagination.total_items = data.total;
    pagination.total_pages = data.pages;

    if (data.page > data.pages && data.pages > 0) { // If current page is out of bounds
        fetchProxies(data.pages); // Fetch the last valid page
    }

  } catch (e: any) {
    error.value = e.message || 'Failed to fetch proxies.';
    // proxies.value = []; // Keep stale data on error? or clear? User preference.
  } finally {
    loading.value = false;
  }
};

const openCreateModal = () => {
  Object.assign(currentProxy, initialProxyState()); // Reset to initial state
  editMode.value = false;
  modalError.value = null;
  showModal.value = true;
};

const openEditModal = (proxy: Proxy) => {
  editMode.value = true;
  // Ensure all fields in currentProxy are set from proxy, even if undefined in proxy
  currentProxy.id = proxy.id;
  currentProxy.name = proxy.name || '';
  currentProxy.type = proxy.type;
  currentProxy.host = proxy.host;
  currentProxy.port = proxy.port;
  currentProxy.username = proxy.username || '';
  currentProxy.password = ''; // Always clear password for edit
  currentProxy.notes = proxy.notes || '';

  modalError.value = null;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  // currentProxy is reset by openCreateModal or filled by openEditModal
};

const handleProxySubmit = async () => {
  modalError.value = null;
  if (!currentProxy.host?.trim() || !currentProxy.port || !currentProxy.type) {
    modalError.value = 'Type, Host and Port are required.';
    return;
  }

  const url = editMode.value ? `${API_BASE_URL}/proxies/${currentProxy.id}` : `${API_BASE_URL}/proxies/`;
  const method = editMode.value ? 'PUT' : 'POST';

  const payload: any = {
    name: currentProxy.name?.trim() || null, // Send null if empty for optional name
    type: currentProxy.type,
    host: currentProxy.host.trim(),
    port: Number(currentProxy.port),
    username: currentProxy.username?.trim() || null,
    notes: currentProxy.notes?.trim() || null,
  };
  if (currentProxy.password) { // Only include password if set
      payload.password = currentProxy.password;
  }


  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Operation failed with status: ' + response.status }));
      throw new Error(errorData.detail || `Failed to ${editMode.value ? 'update' : 'create'} proxy.`);
    }
    fetchProxies(editMode.value ? pagination.current_page : 1);
    closeModal();
  } catch (e: any) {
    modalError.value = e.message;
  }
};

const confirmDeleteProxy = async (proxyId: number) => {
  if (window.confirm('Are you sure you want to delete this proxy? This action cannot be undone.')) {
    try {
      const response = await fetch(`${API_BASE_URL}/proxies/${proxyId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete proxy.'}));
        throw new Error(errorData.detail || 'Failed to delete proxy.');
      }
      // Check if current page becomes empty
      if (proxies.value.length === 1 && pagination.current_page > 1) {
        fetchProxies(pagination.current_page - 1);
      } else {
        fetchProxies(pagination.current_page);
      }
      selectedProxies.value = selectedProxies.value.filter(id => id !== proxyId);
    } catch (e: any) {
      error.value = e.message;
    }
  }
};

const toggleSelectAll = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.checked) {
    selectedProxies.value = proxies.value.map(p => p.id);
  } else {
    selectedProxies.value = [];
  }
};

const handleBatchDelete = async () => {
  if (selectedProxies.value.length === 0) {
    alert('No proxies selected for deletion.');
    return;
  }
  if (window.confirm(`Are you sure you want to delete ${selectedProxies.value.length} selected proxies? This action cannot be undone.`)) {
    try {
      const response = await fetch(`${API_BASE_URL}/proxies/batch-delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ids: selectedProxies.value }),
      });

      const resultText = await response.text(); // Get raw text first
      let result: BatchDeleteResponse;
      try {
        result = JSON.parse(resultText); // Try to parse as JSON
      } catch (e) {
        throw new Error("Failed to parse server response: " + resultText);
      }

      if (!response.ok) { // Check HTTP status code
         throw new Error(result.message || 'Batch delete operation failed.');
      }

      let summaryMessage = result.message;
      if (result.errors && result.errors.length > 0) {
        const errorDetails = result.errors.map(e => `ID ${e.id}: ${e.error}`).join('\n');
        summaryMessage += '\n\nErrors:\n' + errorDetails;
        // alert(summaryMessage); // Or use a more sophisticated notification system
      }
      // alert(summaryMessage); // Show summary, or use a toast notification
      console.log("Batch delete result:", result);


      // Smartly refresh the page: if all items on current page were deleted, go to prev page
      let currentPageAfterDelete = pagination.current_page;
      const numItemsOnCurrentPage = proxies.value.length;
      const numSuccessfullyDeletedOnCurrentPage = selectedProxies.value.length - (result.errors?.length || 0);

      if (numSuccessfullyDeletedOnCurrentPage >= numItemsOnCurrentPage && pagination.current_page > 1) {
        currentPageAfterDelete = pagination.current_page -1;
      }
      fetchProxies(currentPageAfterDelete);
      selectedProxies.value = []; // Clear selection after operation

    } catch (e: any) {
      error.value = e.message; // Display error on the page
      // alert("Error during batch delete: " + e.message); // Or use a more sophisticated notification
    }
  }
};

onMounted(() => {
  fetchProxies();
});

</script>

<style scoped>
.proxies-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.top-operations {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px; /* Reduced margin as parent has gap */
  flex-wrap: wrap;
}
.top-operations button,
.top-operations input,
.top-operations select { /* Added select for future use */
  padding: 8px 12px;
  border: 1px solid #d9d9d9; /* Ant Design-like border */
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.5715;
}
.top-operations button {
    cursor: pointer;
    transition: background-color 0.3s, border-color 0.3s;
}
.top-operations button:hover {
    border-color: #40a9ff;
}
.top-operations button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
    background-color: #f5f5f5;
}
.primary-button {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}
.primary-button:hover:not(:disabled) {
  background-color: #40a9ff;
  border-color: #40a9ff;
}
.search-input {
  min-width: 250px;
}
.proxies-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
  font-size: 14px;
}
.proxies-table th,
.proxies-table td {
  border: 1px solid #e8e8e8;
  padding: 10px 12px;
  text-align: left;
  word-break: break-all;
}
.proxies-table th {
  background-color: #fafafa; /* Ant Design table header color */
  font-weight: 500;   /* Ant Design table header font-weight */
  color: rgba(0,0,0,.85);
}
.proxies-table tbody tr:hover {
  background-color: #f5f5f5;
}
.proxies-table input[type="checkbox"] {
    cursor: pointer;
}
.action-button {
  padding: 4px 8px; /* Slightly smaller padding */
  margin-right: 6px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  cursor: pointer;
  background-color: #fff;
  font-size: 13px;
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
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6); /* Darker overlay */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 24px; /* Ant Design modal padding */
  border-radius: 4px; /* Ant Design modal border-radius */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 520px; /* Ant Design modal width */
  color: rgba(0,0,0,.85);
}
.modal-content h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 18px; /* Ant Design modal title size */
  font-weight: 500;
}
.modal-content form div:not(.modal-actions) {
  margin-bottom: 20px; /* Increased spacing */
}
.modal-content label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: rgba(0,0,0,.85);
}
.modal-content input[type="text"],
.modal-content input[type="number"],
.modal-content input[type="password"],
.modal-content select,
.modal-content textarea {
  box-sizing: border-box;
  width: 100%;
  padding: 8px 12px; /* Ant Design input padding */
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.modal-content input:hover,
.modal-content select:hover,
.modal-content textarea:hover {
    border-color: #40a9ff;
}
.modal-content input:focus,
.modal-content select:focus,
.modal-content textarea:focus {
    border-color: #40a9ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
    outline: 0;
}
.modal-content textarea {
  min-height: 80px;
  resize: vertical;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px; /* Ant Design modal footer gap */
  margin-top: 24px;
}
.modal-actions button {
    padding: 8px 15px;
    font-size: 14px;
    border-radius: 4px;
    cursor: pointer;
}
.modal-actions button[type="button"] {
    background-color: #fff;
    border: 1px solid #d9d9d9;
}
.modal-actions button[type="button"]:hover {
    border-color: #1890ff;
    color: #1890ff;
}

.modal-error {
  color: #ff4d4f;
  font-size: 14px;
  margin-top: 10px;
  text-align: left;
}
.pagination-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 16px; /* Ant Design pagination margin */
}
.pagination-controls button {
  padding: 0 12px; /* Ant Design button padding */
  height: 32px;
  line-height: 30px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  transition: border-color 0.3s, color 0.3s;
}
.pagination-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
  border-color: #d9d9d9;
  color: rgba(0,0,0,.25);
}
.pagination-controls button:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}
.pagination-controls span {
  font-size: 14px;
  color: rgba(0,0,0,.85);
}
</style>
