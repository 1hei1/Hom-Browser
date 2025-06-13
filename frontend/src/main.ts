import { createApp } from 'vue'
import './style.css' // This was emptied, but can be kept or removed. Keeping for now.
import App from './App.vue'
import router from './router' // Import the router

const app = createApp(App)

app.use(router) // Use the router

app.mount('#app')
