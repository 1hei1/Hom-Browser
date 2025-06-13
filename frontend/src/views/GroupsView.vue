<template>
  <div class="groups-view">
    <h1>Group Management</h1>

    <div class="top-operations">
      <button @click="showCreateModal = true" class="primary-button">+ Create Group</button>
      <!-- Add search input if needed later -->
    </div>

    <table class="groups-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>分组名称 (Group Name)</th>
          <th>分组浏览器数 (Profile Count)</th>
          <th>创建时间 (Creation Time)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="5" style="text-align: center;">Loading...</td>
        </tr>
        <tr v-else-if="error">
          <td colspan="5" style="text-align: center; color: red;">{{ error }}</td>
        </tr>
        <tr v-for="group in groups" :key="group.id">
          <td>{{ group.id }}</td>
          <td>{{ group.name }}</td>
          <td>{{ group.profile_count != null ? group.profile_count : '-' }}</td>
          <td>{{ formatDate(group.created_at) }}</td>
          <td>
            <button @click="openEditModal(group)" class="action-button">Edit</button>
            <button @click="confirmDeleteGroup(group.id)" class="action-button danger">Delete</button>
          </td>
        </tr>
        <tr v-if="!loading && !error && groups.length === 0">
          <td colspan="5" style="text-align: center;">No groups found.</td>
        </tr>
      </tbody>
    </table>

    <!-- Pagination -->
    <div v-if="!loading && pagination.total_pages > 1" class="pagination-controls">
      <button @click="fetchGroups(pagination.current_page - 1)" :disabled="pagination.current_page <= 1">&lt; Prev</button>
      <span>Page {{ pagination.current_page }} of {{ pagination.total_pages }}</span>
      <button @click="fetchGroups(pagination.current_page + 1)" :disabled="pagination.current_page >= pagination.total_pages">Next &gt;</button>
    </div>

    <!-- Create/Edit Group Modal -->
    <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click.self="closeModal"> <!-- Close on overlay click -->
      <div class="modal-content">
        <h2>{{ editMode ? 'Edit Group' : 'Create New Group' }}</h2>
        <form @submit.prevent="handleGroupSubmit">
          <div>
            <label for="groupName">Group Name:</label>
            <input type="text" id="groupName" v-model="currentGroup.name" required />
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeModal">Cancel</button>
            <button type="submit" class="primary-button">{{ editMode ? 'Save Changes' : 'Create Group' }}</button>
          </div>
          <p v-if="modalError" class="modal-error">{{ modalError }}</p>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Group {
  id: number;
  name: string;
  profile_count?: number; // Make optional as it might not always be present or needed for create/update
  created_at: string;
}

interface PaginatedGroupsResponse {
  items: Group[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const groups = ref<Group[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);
const showCreateModal = ref(false);
const showEditModal = ref(false);
const editMode = ref(false);
const modalError = ref<string | null>(null);

const currentGroup = reactive<Partial<Group>>({
  id: undefined,
  name: '',
});

const pagination = reactive({
    current_page: 1,
    page_size: 10, // Default page size
    total_items: 0,
    total_pages: 0,
});

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return '-';
  try {
    return new Date(dateString).toLocaleString();
  } catch (e) {
    return dateString; // Return original if parsing fails
  }
};

const fetchGroups = async (page = 1) => {
  loading.value = true;
  error.value = null;
  if (page < 1) page = 1; // Ensure page is not less than 1

  try {
    const response = await fetch(`${API_BASE_URL}/groups?page=${page}&page_size=${pagination.page_size}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    const data: PaginatedGroupsResponse = await response.json();
    groups.value = data.items;
    pagination.current_page = data.page;
    pagination.total_items = data.total;
    pagination.total_pages = data.pages;
    if (pagination.current_page > pagination.total_pages && pagination.total_pages > 0) {
        // If current page is out of bounds after a delete, fetch last page
        fetchGroups(pagination.total_pages);
    }

  } catch (e: any) {
    error.value = e.message || 'Failed to fetch groups.';
    // groups.value = []; // Optionally clear groups or keep stale data
  } finally {
    loading.value = false;
  }
};

const openEditModal = (group: Group) => {
  editMode.value = true;
  currentGroup.id = group.id;
  currentGroup.name = group.name;
  modalError.value = null;
  showEditModal.value = true;
  showCreateModal.value = false; // Ensure create modal is not also active
};

const closeModal = () => {
  showCreateModal.value = false;
  showEditModal.value = false;
  editMode.value = false;
  currentGroup.id = undefined;
  currentGroup.name = '';
  modalError.value = null;
};

const handleGroupSubmit = async () => {
  modalError.value = null;
  if (!currentGroup.name?.trim()) {
      modalError.value = "Group name cannot be empty.";
      return;
  }

  const url = editMode.value ? `${API_BASE_URL}/groups/${currentGroup.id}` : `${API_BASE_URL}/groups/`;
  const method = editMode.value ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name: currentGroup.name }),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `Failed to ${editMode.value ? 'update' : 'create'} group. Server error.` }));
      throw new Error(errorData.detail || `Failed to ${editMode.value ? 'update' : 'create'} group.`);
    }
    // If creating, go to the page where the new item would be (usually last page, or page 1 if sorted by name/creation)
    // For simplicity, refreshing current page or page 1.
    // If it's an edit, stay on the current page.
    await fetchGroups(editMode.value ? pagination.current_page : 1);
    closeModal();
  } catch (e: any) {
    modalError.value = e.message;
  }
};

const confirmDeleteGroup = async (groupId: number) => {
  if (window.confirm('Are you sure you want to delete this group? Profiles in this group will be unassigned.')) {
    try {
      const response = await fetch(`${API_BASE_URL}/groups/${groupId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to delete group. Server error.'}));
        throw new Error(errorData.detail || 'Failed to delete group.');
      }
      // After deleting, if the current page becomes empty and it's not page 1,
      // fetch the previous page or page 1.
      // This logic is simplified in current fetchGroups by checking if current_page > total_pages
      await fetchGroups(pagination.current_page);
    } catch (e: any) {
      error.value = e.message;
    }
  }
};

onMounted(() => {
  fetchGroups();
});

</script>

<style scoped>
.groups-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.top-operations {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap; /* Added for consistency */
  /* margin-bottom: 20px; -- Handled by parent gap */
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
.groups-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}
.groups-table th,
.groups-table td {
  border: 1px solid #e8e8e8;
  padding: 10px 12px;
  text-align: left;
  font-size: 14px;
}
.groups-table th {
  background-color: #f8f8f8;
  font-weight: 600;
}
.groups-table tbody tr:hover {
  background-color: #f5f5f5;
}
.action-button {
  padding: 5px 10px;
  margin-right: 5px;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  background-color: #fff;
  transition: border-color 0.3s;
}
.action-button.danger {
  color: #fff;
  background-color: #ff4d4f;
  border-color: #ff4d4f;
  transition: background-color 0.3s, border-color 0.3s;
}
.action-button.danger:hover {
  background-color: #ff7875;
  border-color: #ff7875;
}
.action-button:hover {
  border-color: #1890ff;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 400px;
  color: #333; /* Ensure text is readable */
}
.modal-content h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.5em;
}
.modal-content form div:not(.modal-actions) { /* Avoid applying to modal-actions div */
  margin-bottom: 15px;
}
.modal-content label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}
.modal-content input[type="text"] {
  width: 100%; /* Full width of parent */
  box-sizing: border-box; /* Include padding and border in the element's total width and height */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px; /* Ant Design/Element UI like modal footer gap */
  margin-top: 24px; /* Consistent spacing */
  border-top: 1px solid #e4e7ed; /* Separator line like ProfileFormModal */
  padding-top: 20px; /* Spacing above buttons */
}
.modal-actions button { /* General style for action buttons */
    padding: 8px 15px; /* Adjusted padding to match ProfileFormModal */
    font-size: 14px; /* Consistent font size */
    border-radius: 4px;
    cursor: pointer;
    /* border: 1px solid #dcdfe6; */ /* Base border from ProfileFormModal */
}
.modal-actions button[type="button"] { /* Cancel button */
    background-color: #fff;
    border: 1px solid #dcdfe6; /* Style like ProfileFormModal's cancel */
    color: #606266;
}
.modal-actions button[type="button"]:hover {
    color: #409eff; /* Element UI hover blue */
    border-color: #c6e2ff; /* Lighter blue border */
    background-color: #ecf5ff; /* Light blue background */
}
/* .primary-button class will style the submit button */

.modal-error {
  color: red;
  font-size: 0.9em;
  margin-top: 15px;
  text-align: left;
}
.pagination-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  /* margin-top: 20px; -- Handled by parent gap */
}
.pagination-controls button {
  padding: 6px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
  transition: border-color 0.3s;
}
.pagination-controls button:hover:not(:disabled) {
  border-color: #1890ff;
}
.pagination-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
.pagination-controls span {
  font-size: 14px;
}
</style>
