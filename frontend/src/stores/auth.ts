import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    username: localStorage.getItem('username') || '',
  }),
  actions: {
    setLogin(username: string, token: string) {
      this.username = username
      localStorage.setItem('username', username)
      localStorage.setItem('token', token)
    },
    logout() {
      this.username = ''
      localStorage.removeItem('username')
      localStorage.removeItem('token')
    },
  },
})
