import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(localStorage.getItem('user') || '')
  const role = ref(localStorage.getItem('role') || '')

  const isLoggedIn = computed(() => !!user.value)
  const initial = computed(() => (user.value || 'U').slice(0, 1).toUpperCase())

  function setSession(name, nextRole) {
    user.value = name
    role.value = nextRole
    localStorage.setItem('user', name)
    localStorage.setItem('role', nextRole)
  }

  function clear() {
    user.value = ''
    role.value = ''
    localStorage.removeItem('user')
    localStorage.removeItem('role')
  }

  return { user, role, isLoggedIn, initial, setSession, clear }
})
