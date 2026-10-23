<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="notfound">
    <p class="code">404</p>
    <h1>页面不存在</h1>
    <p class="muted">链接可能已失效，或你没有访问权限。</p>
    <el-button type="primary" @click="router.push('/drawings')">回到图纸</el-button>
  </div>
</template>

<style scoped>
.notfound { min-height: 60vh; display: grid; place-content: center; justify-items: center; gap: 8px; text-align: center; }
.code { font-size: 72px; font-weight: 800; color: #dbeafe; margin: 0; letter-spacing: -.04em; }
h1 { margin: 0; }
</style>
