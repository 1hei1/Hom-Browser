import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import ProfilesView from '../views/ProfilesView.vue';
import GroupsView from '../views/GroupsView.vue';
import PluginsView from '../views/PluginsView.vue';
import ProxiesView from '../views/ProxiesView.vue';
import ApiDocsView from '../views/ApiDocsView.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/profiles',
    // No name needed for redirect, or it won't be shown in breadcrumbs usually
  },
  {
    path: '/profiles',
    name: 'Browser Profiles', // Changed for breadcrumb
    component: ProfilesView,
    // meta: { breadcrumb: 'Browser Profiles' } // Alternative if name needs to be programmatic
  },
  {
    path: '/groups',
    name: 'Group Management', // Human-readable name
    component: GroupsView,
  },
  {
    path: '/plugins',
    name: 'Plugin Management', // Human-readable name
    component: PluginsView,
  },
  {
    path: '/proxies',
    name: 'Proxy Management', // Human-readable name
    component: ProxiesView,
  },
  {
    path: '/api-docs',
    name: 'API Documentation', // Human-readable name
    component: ApiDocsView,
  },
  // Example of a 404 route:
  // {
  //   path: '/:pathMatch(.*)*',
  //   name: 'Page Not Found',
  //   component: () => import('../views/NotFoundView.vue') // Lazy load 404
  // },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // always scroll to top
    return { top: 0 }
  }
});

export default router;
