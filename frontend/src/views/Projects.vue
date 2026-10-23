<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PageHeader from '../components/PageHeader.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'

const { t } = useI18n()
const projects = ref([])
const createDialog = ref(false)
const memberDialog = ref(false)
const current = ref(null)
const members = ref([])
const users = ref([])
const form = reactive({ name: '' })
const addForm = reactive({ user_id: null, role: 'member' })

async function load() {
  projects.value = (await api.get('/projects')).data
}

async function create() {
  if (!form.name) return
  await api.post('/projects', { name: form.name })
  form.name = ''
  createDialog.value = false
  ElMessage.success('项目已创建')
  await load()
}

async function openMembers(project) {
  current.value = project
  memberDialog.value = true
  users.value = (await api.get('/users/options')).data
  await refreshMembers()
}

async function refreshMembers() {
  members.value = (await api.get('/projects/' + current.value.id + '/members')).data
}

async function addMember() {
  if (!addForm.user_id) {
    ElMessage.warning('请选择用户')
    return
  }
  await api.post('/projects/' + current.value.id + '/members', addForm)
  addForm.user_id = null
  await refreshMembers()
}

async function updateRole(member, role) {
  try {
    await api.patch('/projects/' + current.value.id + '/members/' + member.user_id, { role })
    ElMessage.success('角色已更新')
    await refreshMembers()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function removeMember(member) {
  await ElMessageBox.confirm('移除成员 ' + member.user_name + '？')
  await api.delete('/projects/' + current.value.id + '/members/' + member.user_id)
  await refreshMembers()
}

onMounted(load)
</script>

<template>
  <div>
    <PageHeader :title="t('projects.title')" :subtitle="t('projects.subtitle')">
      <el-button type="primary" @click="createDialog = true">{{ t('projects.new') }}</el-button>
    </PageHeader>

    <el-table :data="projects">
      <el-table-column prop="id" :label="t('projects.id')" width="70" />
      <el-table-column prop="name" :label="t('projects.name')" />
      <el-table-column prop="owner_id" :label="t('projects.owner')" width="100" />
      <el-table-column prop="status" :label="t('projects.status')" width="100" />
      <el-table-column :label="t('projects.actions')" width="120">
        <template #default="{ row }">
          <el-button link @click="openMembers(row)">{{ t('projects.members') }}</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createDialog" :title="t('projects.dialogTitle')" width="420px">
      <el-input v-model="form.name" :placeholder="t('projects.projectName')" />
      <template #footer>
        <el-button @click="createDialog = false">{{ t('projects.cancel') }}</el-button>
        <el-button type="primary" @click="create">{{ t('projects.create') }}</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="memberDialog" :title="t('projects.memberTitle') + ' · ' + (current?.name || '')" width="620px">
      <el-table :data="members" size="small">
        <el-table-column prop="user_id" :label="t('projects.user')" width="90" />
        <el-table-column prop="user_name" :label="t('projects.userName')" />
        <el-table-column :label="t('projects.role')" width="130">
          <template #default="{ row }">
            <el-select :model-value="row.role" size="small" @change="(v) => updateRole(row, v)">
              <el-option :label="t('projects.ownerRole')" value="owner" />
              <el-option :label="t('projects.member')" value="member" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column :label="t('projects.actions')" width="90">
          <template #default="{ row }">
            <el-button link type="danger" @click="removeMember(row)">{{ t('projects.remove') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="add">
        <el-select v-model="addForm.user_id" :placeholder="t('projects.selectUser')" style="width: 180px">
          <el-option v-for="u in users" :key="u.id" :label="u.name" :value="u.id" />
        </el-select>
        <el-select v-model="addForm.role" style="width: 110px; margin-left: 8px">
          <el-option :label="t('projects.member')" value="member" />
          <el-option :label="t('projects.ownerRole')" value="owner" />
        </el-select>
        <el-button type="primary" style="margin-left: 8px" @click="addMember">{{ t('projects.add') }}</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.add { margin-top: 16px; display: flex; }
</style>
