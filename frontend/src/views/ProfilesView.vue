<template>
  <div class="profiles-view">
    <h1>Browser Profiles</h1>

    <div class="top-operations">
      <button @click="openCreateProfileModal" class="primary-button">+ Create Browser</button>
      <button @click="handleBatchDelete" :disabled="selectedProfileIds.length === 0">Batch Delete Selected</button>
      <button @click="openBatchAssignGroupModal" :disabled="selectedProfileIds.length === 0">Batch Assign Group</button>
      <button @click="fetchProfiles(pagination.current_page, true)">同步 (Sync)</button>

      <select class="group-filter-select" v-model="filterGroupId" @change="handleFilterChange">
        <option :value="null">All Groups</option>
        <option v-for="group in availableGroups" :key="group.id" :value="group.id"> <!-- Changed to availableGroups -->
            {{ group.name }}
        </option>
      </select>
      <input type="text" v-model="searchNameQuery" @input="debouncedFetchProfiles" placeholder="Search by name..." class="name-search-input" />
    </div>

    <table class="profiles-table">
      <thead>
        <tr>
          <th><input type="checkbox" @change="toggleSelectAllProfiles" :checked="profiles.length > 0 && selectedProfileIds.length === profiles.length" /></th>
          <th>序号 (ID)</th>
          <th>名称 (Name)</th>
          <th>分组 (Group)</th>
          <th>代理 (Proxy)</th>
          <th>备注 (Notes)</th>
          <th>最后启动时间 (Last Launch Time)</th>
          <th>启动 (Launch)</th>
          <th>操作 (Actions)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="9" style="text-align: center;">Loading...</td>
        </tr>
        <tr v-else-if="error">
          <td colspan="9" style="text-align: center; color: red;">{{ error }}</td>
        </tr>
        <tr v-for="profile in profiles" :key="profile.id">
          <td><input type="checkbox" :value="profile.id" v-model="selectedProfileIds" /></td>
          <td>{{ profile.id }}</td>
          <td>{{ profile.name }}</td>
          <td>{{ getGroupName(profile.group_id) || '-' }}</td>
          <td>{{ getProxyDisplay(profile.custom_proxy_id, profile.proxy_config_type) }}</td>
          <td>{{ profile.notes || '-' }}</td>
          <td>{{ formatDate(profile.last_launch_time) }}</td>
          <td><button @click="launchProfile(profile.id)" class="action-button launch-button">Launch</button></td>
          <td>
            <button @click="openEditProfileModal(profile)" class="action-button">Edit</button>
            <button @click="confirmDeleteProfile(profile.id)" class="action-button danger">Delete</button>
          </td>
        </tr>
        <tr v-if="!loading && !error && profiles.length === 0">
          <td colspan="9" style="text-align: center;">No profiles found.</td>
        </tr>
      </tbody>
    </table>

    <div v-if="!loading && pagination.total_pages > 1" class="pagination-controls">
      <button @click="fetchProfiles(pagination.current_page - 1)" :disabled="pagination.current_page <= 1">&lt; Prev</button>
      <span>Page {{ pagination.current_page }} of {{ pagination.total_pages }}</span>
      <button @click="fetchProfiles(pagination.current_page + 1)" :disabled="pagination.current_page >= pagination.total_pages">Next &gt;</button>
    </div>

    <ProfileFormModal
      :visible="showProfileModal"
      :profile-data="editingProfile"
      @close="handleProfileModalClose"
      @save="handleProfileModalSave"
    />

    <!-- Launch Status Modal (existing) -->
    <div v-if="showLaunchStatusModal" class="modal-overlay" @click.self="showLaunchStatusModal = false">
      <div class="modal-content launch-status-modal">
        <h2>Profile Launch Status</h2>
        <p :class="launchStatus.error ? 'modal-error' : 'modal-success'"><strong>Status:</strong> {{ launchStatus.message }}</p>
        <div v-if="launchStatus.command">
          <strong>Generated Command:</strong>
          <pre class="command-display"><code>{{ launchStatus.command }}</code></pre>
        </div>
        <p v-if="launchStatus.error" class="modal-error"><strong>Details:</strong> {{ launchStatus.error }}</p>
        <div class="modal-actions">
          <button @click="showLaunchStatusModal = false" class="primary-button">Close</button>
        </div>
      </div>
    </div>

    <!-- Batch Assign Group Modal -->
    <div v-if="showAssignGroupModal" class="modal-overlay" @click.self="showAssignGroupModal = false">
      <div class="modal-content">
        <h2>Assign Group to {{selectedProfileIds.length}} Selected Profile(s)</h2>
        <div>
          <label for="batchAssignGroupSelect">Select Group:</label>
          <select id="batchAssignGroupSelect" v-model="selectedGroupIdForBatchAssign">
            <option :value="null">Select a Group</option>
            <option :value="0">Unassign (Remove from Group)</option>
            <option v-for="group in availableGroups" :key="group.id" :value="group.id">
              {{ group.name }}
            </option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" @click="showAssignGroupModal = false">Cancel</button>
          <button type="button" @click="submitBatchAssignGroup" class="primary-button" :disabled="selectedGroupIdForBatchAssign === null">Assign Group</button>
        </div>
        <p v-if="batchAssignError" class="modal-error">{{ batchAssignError }}</p>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, watch, computed } from 'vue';
import ProfileFormModal from '../components/profiles/ProfileFormModal.vue'; // Corrected path

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Simplified Profile interface for the list view
interface ProfileListItem {
  id: number;
  name: string;
  group_id?: number | null;
  custom_proxy_id?: number | null;
  proxy_config_type?: 'default' | 'none' | 'custom';
  notes?: string | null;
  last_launch_time?: string | null;
  // Fields needed for editing that might not be on ProfileSimple from backend
  os_platform?: string;
  os_version?: string;
  browser_version?: string;
  cookies?: string;
  language?: string;
  accept_language?: string;
  timezone?: string;
  fingerprint_seed?: number | null;
  startup_homepage?: string;
  user_agent?: string;
  sec_ch_ua?: string;
  webgl_image_mode?: string;
  webgl_vendor?: string;
  webgl_renderer?: string;
  audiocontext_mode?: string;
  clientrects_mode?: string;
  speech_voices_mode?: string;
  cpu_cores?: number | null;
  memory_gb?: number | null;
  device_name?: string;
  mac_address?: string;
  do_not_track?: boolean;
  ssl_cipher_suites_mode?: string;
  port_scan_protection?: boolean;
  hardware_acceleration?: boolean;
  scan_port_whitelist?: string;
  custom_launch_parameters?: string;
}

interface PaginatedProfilesResponse {
  items: ProfileListItem[]; // Using ProfileListItem which should match schemas.ProfileSimple + potentially more for edit
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

interface Group { id: number; name: string; } // For group filter dropdown
interface Proxy { id: number; name?: string | null; host: string; port: number; type: string; } // For proxy display

const profiles = ref<ProfileListItem[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const showProfileModal = ref(false);
const editingProfile = ref<ProfileListItem | null>(null);

const selectedProfileIds = ref<number[]>([]);
// selectedBatchAction is removed as direct buttons are used
// batchAssignGroupId is now selectedGroupIdForBatchAssign
const availableGroups = ref<Group[]>([]); // Unified available groups list
const availableProxiesForDisplay = ref<Proxy[]>([]);

const filterGroupId = ref<number | null>(null);
const searchNameQuery = ref('');


const showLaunchStatusModal = ref(false);
const launchStatus = reactive({
  profile_id: null as number | null,
  message: '',
  command: null as string | null,
  error: null as string | null,
});

// New refs for Batch Assign Group Modal
const showAssignGroupModal = ref(false);
const selectedGroupIdForBatchAssign = ref<number | null>(null); // Can be 0 for unassign
const batchAssignError = ref<string | null>(null);

const pagination = reactive({
  current_page: 1,
  page_size: 10,
  total_items: 0,
  total_pages: 0,
});

const formatDate = (dateString?: string | null) => {
  if (!dateString) return '-';
  try { return new Date(dateString).toLocaleString(); }
  catch { return dateString; }
};

let debounceTimer: number;
const debouncedFetchProfiles = () => {
  clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    fetchProfiles(1); // Reset to page 1 on new search/filter
  }, 300);
};

const handleFilterChange = () => {
    debouncedFetchProfiles();
};


const fetchSelectableData = async () => {
    try {
        const groupsResponse = await fetch(`${API_BASE_URL}/groups?page_size=1000`);
        if (groupsResponse.ok) {
            availableGroups.value = (await groupsResponse.json()).items;
        } else {
            console.error("Failed to fetch groups");
            availableGroups.value = [];
        }

        const proxiesResponse = await fetch(`${API_BASE_URL}/proxies?page_size=1000`);
        if (proxiesResponse.ok) {
            availableProxiesForDisplay.value = (await proxiesResponse.json()).items;
        }
        else console.error("Failed to fetch proxies for display");

    } catch (e) {
        console.error("Error fetching selectable data:", e);
    }
};

const getGroupName = (groupId?: number | null) => {
    if (groupId === null || groupId === undefined) return null; // Check for undefined as well
    const group = availableGroups.value.find(g => g.id === groupId);
    return group ? group.name : String(groupId);
};

const getProxyDisplay = (proxyId?: number | null, configType?: string | null) => {
    if (configType === 'none') return 'No Proxy';
    if (configType === 'default') return 'System Default';
    if (configType === 'custom' && proxyId) {
        const proxy = availableProxiesForDisplay.value.find(p => p.id === proxyId);
        if (proxy) return proxy.name ? `${proxy.name} (${proxy.host}:${proxy.port})` : `${proxy.host}:${proxy.port}`;
        return `Custom (ID: ${proxyId})`;
    }
    return '-';
};


const fetchProfiles = async (page = 1, forceRefresh = false) => {
  loading.value = true;
  error.value = null;
  if (page < 1 && pagination.total_pages > 0) page = 1;
  if (page > pagination.total_pages && pagination.total_pages > 0) page = pagination.total_pages;

  try {
    let url = `${API_BASE_URL}/profiles?page=${page}&page_size=${pagination.page_size}`;
    if (filterGroupId.value !== null) {
      url += `&group_id=${filterGroupId.value}`;
    }
    if (searchNameQuery.value.trim()) {
      url += `&name=${encodeURIComponent(searchNameQuery.value.trim())}`;
    }
    // Add sort params if needed: &sort_by=created_at&sort_order=desc

    const response = await fetch(url);
    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
      throw new Error(errData.detail || `HTTP error! status: ${response.status}`);
    }
    const data: PaginatedProfilesResponse = await response.json();
    // Assume backend's ProfileSimple matches or is compatible with ProfileListItem
    // If ProfileListItem needs more fields than ProfileSimple, an additional fetch per profile might be needed for edit,
    // or ProfileSimple from backend should be expanded.
    profiles.value = data.items;
    pagination.current_page = data.page;
    pagination.total_items = data.total;
    pagination.total_pages = data.pages;
    if (data.page > data.pages && data.pages > 0) {
        fetchProfiles(data.pages);
    }
  } catch (e: any) {
    error.value = e.message || 'Failed to fetch profiles.';
  } finally {
    loading.value = false;
  }
};

const openCreateProfileModal = () => {
  editingProfile.value = null; // Explicitly null for create mode
  showProfileModal.value = true;
};

const openEditProfileModal = async (profile: ProfileListItem) => {
  // Fetch full profile data for editing to ensure all fields are present
  loading.value = true; // Show loading indicator
  try {
    const response = await fetch(`${API_BASE_URL}/profiles/${profile.id}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch profile details (status ${response.status})`);
    }
    const fullProfileData = await response.json();
    editingProfile.value = fullProfileData; // This should be ProfileFormData compatible
    showProfileModal.value = true;
  } catch (e: any) {
    error.value = "Could not load profile data for editing: " + e.message;
  } finally {
    loading.value = false;
  }
};

const handleProfileModalClose = () => {
  showProfileModal.value = false;
  editingProfile.value = null;
};

const handleProfileModalSave = () => {
  showProfileModal.value = false;
  editingProfile.value = null;
  // Refresh current page or go to page 1 if a new item was added
  fetchProfiles(pagination.current_page);
};

const confirmDeleteProfile = async (profileId: number) => {
    if (window.confirm('Are you sure you want to delete this profile? This will also delete its user data directory if it exists.')) {
        try {
            const response = await fetch(`${API_BASE_URL}/profiles/${profileId}`, { method: 'DELETE' });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({detail: 'Failed to delete profile.'}));
                throw new Error(errorData.detail);
            }
            fetchProfiles(pagination.current_page); // Refresh
        } catch (e:any) {
            error.value = e.message;
        }
    }
};

const toggleSelectAllProfiles = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.checked) {
    selectedProfileIds.value = profiles.value.map(p => p.id);
  } else {
    selectedProfileIds.value = [];
  }
};

const handleBatchDelete = async () => {
    if (selectedProfileIds.value.length === 0) {
        alert('No profiles selected for deletion.');
        return;
    }
    if (window.confirm(`Are you sure you want to delete ${selectedProfileIds.value.length} selected profile(s)? This action cannot be undone.`)) {
        loading.value = true; // Use main loading indicator for simplicity
        error.value = null;
        try {
            const response = await fetch(`${API_BASE_URL}/profiles/batch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'delete', profile_ids: selectedProfileIds.value }),
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Batch delete failed. Server error.' }));
                throw new Error(errorData.detail || 'Batch delete operation failed.');
            }
            // Assuming backend returns a success message or status
            // const result = await response.json();
            // alert(result.message || `${selectedProfileIds.value.length} profiles deleted successfully.`);
            fetchProfiles(pagination.current_page); // Refresh list
            selectedProfileIds.value = []; // Clear selection
        } catch (e: any) {
            error.value = e.message; // Display error on main page
            // alert("Error during batch delete: " + e.message); // Or use a notification system
        } finally {
            loading.value = false;
        }
    }
};

const openBatchAssignGroupModal = () => {
  if (selectedProfileIds.value.length === 0) {
    alert('No profiles selected to assign to a group.');
    return;
  }
  selectedGroupIdForBatchAssign.value = null; // Reset previous selection in modal
  batchAssignError.value = null; // Clear previous modal errors
  showAssignGroupModal.value = true;
};

const submitBatchAssignGroup = async () => {
  // selectedGroupIdForBatchAssign can be 0 for "Unassign"
  if (selectedGroupIdForBatchAssign.value === null) {
    batchAssignError.value = "Please select a group to assign, or choose 'Unassign'.";
    return;
  }
  if (selectedProfileIds.value.length === 0) { // Should be prevented by button disable state
    batchAssignError.value = "No profiles selected.";
    return;
  }

  // loading.value = true; // Can use a modal-specific loader if preferred
  batchAssignError.value = null;

  try {
    const response = await fetch(`${API_BASE_URL}/profiles/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'assign_group',
        profile_ids: selectedProfileIds.value,
        // Send null to backend if 'Unassign' (value 0) is selected
        group_id: selectedGroupIdForBatchAssign.value === 0 ? null : selectedGroupIdForBatchAssign.value,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Batch assign group failed. Server error.' }));
      throw new Error(errorData.detail || 'Batch assign group operation failed.');
    }
    // const result = await response.json();
    // alert(result.message || "Profiles successfully assigned to group.");

    fetchProfiles(pagination.current_page); // Refresh the list to show updated group assignments
    selectedProfileIds.value = []; // Clear selection
    showAssignGroupModal.value = false; // Close modal

  } catch (e: any) {
    batchAssignError.value = e.message; // Show error within the modal
  } finally {
    // loading.value = false;
  }
};

const launchProfile = async (profileId: number) => {
  loading.value = true; // Optional: show a general loading state for the view
  launchStatus.profile_id = profileId;
  launchStatus.message = 'Initiating launch...'; // Initial message
  launchStatus.command = null;
  launchStatus.error = null;
  showLaunchStatusModal.value = true; // Open modal immediately with initial message

  try {
    const response = await fetch(`${API_BASE_URL}/profiles/${profileId}/launch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }, // Good practice, though no body for this one
    });

    const responseData = await response.json();

    if (!response.ok) {
      // Assuming backend returns error in responseData.detail
      launchStatus.error = responseData.detail || `Failed to launch profile (status ${response.status}).`;
      launchStatus.message = 'Launch Failed.'; // Overwrite initial message
      // No command to show on failure usually
      throw new Error(launchStatus.error); // Throw to be caught by catch block for consistent error handling
    }

    launchStatus.message = responseData.message;
    launchStatus.command = responseData.command;
    // If command is null and message indicates an issue (like exec not found), mark as error for styling
    if (responseData.command === null && (responseData.message.includes("not found") || responseData.message.includes("failed"))) {
        launchStatus.error = responseData.message; // Use the message as the error detail
    }

    // Update last_launch_time in the UI
    const profileIndex = profiles.value.findIndex(p => p.id === profileId);
    if (profileIndex !== -1) {
      // Create a new object to ensure reactivity for the specific item
      // This is a client-side approximation. Backend already updated its record.
      // For full accuracy, one might re-fetch the specific profile or the list.
      profiles.value[profileIndex] = {
        ...profiles.value[profileIndex],
        last_launch_time: new Date().toISOString(),
      };
    }

  } catch (e: any) {
    // Error already set if it was an HTTP error with JSON detail
    if (!launchStatus.error) { // If error was not set from response.json().detail
        launchStatus.error = e.message || 'An unexpected error occurred during launch.';
    }
    if (!launchStatus.message || launchStatus.message === 'Initiating launch...') {
      launchStatus.message = 'Launch Failed.'; // Ensure message reflects failure
    }
  } finally {
    loading.value = false; // Optional: stop general loading state
    // Modal remains open until user closes it
  }
};


onMounted(() => {
  fetchSelectableData(); // For dropdowns
  fetchProfiles(); // Initial profile list
});

// Reset dependent UI elements if selection is cleared
watch(selectedProfileIds, (newSelection) => {
    if (newSelection.length === 0) {
        // No specific action needed here now as selectedBatchAction is removed
    }
});

// When modal for assign group is closed, reset its specific state
watch(showAssignGroupModal, (isVisible) => {
    if (!isVisible) {
        selectedGroupIdForBatchAssign.value = null;
        batchAssignError.value = null;
    }
});

</script>

<style scoped>
/* Styles from previous ProfilesView (mock data version) are largely compatible */
/* Add new styles or adjust existing ones as needed */
.profiles-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px; /* Reduced gap a bit */
}

.top-operations {
  display: flex;
  gap: 8px; /* Reduced gap */
  align-items: center;
  margin-bottom: 15px; /* Reduced margin */
  flex-wrap: wrap;
}

.top-operations button,
.top-operations select,
.top-operations input {
  padding: 8px 10px; /* Adjusted padding */
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 14px;
}
.top-operations button { cursor: pointer; }
.top-operations button:disabled { cursor: not-allowed; opacity: 0.6; }


.primary-button {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}
.primary-button:hover:not(:disabled) {
  background-color: #40a9ff;
}

.action-button { /* General action buttons in table etc. */
  padding: 4px 8px;
  margin-right: 5px;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  cursor: pointer;
  background-color: #fff;
  font-size: 13px;
}
.action-button:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}
.action-button.danger {
  color: #ff4d4f;
  border-color: #ff4d4f;
}
.action-button.danger:hover:not(:disabled) {
  color: #fff;
  background-color: #ff4d4f;
}
.launch-button:hover:not(:disabled) { /* Specific hover for launch */
    background-color: #e6f7ff;
}


.name-search-input {
  min-width: 200px;
}

.profiles-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.1);
  font-size: 13px; /* Smaller font for table */
}

.profiles-table th,
.profiles-table td {
  border: 1px solid #e8e8e8;
  padding: 8px 10px; /* Adjusted padding */
  text-align: left;
  word-break: break-all;
}

.profiles-table th {
  background-color: #fafafa;
  font-weight: 500;
  color: rgba(0,0,0,.85);
}

.profiles-table tbody tr:hover {
  background-color: #f5f5f5;
}
.profiles-table input[type="checkbox"] {
    cursor: pointer;
}

.pagination-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  margin-top: 15px;
}
.pagination-controls button {
  padding: 0 12px;
  height: 32px;
  line-height: 30px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background-color: #fff;
  cursor: pointer;
}
.pagination-controls button:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}
.pagination-controls button:hover:not(:disabled) {
  border-color: #1890ff;
  color: #1890ff;
}
.pagination-controls span {
  font-size: 14px;
}

/* Launch Status Modal Styles */
.launch-status-modal {
    padding: 20px;
    text-align: center;
}
.launch-status-modal h3 {
    margin-top: 0;
    margin-bottom: 15px;
}
.launch-status-modal pre {
    white-space: pre-wrap;
    word-break: break-all;
    background-color: #f5f5f5;
    padding: 10px;
    border-radius: 4px;
    text-align: left;
    max-height: 200px;
    overflow-y: auto;
    font-size: 0.8em;
}
.modal-success { color: green; }
.modal-error { color: red; } /* Also used by form modal error */

.command-display {
  background-color: #2d2d2d; /* Darker background for command */
  color: #f0f0f0; /* Light text */
  padding: 10px 15px;
  border-radius: 4px;
  border: 1px solid #444; /* Darker border */
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'Courier New', Courier, monospace; /* Monospace font */
  font-size: 0.85em; /* Slightly larger for readability */
  margin-top: 10px; /* Space above command block */
}

.launch-status-modal .modal-actions {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
}
</style>
