import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import api from '../api'

export const useNotificationStore = defineStore('notifications', () => {
  const items = ref([])
  const unread = computed(() => items.value.filter((item) => !item.read).length)

  async function load() {
    try {
      items.value = (await api.get('/notifications', { params: { limit: 20 } })).data
    } catch {
      items.value = []
    }
  }

  async function markRead(id) {
    await api.post('/notifications/' + id + '/read')
    await load()
  }

  async function readAll() {
    await api.post('/notifications/read-all')
    await load()
  }

  return { items, unread, load, markRead, readAll }
})
