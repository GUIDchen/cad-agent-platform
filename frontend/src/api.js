import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

api.interceptors.request.use((config) => {
  const user = localStorage.getItem('user')
  if (user) config.headers['X-User'] = user
  const csrf = document.cookie.split('; ').find((row) => row.startsWith('csrf_token='))
  if (csrf) config.headers['X-CSRF-Token'] = csrf.split('=')[1]
  return config
})

api.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const detail = error.response?.data?.detail
    const message = detail?.message || detail || error.message
    if (error.response?.status === 401) {
      localStorage.removeItem('user')
      if (location.pathname !== '/login') location.href = '/login'
    }
    return Promise.reject(new Error(typeof message === 'string' ? message : '请求失败'))
  }
)

export default api
