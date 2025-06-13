<template>
  <div class="profiles-view">
    <h1>Browser Profiles</h1>

    <div class="top-operations">
      <button class="primary-button">+ Create Browser</button>
      <select class="batch-actions-select">
        <option value="">批量操作 (Batch Actions)</option>
        <option value="delete">Batch Delete</option>
        <option value="assign_group">Batch Assign Group</option>
      </select>
      <button>同步 (Sync)</button>
      <select class="group-filter-select">
        <option value="">All Groups</option>
        <option value="group1">Group 1</option>
        <option value="group2">Group 2</option>
      </select>
      <input type="text" placeholder="Search by name..." class="name-search-input" />
    </div>

    <table class="profiles-table">
      <thead>
        <tr>
          <th><input type="checkbox" /></th>
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
        <tr v-for="profile in mockProfiles" :key="profile.id">
          <td><input type="checkbox" :value="profile.id" /></td>
          <td>{{ profile.id }}</td>
          <td>{{ profile.name }}</td>
          <td>{{ profile.group || '-' }}</td>
          <td>{{ profile.proxy || '-' }}</td>
          <td>{{ profile.notes || '-' }}</td>
          <td>{{ profile.lastLaunchTime || '-' }}</td>
          <td><button class="action-button">Launch</button></td>
          <td>
            <button class="action-button">Edit</button>
            <button class="action-button danger">Delete</button>
          </td>
        </tr>
        <tr v-if="mockProfiles.length === 0">
          <td colspan="9" style="text-align: center;">No profiles found.</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination-controls">
      <span>Page 1 of 10</span>
      <button>&lt; Prev</button>
      <button>Next &gt;</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface MockProfile {
  id: number;
  name: string;
  group?: string;
  proxy?: string;
  notes?: string;
  lastLaunchTime?: string;
}

const mockProfiles = ref<MockProfile[]>([
  {
    id: 1,
    name: 'Work Profile Alpha',
    group: 'Work',
    proxy: '127.0.0.1:1080',
    notes: 'For development tasks',
    lastLaunchTime: '2023-10-26 10:00:00',
  },
  {
    id: 2,
    name: 'Social Media Profile',
    group: 'Personal',
    proxy: 'socks5://user:pass@example.com:5060',
    notes: 'Facebook, Twitter, etc.',
    lastLaunchTime: '2023-10-25 15:30:00',
  },
  {
    id: 3,
    name: 'Research Profile',
    notes: 'Academic research',
    lastLaunchTime: '2023-10-24 09:15:00',
  },
]);

</script>

<style scoped>
.profiles-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px; /* Adds space between elements like H1, top-operations, table, pagination */
}

.top-operations {
  display: flex;
  gap: 10px;
  align-items: center;
  /* margin-bottom: 20px; Removed as parent flex gap handles spacing */
  flex-wrap: wrap; /* Allow wrapping on smaller screens */
}

.top-operations button,
.top-operations select,
.top-operations input {
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.primary-button {
  background-color: #1890ff;
  color: white;
  border-color: #1890ff;
}

.primary-button:hover {
  background-color: #40a9ff;
}

.name-search-input {
  min-width: 200px;
}

.profiles-table {
  width: 100%;
  border-collapse: collapse;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
}

.profiles-table th,
.profiles-table td {
  border: 1px solid #e8e8e8;
  padding: 10px 12px;
  text-align: left;
  font-size: 14px;
  word-break: break-all; /* Helps prevent long strings from breaking layout */
}

.profiles-table th {
  background-color: #f8f8f8;
  font-weight: 600;
}

.profiles-table tbody tr:hover {
  background-color: #f5f5f5;
}

.action-button {
  padding: 5px 10px;
  margin-right: 5px;
  border: 1px solid #ccc;
  border-radius: 3px;
  cursor: pointer;
  background-color: #fff;
  font-size: 13px; /* Slightly smaller for action buttons */
}

.action-button.danger {
  color: #fff;
  background-color: #ff4d4f;
  border-color: #ff4d4f;
}

.action-button.danger:hover {
  background-color: #ff7875;
}

.action-button:hover {
  border-color: #1890ff;
  /* color: #1890ff; Optional: change text color on hover for non-danger buttons */
}

.pagination-controls {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  /* margin-top: 20px; Removed as parent flex gap handles spacing */
}

.pagination-controls button {
  padding: 6px 10px;
  border: 1px solid #ccc;
  border-radius: 3px;
  background-color: #fff;
  cursor: pointer;
}
.pagination-controls button:hover {
  border-color: #1890ff;
}

.pagination-controls span {
  font-size: 14px;
}
</style>
