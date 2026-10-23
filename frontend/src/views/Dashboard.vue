<script setup>
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DataLine, Document, Files, Timer } from '@element-plus/icons-vue'
import { useDashboardQuery } from '../queries'

use([CanvasRenderer, PieChart, BarChart, TooltipComponent, LegendComponent, GridComponent])

const { data: stats, isLoading: loading, refetch } = useDashboardQuery()

const kpis = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '图纸', value: s.drawings, icon: Document, color: '#2563eb' },
    { label: '版本', value: s.versions, icon: Files, color: '#0ea5e9' },
    { label: '待审批', value: s.pending_review, icon: Timer, color: '#f59e0b' },
    { label: '已通过', value: s.approved, icon: DataLine, color: '#10b981' },
  ]
})

const pieOption = computed(() => {
  const rows = Object.entries(stats.value?.jobs_by_status || {}).map(([name, value]) => ({ name, value }))
  return {
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, icon: 'circle', textStyle: { color: '#64748b' } },
    series: [
      {
        type: 'pie',
        radius: ['48%', '72%'],
        center: ['50%', '44%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 3 },
        label: { show: false },
        data: rows,
        color: ['#2563eb', '#0ea5e9', '#f59e0b', '#10b981', '#ef4444'],
      },
    ],
  }
})

const approvalOption = computed(() => {
  const s = stats.value
  if (!s) return {}
  return {
    grid: { left: 70, right: 40, top: 20, bottom: 20 },
    xAxis: { type: 'value', show: false },
    yAxis: {
      type: 'category',
      data: ['待审批', '已通过'],
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        barWidth: 18,
        label: { show: true, position: 'right', color: '#475569' },
        data: [
          { value: s.pending_review, itemStyle: { color: '#f59e0b', borderRadius: 8 } },
          { value: s.approved, itemStyle: { color: '#10b981', borderRadius: 8 } },
        ],
      },
    ],
  }
})

const jobRows = computed(() => {
  return Object.entries(stats.value?.jobs_by_status || {}).map(([status, count]) => ({ status, count }))
})


</script>

<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <h1>运营看板</h1>
        <p>图纸、版本、任务与审批的整体运行情况</p>
      </div>
      <div class="page-actions">
        <el-button @click="refetch">刷新</el-button>
      </div>
    </div>

    <div class="kpis">
      <div v-for="item in kpis" :key="item.label" class="kpi">
        <div class="kpi-icon" :style="{ background: item.color + '14', color: item.color }">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <div>
          <div class="kpi-value">{{ item.value }}</div>
          <div class="kpi-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <div class="charts">
      <el-card header="任务状态分布">
        <VChart v-if="jobRows.length" :option="pieOption" class="chart" autoresize />
        <el-empty v-else description="暂无任务" :image-size="80" />
      </el-card>

      <el-card header="审批状态">
        <VChart :option="approvalOption" class="chart" autoresize />
      </el-card>
    </div>

    <el-card header="任务明细" class="table-card">
      <el-table :data="jobRows" size="small">
        <el-table-column prop="status" label="状态" />
        <el-table-column prop="count" label="数量" align="right" />
      </el-table>
      <div class="avg">
        <span>平均任务耗时</span>
        <strong>{{ stats?.avg_job_seconds ?? '-' }} s</strong>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.kpi {
  display: flex; align-items: center; gap: 14px;
  background: #fff; border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 14px; padding: 18px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, .04);
}
.kpi-icon {
  width: 42px; height: 42px; border-radius: 12px;
  display: grid; place-items: center; font-size: 20px;
}
.kpi-value { font-size: 26px; font-weight: 700; line-height: 1.1; letter-spacing: -.02em; }
.kpi-label { color: #64748b; font-size: 12px; margin-top: 4px; }

.charts { display: grid; grid-template-columns: 1.1fr .9fr; gap: 16px; }
.chart { height: 300px; }
.table-card { margin-top: 16px; }
.avg {
  display: flex; justify-content: space-between;
  margin-top: 16px; padding-top: 14px;
  border-top: 1px dashed #e2e8f0; color: #64748b; font-size: 13px;
}

@media (max-width: 900px) {
  .kpis { grid-template-columns: 1fr 1fr; }
  .charts { grid-template-columns: 1fr; }
}
</style>
