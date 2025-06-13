<template>
  <div v-if="visible" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      <h2>{{ isEditMode ? 'Edit Browser Profile' : 'Create New Browser Profile' }}</h2>
      <form @submit.prevent="handleSubmit">
        <!-- Basic Settings -->
        <fieldset>
          <legend>Basic Settings</legend>
          <div>
            <label for="profileName">Name:</label>
            <input type="text" id="profileName" v-model="formData.name" required />
          </div>
          <div>
            <label for="profileGroup">Group:</label>
            <select id="profileGroup" v-model="formData.group_id">
              <option :value="null">No Group</option>
              <option :value="undefined">No Group (compat)</option> <!-- For existing data that might have undefined -->
              <option v-for="group in availableGroups" :key="group.id" :value="group.id">
                {{ group.name }}
              </option>
            </select>
          </div>
          <div>
            <label for="profileOS">Operating System:</label>
            <select id="profileOS" v-model="formData.os_platform">
              <option value="windows">Windows</option>
              <option value="linux">Linux</option>
              <option value="macos">MacOS</option>
            </select>
          </div>
          <div v-if="formData.os_platform === 'windows'">
             <label for="profileOsVersionWin">Windows Version:</label>
             <select id="profileOsVersionWin" v-model="formData.os_version">
                 <option value="11">Windows 11</option>
                 <option value="10">Windows 10</option>
                 <option value="8.1">Windows 8.1</option>
                 <option value="7">Windows 7</option>
             </select>
          </div>
          <!-- TODO: Add os_version selectors for linux/macos if distinct versions are supported -->
          <div>
            <label for="profileBrowserVersion">Browser Version:</label>
            <input type="text" id="profileBrowserVersion" v-model="formData.browser_version" placeholder="e.g., 119.0.6045.123" />
          </div>
          <div>
             <label for="profileNotes">Notes:</label>
             <textarea id="profileNotes" v-model="formData.notes" rows="2"></textarea>
          </div>
          <div>
             <label for="profileCookies">Cookies (JSON/Netscape or Semicolon separated):</label>
             <textarea id="profileCookies" v-model="formData.cookies" rows="3"></textarea>
          </div>
        </fieldset>

        <!-- Proxy Settings -->
        <fieldset>
          <legend>Proxy Settings</legend>
          <div>
            <label>Proxy Configuration:</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.proxy_config_type === 'default'}" @click="setProxyConfigType('default')">Default From System</button>
              <button type="button" :class="{active: formData.proxy_config_type === 'none'}" @click="setProxyConfigType('none')">No Proxy</button>
              <button type="button" :class="{active: formData.proxy_config_type === 'custom'}" @click="setProxyConfigType('custom')">Custom Proxy</button>
            </div>
          </div>
          <div v-if="formData.proxy_config_type === 'custom'">
            <label for="profileProxy">Select Existing Proxy:</label>
            <select id="profileProxy" v-model="formData.custom_proxy_id">
              <option :value="null">Select a Proxy</option>
              <option :value="undefined">Select a Proxy (compat)</option>
              <option v-for="proxy in availableProxies" :key="proxy.id" :value="proxy.id">
                {{ proxy.name ? `${proxy.name} (${proxy.type}://${proxy.host}:${proxy.port})` : `${proxy.type}://${proxy.host}:${proxy.port}` }}
              </option>
            </select>
            <p class="small-text">Manage proxies in the <router-link to="/proxies" @click="closeModal">Proxy Management</router-link> page.</p>
          </div>
        </fieldset>

        <!-- Advanced Settings (Placeholder for now) -->
        <fieldset>
          <legend>Advanced Fingerprint Settings (Partial - More Coming Soon)</legend>
            <div>
                <label for="profileStartupHomepage">Startup Homepage URL:</label>
                <input type="text" id="profileStartupHomepage" v-model="formData.startup_homepage" placeholder="e.g., https://www.google.com" />
            </div>
            <div>
                <label for="profileUserAgent">User-Agent (Override):</label>
                <input type="text" id="profileUserAgent" v-model="formData.user_agent" placeholder="Full User-Agent string" />
            </div>
             <div>
                <label for="profileLanguage">Language (e.g., en-US):</label>
                <input type="text" id="profileLanguage" v-model="formData.language" placeholder="e.g., en-US, fr-FR" />
            </div>
            <div>
                <label for="profileTimezone">Timezone (e.g., America/New_York):</label>
                <input type="text" id="profileTimezone" v-model="formData.timezone" placeholder="e.g., Europe/London" />
            </div>
             <div>
                <label for="profileCustomParams">Custom Launch Parameters:</label>
                <input type="text" id="profileCustomParams" v-model="formData.custom_launch_parameters" placeholder="e.g., --disable-gpu --some-flag" />
            </div>


          <p style="text-align:center; color:#777;">More specific fingerprint settings (WebGL, Canvas, Fonts, Audio, etc.) will be added here.</p>
        </fieldset>

        <div class="modal-actions">
          <button type="button" @click="closeModal">Cancel</button>
          <button type="submit" class="primary-button">{{ isEditMode ? 'Save Changes' : 'Create Profile' }}</button>
        </div>
        <p v-if="error" class="modal-error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { RouterLink } from 'vue-router'; // Import for template usage

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Group {
  id: number;
  name: string;
}

interface Proxy {
  id: number;
  name?: string | null;
  type: string;
  host: string;
  port: number;
}

// This should align with schemas.Profile and schemas.ProfileCreate/Update
interface ProfileFormData {
  id?: number;
  name: string;
  notes?: string | null;
  group_id?: number | null;
  os_platform?: string | null;
  os_version?: string | null;
  browser_version?: string | null;
  proxy_config_type: 'default' | 'none' | 'custom';
  custom_proxy_id?: number | null;
  cookies?: string | null;

  language?: string | null;
  accept_language?: string | null; // Will need a dedicated input if complex
  timezone?: string | null;
  fingerprint_seed?: number | null; // Usually auto-generated or for advanced users
  startup_homepage?: string | null;

  user_agent?: string | null;
  sec_ch_ua?: string | null; // Usually derived or for advanced override

  // Simplified fingerprinting aspects for now
  webgl_image_mode?: string;
  webgl_vendor?: string | null;
  webgl_renderer?: string | null;
  audiocontext_mode?: string;
  clientrects_mode?: string;
  speech_voices_mode?: string;
  cpu_cores?: number | null;
  memory_gb?: number | null;
  device_name?: string | null; // For mobile emulation etc.
  mac_address?: string | null; // If supported

  // Switches
  do_not_track?: boolean;
  ssl_cipher_suites_mode?: string; // Simplified
  port_scan_protection?: boolean;
  hardware_acceleration?: boolean;
  scan_port_whitelist?: string | null; // Comma-separated
  custom_launch_parameters?: string | null;
}

const props = defineProps<{
  visible: boolean;
  profileData?: Partial<ProfileFormData> | null; // Use Partial for editing
}>();

const emit = defineEmits(['close', 'save']);

const initialFormData = (): ProfileFormData => ({
  name: '',
  notes: '',
  group_id: null,
  os_platform: 'windows',
  os_version: '10', // Default for Windows
  browser_version: '',
  proxy_config_type: 'default',
  custom_proxy_id: null,
  cookies: '',
  language: 'en-US', // Sensible default
  accept_language: 'en-US,en;q=0.9', // Sensible default
  timezone: '', // Best to let user set or auto-detect if possible later
  fingerprint_seed: null,
  startup_homepage: '',
  user_agent: '',
  sec_ch_ua: '',
  webgl_image_mode: 'default',
  webgl_vendor: '',
  webgl_renderer: '',
  audiocontext_mode: 'default',
  clientrects_mode: 'default',
  speech_voices_mode: 'default',
  cpu_cores: null,
  memory_gb: null,
  device_name: '',
  mac_address: '',
  do_not_track: false,
  ssl_cipher_suites_mode: 'default',
  port_scan_protection: true,
  hardware_acceleration: true,
  scan_port_whitelist: '',
  custom_launch_parameters: '',
});

const formData = reactive<ProfileFormData>(initialFormData());

const availableGroups = ref<Group[]>([]);
const availableProxies = ref<Proxy[]>([]);
const error = ref<string | null>(null);

const isEditMode = computed(() => !!formData.id);

const fetchSelectableData = async () => {
  try {
    // Fetch groups
    const groupsResponse = await fetch(`${API_BASE_URL}/groups?page_size=1000`); // Fetch many for dropdown
    if (!groupsResponse.ok) throw new Error('Failed to fetch groups');
    availableGroups.value = (await groupsResponse.json()).items;

    // Fetch proxies
    const proxiesResponse = await fetch(`${API_BASE_URL}/proxies?page_size=1000`); // Fetch many for dropdown
    if (!proxiesResponse.ok) throw new Error('Failed to fetch proxies');
    availableProxies.value = (await proxiesResponse.json()).items;

  } catch (e: any) {
    console.error('Error fetching selectable data:', e);
    error.value = 'Could not load groups or proxies for selection. Please try again later.';
  }
};

onMounted(() => {
  if (props.visible) { // Fetch only if modal becomes visible initially
    fetchSelectableData();
  }
});

watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    fetchSelectableData(); // Fetch fresh data each time modal is opened
    error.value = null; // Clear previous errors
    if (props.profileData) { // Edit mode
      // Create a new object based on profileData to avoid reactivity issues with props
      const dataToEdit = { ...initialFormData(), ...props.profileData };
      Object.assign(formData, dataToEdit);
      // Ensure nulls are correctly set for optional selects
      if (dataToEdit.group_id === undefined || dataToEdit.group_id === 0) formData.group_id = null;
      if (dataToEdit.custom_proxy_id === undefined || dataToEdit.custom_proxy_id === 0) formData.custom_proxy_id = null;
      if (dataToEdit.proxy_config_type === undefined) formData.proxy_config_type = 'default';

    } else { // Create mode
      Object.assign(formData, initialFormData());
    }
  }
});

const setProxyConfigType = (type: 'default' | 'none' | 'custom') => {
    formData.proxy_config_type = type;
    if (type !== 'custom') {
        formData.custom_proxy_id = null;
    }
};

const closeModal = () => {
  emit('close');
};

const handleSubmit = async () => {
  error.value = null;
  if (!formData.name.trim()) {
    error.value = "Profile name is required.";
    return;
  }

  const payload: any = { ...formData };

  // Ensure numeric fields are numbers or null, not empty strings
  const numericFields: (keyof ProfileFormData)[] = ['cpu_cores', 'memory_gb', 'fingerprint_seed'];
  numericFields.forEach(key => {
    if (payload[key] === '' || payload[key] === undefined || payload[key] === null) {
      payload[key] = null; // Send null for empty optional numerics
    } else {
      payload[key] = Number(payload[key]);
      if (isNaN(payload[key] as number)) payload[key] = null; // If somehow NaN, make it null
    }
  });

  // Handle group_id and custom_proxy_id: send null if not set, not 0 or undefined
  if (payload.group_id === undefined || payload.group_id === 0) payload.group_id = null;
  if (payload.custom_proxy_id === undefined || payload.custom_proxy_id === 0) payload.custom_proxy_id = null;


  // If proxy type is not custom, custom_proxy_id should be null
  if (payload.proxy_config_type !== 'custom') {
    payload.custom_proxy_id = null;
  }

  // Remove id from payload for create, it's part of URL for update
  if (!isEditMode.value) {
    delete payload.id;
  }

  // Remove purely client-side or irrelevant fields if any (none in this case yet)

  const url = isEditMode.value ? `${API_BASE_URL}/profiles/${formData.id}` : `${API_BASE_URL}/profiles/`;
  const method = isEditMode.value ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Save operation failed with status: ' + response.status }));
      throw new Error(errorData.detail || `Failed to save profile (status ${response.status}).`);
    }
    emit('save');
    closeModal();
  } catch (e: any) {
    error.value = e.message;
  }
};

</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white; padding: 20px; /* Reduced padding */
  border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  width: 90%; max-width: 700px; /* Max width */
  max-height: 90vh; overflow-y: auto;
  color: #333; /* Default text color for modal content */
}
.modal-content h2 {
  margin-top: 0; margin-bottom: 20px; /* Reduced bottom margin */
  text-align: center; font-size: 1.4em; /* Slightly smaller */
}
form fieldset {
  border: 1px solid #e0e0e0;
  padding: 10px 15px 15px 15px; /* Adjusted padding */
  margin-bottom: 15px; /* Reduced margin */
  border-radius: 4px;
}
form legend {
  font-weight: 600; /* Slightly bolder */
  padding: 0 8px; /* Adjusted padding */
  font-size: 1.0em; /* Slightly smaller */
  color: #1890ff; /* Legend color */
}
form div { /* Applies to direct div children of form or fieldset */
  margin-bottom: 12px; /* Reduced margin */
}
form label {
  display: block; margin-bottom: 4px; /* Reduced margin */
  font-weight: 500; font-size: 0.85em; /* Slightly smaller */
  color: #555;
}
form input[type="text"],
form input[type="number"],
form select,
form textarea {
  box-sizing: border-box; /* Ensure padding/border don't increase width */
  width: 100%; /* Take full width of parent */
  padding: 8px 10px; /* Reduced padding */
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.95em; /* Slightly smaller */
}
form textarea {
  min-height: 50px; resize: vertical;
}
.button-group {
  display: flex;
  gap: 5px;
  margin-top: 5px; /* Space above button group */
}
.button-group button {
  padding: 8px 10px; /* Consistent padding */
  border: 1px solid #ccc;
  background-color: #f0f0f0;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.85em; /* Smaller font for buttons */
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}
.button-group button.active {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}
.button-group button:not(.active):hover {
    border-color: #1890ff;
    color: #1890ff;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; /* Increased top margin */
}
.modal-actions button { /* General style for action buttons */
    padding: 9px 15px;
    font-size: 0.9em;
    border-radius: 4px;
    cursor: pointer;
    border: 1px solid #d9d9d9;
}
.modal-actions button[type="button"] { /* Cancel button */
    background-color: #fff;
}
.modal-actions button[type="button"]:hover {
    border-color: #1890ff;
    color: #1890ff;
}
.primary-button { /* Submit button */
  background-color: #1890ff; color: white; border-color: #1890ff;
}
.primary-button:hover { background-color: #40a9ff; }

.modal-error {
  color: red; font-size: 0.85em; /* Smaller font */
  margin-top: 12px; /* Reduced margin */
  text-align: center;
}
.small-text {
    font-size: 0.8em; /* Smaller font */
    color: #777;
    margin-top: 3px; /* Reduced margin */
}
.small-text a {
    color: #1890ff;
    text-decoration: none;
}
.small-text a:hover {
    text-decoration: underline;
}
</style>
