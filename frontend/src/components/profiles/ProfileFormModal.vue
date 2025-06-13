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
            <label for="profileNotes">Notes:</label>
            <textarea id="profileNotes" v-model="formData.notes" rows="2"></textarea>
          </div>
          <div>
            <label for="profileGroup">Group:</label>
            <select id="profileGroup" v-model="formData.group_id">
              <option :value="null">No Group</option>
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
           <!-- TODO: Add os_version selectors for linux/macos if distinct versions are supported by kernel flags -->
          <div>
            <label for="profileBrowserVersion">Browser Version (e.g., 119.0.6045.123):</label>
            <input type="text" id="profileBrowserVersion" v-model="formData.browser_version" placeholder="Corresponds to --fingerprint-brand-version" />
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
              <button type="button" :class="{active: formData.proxy_config_type === 'default'}" @click="setProxyConfigType('default')">System Default</button>
              <button type="button" :class="{active: formData.proxy_config_type === 'none'}" @click="setProxyConfigType('none')">No Proxy</button>
              <button type="button" :class="{active: formData.proxy_config_type === 'custom'}" @click="setProxyConfigType('custom')">Custom Proxy</button>
            </div>
          </div>
          <div v-if="formData.proxy_config_type === 'custom'">
            <label for="profileProxy">Select Existing Proxy:</label>
            <select id="profileProxy" v-model="formData.custom_proxy_id">
              <option :value="null">Select a Proxy</option>
              <option v-for="proxy in availableProxies" :key="proxy.id" :value="proxy.id">
                {{ proxy.name ? `${proxy.name} (${proxy.type}://${proxy.host}:${proxy.port})` : `${proxy.type}://${proxy.host}:${proxy.port}` }}
              </option>
            </select>
            <p class="small-text">Manage proxies in the <router-link to="/proxies" @click="closeModal">Proxy Management</router-link> page.</p>
          </div>
        </fieldset>

        <!-- Advanced Settings -->
        <fieldset>
          <legend>Advanced Fingerprint Settings</legend>
          <div>
            <label for="profileStartupHomepage">Startup Homepage URL:</label>
            <input type="text" id="profileStartupHomepage" v-model="formData.startup_homepage" placeholder="e.g., https://www.google.com" />
          </div>
          <div>
            <label for="profileFingerprintSeed">Fingerprint Seed (Integer, Optional):</label>
            <input type="number" id="profileFingerprintSeed" v-model.number="formData.fingerprint_seed" placeholder="Leave blank for random default" />
          </div>

          <!-- User-Agent -->
          <div>
            <label>User-Agent:</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.user_agent_mode === 'default'}" @click="formData.user_agent_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.user_agent_mode === 'custom'}" @click="formData.user_agent_mode = 'custom'">Custom</button>
              <!-- <button type="button" :class="{active: formData.user_agent_mode === 'random'}" @click="formData.user_agent_mode = 'random'">Random (via Seed)</button> -->
            </div>
            <textarea v-if="formData.user_agent_mode === 'custom'" v-model="formData.user_agent_custom" placeholder="Enter custom User-Agent string" rows="2"></textarea>
          </div>

          <!-- Sec-CH-UA -->
          <div>
            <label>Sec-CH-UA Client Hints:</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.sec_ch_ua_mode === 'default'}" @click="formData.sec_ch_ua_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.sec_ch_ua_mode === 'custom'}" @click="formData.sec_ch_ua_mode = 'custom'">Custom</button>
              <!-- <button type="button" :class="{active: formData.sec_ch_ua_mode === 'random'}" @click="formData.sec_ch_ua_mode = 'random'">Random (via Seed)</button> -->
            </div>
            <textarea v-if="formData.sec_ch_ua_mode === 'custom'" v-model="formData.sec_ch_ua_custom" placeholder="e.g., &quot;Not_A Brand&quot;;v=&quot;99&quot;, &quot;Chromium&quot;;v=&quot;119&quot;" rows="2"></textarea>
          </div>

          <!-- WebGL Image - Placeholder for now, as custom hash input is not defined yet -->
          <!-- <div>
            <label>WebGL Image Hash:</label>
             <div class="button-group">
              <button type="button" :class="{active: formData.webgl_image_mode === 'default'}" @click="formData.webgl_image_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.webgl_image_mode === 'random'}" @click="formData.webgl_image_mode = 'random'">Random (via Seed)</button>
            </div>
          </div> -->

          <!-- WebGL Metadata -->
          <div>
            <label>WebGL Metadata (Vendor/Renderer - Linux Only):</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.webgl_metadata_mode === 'default'}" @click="formData.webgl_metadata_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.webgl_metadata_mode === 'custom'}" @click="formData.webgl_metadata_mode = 'custom'">Custom</button>
              <!-- <button type="button" :class="{active: formData.webgl_metadata_mode === 'random'}" @click="formData.webgl_metadata_mode = 'random'">Random (via Seed)</button> -->
            </div>
            <div v-if="formData.webgl_metadata_mode === 'custom'">
              <input type="text" v-model="formData.webgl_vendor" placeholder="WebGL Vendor (e.g., Google Inc.)" />
              <input type="text" v-model="formData.webgl_renderer" placeholder="WebGL Renderer (e.g., ANGLE)" style="margin-top:5px;" />
            </div>
             <p v-if="formData.os_platform !== 'linux' && formData.webgl_metadata_mode === 'custom'" class="small-text warning">Note: WebGL Vendor/Renderer override is typically effective on Linux only.</p>
          </div>

          <!-- AudioContext -->
          <div>
            <label>AudioContext Fingerprint:</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.audiocontext_mode === 'default'}" @click="formData.audiocontext_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.audiocontext_mode === 'noise'}" @click="formData.audiocontext_mode = 'noise'">Add Noise</button>
              <button type="button" :class="{active: formData.audiocontext_mode === 'off'}" @click="formData.audiocontext_mode = 'off'">Disable</button>
            </div>
          </div>

          <!-- ClientRects -->
          <div>
            <label>ClientRects Fingerprint:</label>
            <div class="button-group">
              <button type="button" :class="{active: formData.clientrects_mode === 'default'}" @click="formData.clientrects_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.clientrects_mode === 'noise'}" @click="formData.clientrects_mode = 'noise'">Add Noise</button>
               <button type="button" :class="{active: formData.clientrects_mode === 'off'}" @click="formData.clientrects_mode = 'off'">Disable</button>
            </div>
          </div>

          <!-- Speech Voices -->
          <div>
            <label>Speech Voices:</label>
             <div class="button-group">
              <button type="button" :class="{active: formData.speech_voices_mode === 'default'}" @click="formData.speech_voices_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.speech_voices_mode === 'custom'}" @click="formData.speech_voices_mode = 'custom'">Custom</button>
            </div>
            <textarea v-if="formData.speech_voices_mode === 'custom'" v-model="formData.speech_voices_custom_data" placeholder="JSON data for custom speech voices" rows="2"></textarea>
          </div>

          <!-- Hardware Concurrency -->
          <div>
            <label for="profileCpuCores">CPU Cores (hardwareConcurrency):</label>
            <input type="number" id="profileCpuCores" v-model.number="formData.cpu_cores" placeholder="e.g., 4 or 8. Leave blank for default." min="1" />
          </div>
          <div>
            <label for="profileMemoryGb">Memory (deviceMemory GB - Informational):</label>
            <input type="number" id="profileMemoryGb" v_model.number="formData.memory_gb" placeholder="e.g., 8. Kernel might not use directly." min="1" />
          </div>

          <!-- Device Name & MAC Address - Informational for now -->
          <div>
            <label for="profileDeviceName">Device Name (Informational):</label>
            <input type="text" id="profileDeviceName" v-model="formData.device_name" placeholder="e.g., Pixel 5 or CustomPC" />
          </div>
          <div>
            <label for="profileMacAddress">MAC Address (Informational):</label>
            <input type="text" id="profileMacAddress" v-model="formData.mac_address" placeholder="e.g., 00:1A:2B:3C:4D:5E" />
          </div>

          <!-- Toggle Switches -->
          <div class="toggle-switches">
            <label><input type="checkbox" v-model="formData.do_not_track" /> Enable Do Not Track</label>
            <label><input type="checkbox" v-model="formData.hardware_acceleration" /> Enable Hardware Acceleration</label>
            <label><input type="checkbox" v-model="formData.port_scan_protection" /> Enable Port Scan Protection (--disable-non-proxied-udp)</label>
          </div>

          <!-- SSL Cipher Suites -->
          <div>
            <label>SSL Cipher Suites:</label>
             <div class="button-group">
              <button type="button" :class="{active: formData.ssl_cipher_suites_mode === 'default'}" @click="formData.ssl_cipher_suites_mode = 'default'">Default</button>
              <button type="button" :class="{active: formData.ssl_cipher_suites_mode === 'custom'}" @click="formData.ssl_cipher_suites_mode = 'custom'">Custom</button>
              <!-- <button type="button" :class="{active: formData.ssl_cipher_suites_mode === 'strict'}" @click="formData.ssl_cipher_suites_mode = 'strict'">Strict</button> -->
            </div>
            <textarea v-if="formData.ssl_cipher_suites_mode === 'custom'" v-model="formData.ssl_custom_suites_data" placeholder="Comma-separated list of cipher suites" rows="2"></textarea>
          </div>

          <div>
            <label for="profileScanPortWhitelist">Scan Port Whitelist (Comma-separated, for external use):</label>
            <input type="text" id="profileScanPortWhitelist" v-model="formData.scan_port_whitelist" />
          </div>

          <!-- Language, Timezone, etc. already in Basic or here -->
          <div>
            <label for="profileLanguage">Navigator Language (e.g., en-US):</label>
            <input type="text" id="profileLanguage" v-model="formData.language" placeholder="e.g., en-US, fr-FR" />
          </div>
          <div>
            <label for="profileAcceptLanguage">Accept-Language Header:</label>
            <input type="text" id="profileAcceptLanguage" v-model="formData.accept_language" placeholder="e.g., en-US,en;q=0.9" />
          </div>
          <div>
            <label for="profileTimezone">Timezone Override (e.g., America/New_York):</label>
            <input type="text" id="profileTimezone" v-model="formData.timezone" placeholder="e.g., Europe/London, Australia/Sydney" />
          </div>

          <div>
            <label for="profileCustomParams">Custom Launch Parameters:</label>
            <textarea id="profileCustomParams" v-model="formData.custom_launch_parameters" placeholder="e.g., --disable-gpu --some-flag" rows="2"></textarea>
          </div>

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
import { RouterLink } from 'vue-router';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

interface Group { id: number; name: string; }
interface Proxy { id: number; name?: string | null; type: string; host: string; port: number; }

interface ProfileFormData {
  id?: number;
  name: string;
  notes?: string | null;
  group_id?: number | null;

  // Basic
  os_platform?: string | null;
  os_version?: string | null;
  browser_version?: string | null;
  cookies?: string | null;

  // Proxy
  proxy_config_type: 'default' | 'none' | 'custom';
  custom_proxy_id?: number | null;

  // Advanced - General
  startup_homepage?: string | null;
  fingerprint_seed?: number | null;
  custom_launch_parameters?: string | null;

  // Advanced - UA & Client Hints
  user_agent_mode?: string; // default, custom
  user_agent_custom?: string | null;
  sec_ch_ua_mode?: string; // default, custom
  sec_ch_ua_custom?: string | null;

  // Advanced - WebGL
  webgl_image_mode?: string; // default, random (no custom hash input for now)
  webgl_metadata_mode?: string; // default, custom, random
  webgl_vendor?: string | null;
  webgl_renderer?: string | null;

  // Advanced - Other Fingerprints
  audiocontext_mode?: string; // default, noise, off
  clientrects_mode?: string; // default, noise, off
  speech_voices_mode?: string; // default, custom
  speech_voices_custom_data?: string | null;

  // Advanced - Hardware
  cpu_cores?: number | null;
  memory_gb?: number | null; // Informational
  device_name?: string | null; // Informational
  mac_address?: string | null; // Informational

  // Advanced - Toggles/Switches
  do_not_track?: boolean;
  hardware_acceleration?: boolean;
  port_scan_protection?: boolean; // For --disable-non-proxied-udp

  // Advanced - SSL
  ssl_cipher_suites_mode?: string; // default, custom
  ssl_custom_suites_data?: string | null;

  // Advanced - Network Misc
  scan_port_whitelist?: string | null; // Informational for user, not direct flag

  // Advanced - Localization
  language?: string | null; // For --lang
  accept_language?: string | null; // For --accept-lang
  timezone?: string | null; // For --timezone
}

const props = defineProps<{
  visible: boolean;
  profileData?: Partial<ProfileFormData> | null;
}>();

const emit = defineEmits(['close', 'save']);

const initialFormData = (): ProfileFormData => ({
  name: '',
  notes: '',
  group_id: null,
  os_platform: 'windows',
  os_version: '10',
  browser_version: '',
  proxy_config_type: 'default',
  custom_proxy_id: null,
  cookies: '',
  startup_homepage: '',
  fingerprint_seed: null,
  custom_launch_parameters: '',
  user_agent_mode: 'default',
  user_agent_custom: '',
  sec_ch_ua_mode: 'default',
  sec_ch_ua_custom: '',
  webgl_image_mode: 'default',
  webgl_metadata_mode: 'default',
  webgl_vendor: '',
  webgl_renderer: '',
  audiocontext_mode: 'default',
  clientrects_mode: 'default',
  speech_voices_mode: 'default',
  speech_voices_custom_data: '',
  cpu_cores: null,
  memory_gb: null,
  device_name: '',
  mac_address: '',
  do_not_track: false,
  hardware_acceleration: true,
  port_scan_protection: true,
  ssl_cipher_suites_mode: 'default',
  ssl_custom_suites_data: '',
  scan_port_whitelist: '',
  language: 'en-US',
  accept_language: 'en-US,en;q=0.9',
  timezone: '',
});

const formData = reactive<ProfileFormData>(initialFormData());
const availableGroups = ref<Group[]>([]);
const availableProxies = ref<Proxy[]>([]);
const error = ref<string | null>(null);
const isEditMode = computed(() => !!formData.id);

const fetchSelectableData = async () => {
  try {
    const groupsResponse = await fetch(`${API_BASE_URL}/groups?page_size=1000`);
    if (!groupsResponse.ok) throw new Error('Failed to fetch groups for modal');
    availableGroups.value = (await groupsResponse.json()).items;

    const proxiesResponse = await fetch(`${API_BASE_URL}/proxies?page_size=1000`);
    if (!proxiesResponse.ok) throw new Error('Failed to fetch proxies for modal');
    availableProxies.value = (await proxiesResponse.json()).items;
  } catch (e: any) {
    console.error('Error fetching selectable data for modal:', e);
    error.value = 'Could not load groups or proxies. Some dropdowns may be empty.';
  }
};

watch(() => props.visible, (isVisible) => {
  if (isVisible) {
    fetchSelectableData();
    error.value = null;
    if (props.profileData && props.profileData.id) { // Edit mode
      // Deep copy and ensure all fields from initialFormData are present
      const initial = initialFormData();
      const mergedData = { ...initial, ...props.profileData };
      Object.assign(formData, mergedData);
      // Ensure nulls for optional selects if data is missing or 0
      if (!formData.group_id) formData.group_id = null;
      if (!formData.custom_proxy_id) formData.custom_proxy_id = null;
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

const closeModal = () => { emit('close'); };

const handleSubmit = async () => {
  error.value = null;
  if (!formData.name.trim()) {
    error.value = "Profile name is required.";
    return;
  }

  const payload: any = { ...formData };

  // Clean up payload based on modes
  if (payload.user_agent_mode !== 'custom') delete payload.user_agent_custom;
  if (payload.sec_ch_ua_mode !== 'custom') delete payload.sec_ch_ua_custom;
  if (payload.webgl_metadata_mode !== 'custom') {
    delete payload.webgl_vendor;
    delete payload.webgl_renderer;
  }
  if (payload.speech_voices_mode !== 'custom') delete payload.speech_voices_custom_data;
  if (payload.ssl_cipher_suites_mode !== 'custom') delete payload.ssl_custom_suites_data;
  if (payload.proxy_config_type !== 'custom') payload.custom_proxy_id = null;


  const numericFields: (keyof ProfileFormData)[] = ['cpu_cores', 'memory_gb', 'fingerprint_seed'];
  numericFields.forEach(key => {
    if (payload[key] === '' || payload[key] === undefined || payload[key] === null) {
      payload[key] = null;
    } else {
      const numVal = Number(payload[key]);
      payload[key] = isNaN(numVal) ? null : numVal;
    }
  });

  if (payload.group_id === undefined) payload.group_id = null;
  if (payload.custom_proxy_id === undefined) payload.custom_proxy_id = null;

  if (!isEditMode.value) delete payload.id;

  const url = isEditMode.value ? `${API_BASE_URL}/profiles/${formData.id}` : `${API_BASE_URL}/profiles/`;
  const method = isEditMode.value ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: `Request failed with status ${response.status}` }));
      throw new Error(errorData.detail || 'Failed to save profile.');
    }
    emit('save');
    closeModal();
  } catch (e: any) {
    error.value = e.message;
  }
};
</script>

<style scoped>
/* Styles are similar to previous modal, with adjustments for more fields */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(0, 0, 0, 0.65); /* Slightly darker overlay */
  display: flex; justify-content: center; align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white; padding: 20px;
  border-radius: 8px; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
  width: 90%; max-width: 750px; /* Increased width for more fields */
  max-height: 90vh; overflow-y: auto;
  color: #333;
}
.modal-content h2 {
  margin-top: 0; margin-bottom: 20px;
  text-align: center; font-size: 1.3em; /* Adjusted size */
  color: #2c3e50;
}
form fieldset {
  border: 1px solid #dcdfe6; /* Lighter border */
  padding: 12px 15px 15px 15px;
  margin-bottom: 18px;
  border-radius: 4px;
}
form legend {
  font-weight: 600;
  padding: 0 8px;
  font-size: 1.0em;
  color: #303133; /* Darker legend text */
}
form div { margin-bottom: 10px; }
form label {
  display: block; margin-bottom: 5px;
  font-weight: 500; font-size: 0.875em;
  color: #606266; /* Label text color */
}
form input[type="text"],
form input[type="number"],
form input[type="password"], /* Added password type */
form select,
form textarea {
  box-sizing: border-box;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #dcdfe6; /* Input border */
  border-radius: 4px;
  font-size: 0.9em;
  color: #303133;
  background-color: #fff;
}
form input:focus, form select:focus, form textarea:focus {
    border-color: #409eff; /* Focus color */
    box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.2);
}
form textarea {
  min-height: 50px; resize: vertical;
}
.button-group {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}
.button-group button {
  padding: 7px 10px;
  border: 1px solid #dcdfe6;
  background-color: #f4f4f5; /* Lighter button background */
  color: #606266;
  cursor: pointer;
  border-radius: 4px;
  font-size: 0.8em;
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}
.button-group button.active {
  background-color: #409eff; /* Element UI primary blue */
  color: white;
  border-color: #409eff;
}
.button-group button:not(.active):hover {
    border-color: #409eff;
    color: #409eff;
}
.toggle-switches {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
}
.toggle-switches label {
    display: flex;
    align-items: center;
    font-weight: normal; /* Normal weight for checkbox labels */
    font-size: 0.9em;
    color: #606266;
}
.toggle-switches input[type="checkbox"] {
    margin-right: 8px;
    width: auto; /* Override full width for checkbox */
    height: auto; /* Override full width for checkbox */
    cursor: pointer;
}

.modal-actions {
  display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;
  border-top: 1px solid #e4e7ed; /* Separator line */
  padding-top: 20px;
}
.modal-actions button {
    padding: 9px 15px;
    font-size: 0.9em;
    border-radius: 4px;
    cursor: pointer;
}
.modal-actions button[type="button"] { /* Cancel button */
    background-color: #fff;
    border: 1px solid #dcdfe6;
    color: #606266;
}
.modal-actions button[type="button"]:hover {
    color: #409eff;
    border-color: #c6e2ff;
    background-color: #ecf5ff;
}
.primary-button { /* Submit button in actions */
  background-color: #409eff; color: white; border-color: #409eff;
}
.primary-button:hover { background-color: #66b1ff; border-color: #66b1ff;}

.modal-error {
  color: #f56c6c; /* Element UI error red */
  font-size: 0.85em;
  margin-top: 10px;
  text-align: center;
}
.small-text {
    font-size: 0.8em;
    color: #909399; /* Element UI secondary text color */
    margin-top: 4px;
}
.small-text a {
    color: #409eff;
    text-decoration: none;
}
.small-text a:hover {
    text-decoration: underline;
}
.small-text.warning {
    color: #e6a23c; /* Element UI warning color */
}
</style>
