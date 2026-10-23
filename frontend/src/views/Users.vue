<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const { t } = useI18n()
const users = ref([])
const dialog = ref(false)
const form = reactive({ name: '', role: 'viewer' })
const roles = ['admin', 'designer', 'reviewer', 'viewer']

async function load() {
  users.value = (await api.get('/users')).data
}

async function create() {
  if (!form.name) return
  await api.post('/users', form)
  form.name = ''
  dialog.value = false
  ElMessage.success('用户已创建')
  await load()
}

async function updateRole(user, role) {
  await api.patch('/users/' + user.id, { role })
  ElMessage.success('角色已更新')
  await load()
}

async function toggleActive(user, active) {
  await api.patch('/users/' + user.id, { active })
  ElMessage.success(active ? '已启用' : '已禁用')
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="t('users.title')" :subtitle="t('users.subtitle')">
      <el-button type="primary" @click="dialog = true">{{ t('users.new') }}</el-button>
    </PageHeader>

    <el-table :data="users">
      <el-table-column prop="id" :label="t('users.id')" width="70" />
      <el-table-column prop="name" :label="t('users.name')" />
      <el-table-column :label="t('users.role')" width="160">
        <template #default="{ row }">
          <el-select :model-value="row.role" size="small" @change="(v) => updateRole(row, v)">
            <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column :label="t('users.active')" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.active" @change="(v) => toggleActive(row, v)" />
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" :title="t('users.dialogTitle')" width="420px">
      <el-form label-width="70px">
        <el-form-item :label="t('users.name')">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('users.role')">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">{{ t('users.cancel') }}</el-button>
        <el-button type="primary" @click="create">{{ t('users.create') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
