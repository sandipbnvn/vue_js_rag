import { createRouter, createWebHistory } from 'vue-router'
import Chat from '@/views/Chat.vue'
import Upload from '@/views/Upload.vue'
import History from '@/views/History.vue'

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload
  },
  {
    path: '/history',
    name: 'History',
    component: History
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 