import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import ProfilesView from '../views/ProfilesView.vue';
import GroupsView from '../views/GroupsView.vue';
import PluginsView from '../views/PluginsView.vue';
import ProxiesView from '../views/ProxiesView.vue';
import ApiDocsView from '../views/ApiDocsView.vue';

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    redirect: '/profiles', // Default route redirects to profiles
  },
  {
    path: '/profiles',
    name: 'Profiles',
    component: ProfilesView,
  },
  {
    path: '/groups',
    name: 'Groups',
    component: GroupsView,
  },
  {
    path: '/plugins',
    name: 'Plugins',
    component: PluginsView,
  },
  {
    path: '/proxies',
    name: 'Proxies',
    component: ProxiesView,
  },
  {
    path: '/api-docs',
    name: 'ApiDocs',
    component: ApiDocsView,
  },
  // Example of a 404 route:
  // {
  //   path: '/:pathMatch(.*)*',
  //   name: 'NotFound',
  //   component: () => import('../views/NotFoundView.vue') // Lazy load 404
  // },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // Vite exposes BASE_URL
  routes,
});

export default router;
