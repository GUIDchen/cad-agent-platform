<script setup>
import { computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useApprovalsQuery, useApproveVersion, useRejectVersion } from '../queries'

const { t } = useI18n()
const { data, isLoading: loading, refetch } = useApprovalsQuery()
const rows = computed(() => data.value || [])
const approveMutation = useApproveVersion()
const rejectMutation = useRejectVersion()

async function approve(row) {
  await ElMessageBox.confirm(t('approvals.approveConfirm') + ' ' + row.drawing_no + ' v' + row.version + '?')
  await approveMutation.mutateAsync({ versionId: row.version_id, comment: 'ok' })
  ElMessage.success('已通过')
}

async function reject(row) {
  const { value } = await ElMessageBox.prompt(t('approvals.rejectPrompt'), t('approvals.rejectTitle'), {
    inputPattern: /\S+/,
    inputErrorMessage: t('approvals.rejectRequired'),
  })
  await rejectMutation.mutateAsync({ versionId: row.version_id, comment: value })
  ElMessage.success('已驳回')
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>{{ t('approvals.title') }}</h1>
        <p>{{ t('approvals.subtitle') }}</p>
      </div>
      <div class="page-actions">
        <el-button @click="refetch">{{ t('approvals.refresh') }}</el-button>
      </div>
    </div>

    <el-card>
      <el-table :data="rows" v-loading="loading">
        <el-table-column prop="drawing_no" :label="t('approvals.drawingNo')" width="170" />
        <el-table-column prop="title" :label="t('approvals.name')" />
        <el-table-column prop="version" :label="t('approvals.version')" width="90" />
        <el-table-column prop="created_at" :label="t('approvals.submitted')" width="190" />
        <el-table-column :label="t('approvals.actions')" width="160" align="right">
          <template #default="{ row }">
            <el-button link type="success" @click="approve(row)">{{ t('approvals.approve') }}</el-button>
            <el-button link type="danger" @click="reject(row)">{{ t('approvals.reject') }}</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty :description="t('approvals.empty')" :image-size="90" />
        </template>
      </el-table>
    </el-card>
  </div>
</template>
