<template>
  <header class="app-header">
    <div class="breadcrumbs">
      <!-- Basic breadcrumb, will be dynamic later -->
      <span v-for="(crumb, index) in breadcrumbs" :key="index">
        <router-link v-if="crumb.to" :to="crumb.to">{{ crumb.text }}</router-link>
        <span v-else>{{ crumb.text }}</span>
        <span v-if="index < breadcrumbs.length - 1" class="separator"> / </span>
      </span>
      <span v-if="breadcrumbs.length === 0 && $route.path !== '/'">Dashboard</span>
      <span v-else-if="breadcrumbs.length === 0 && $route.path === '/'">Browser Profiles</span>


    </div>
    <div class="header-actions">
      <button class="action-icon" title="Notifications">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
        <!-- Add notification count badge if needed -->
      </button>
      <div class="user-menu" title="User Menu">
        <img src="https://ui-avatars.com/api/?name=User&background=0D8ABC&color=fff&size=32&rounded=true" alt="User Avatar" class="avatar" />
        <span>Username</span> <!-- Replace with actual username later -->
        <!-- Add dropdown for user actions later -->
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, RouterLink, RouteLocationMatched } from 'vue-router';

const route = useRoute();

interface BreadcrumbItem {
  text: string;
  to?: string;
}

const breadcrumbs = computed(() => {
  const matched: RouteLocationMatched[] = route.matched;
  const crumbs: BreadcrumbItem[] = [];

  // Handle default redirect from '/' to '/profiles' specifically for breadcrumb
  if (route.path === '/profiles' && matched.length > 0 && matched[0].path === '/profiles') {
     if (matched[0].meta?.breadcrumb) {
        crumbs.push({ text: matched[0].meta.breadcrumb as string });
     } else if (matched[0].name) {
        crumbs.push({ text: matched[0].name as string });
     }
     return crumbs;
  }

  matched.forEach(m => {
    const breadcrumbText = m.meta?.breadcrumb as string || m.name as string;
    if (breadcrumbText) {
      // Only add to if it's not the current page itself
      if (m.path !== route.path) {
        crumbs.push({ text: breadcrumbText, to: m.path });
      } else {
        crumbs.push({ text: breadcrumbText });
      }
    }
  });
  return crumbs;
});

</script>

<style scoped>
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px; /* Standard header height */
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
  z-index: 10; /* Ensure header is above content if overlapping occurs */
}
.breadcrumbs {
  font-size: 14px;
  color: rgba(0,0,0,.45); /* Ant Design breadcrumb color */
}
.breadcrumbs a {
  color: rgba(0,0,0,.45);
  text-decoration: none;
  transition: color .3s;
}
.breadcrumbs a:hover {
  color: #1890ff; /* Ant Design primary color */
}
.breadcrumbs .separator {
  margin: 0 8px;
  color: rgba(0,0,0,.45);
}
.breadcrumbs span:last-child > span.separator { /* Hide last separator */
    display: none;
}
.breadcrumbs span:last-child > a, /* Last item if it's a link (should not happen with logic) */
.breadcrumbs span:last-child > span { /* Last item if it's plain text */
    color: rgba(0,0,0,.85); /* Ant Design current page breadcrumb color */
    font-weight: 500;
}


.header-actions {
  display: flex;
  align-items: center;
  gap: 24px; /* Increased gap */
}
.action-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0; /* Removed padding for pure icon feel */
  color: rgba(0,0,0,.65);
  display: flex; /* For centering icon if needed */
  align-items: center;
  justify-content: center;
  height: 100%; /* Fill header height for click area if desired */
}
.action-icon svg {
    width: 20px;
    height: 20px;
}
.action-icon:hover {
  color: #1890ff;
}
.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: rgba(0,0,0,.85);
}
.user-menu:hover span {
    color: #1890ff;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover; /* Ensure placeholder/image covers well */
}
</style>
