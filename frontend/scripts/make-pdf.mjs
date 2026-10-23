import { chromium } from '@playwright/test'
import { marked } from 'marked'
import { readFile, writeFile, rm } from 'node:fs/promises'
import path from 'node:path'

const docsDir = path.resolve('../docs')
const mdPath = path.join(docsDir, '38-面试介绍与问答.md')
const tmpPath = path.join(docsDir, '.38-print.html')
const pdfPath = path.join(docsDir, '38-面试介绍与问答.pdf')

let md = await readFile(mdPath, 'utf-8')
md = md.replace(/^#\s+38[^\n]*\n/, '')
const body = marked.parse(md, { gfm: true })

const lines = [
  '<!doctype html>',
  '<html lang="zh-CN">',
  '<head>',
  '<meta charset="utf-8" />',
  '<style>',
  '  @page { size: A4; margin: 16mm 14mm 16mm 14mm; }',
  '  * { box-sizing: border-box; }',
  '  body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: #0f172a; font-size: 10.5pt; line-height: 1.75; margin: 0; }',
  '  .cover { height: 255mm; display: flex; flex-direction: column; justify-content: center; padding: 0 10mm; page-break-after: always; background: linear-gradient(160deg, #0b1220, #111c33 60%, #0b1220); color: #e2e8f0; border-radius: 4mm; }',
  '  .cover .brand { color: #60a5fa; letter-spacing: .22em; font-size: 10pt; font-weight: 700; }',
  '  .cover h1 { font-size: 34pt; line-height: 1.15; margin: 8mm 0 5mm; color: #fff; letter-spacing: -.03em; }',
  '  .cover p { color: #94a3b8; font-size: 12pt; margin: 0 0 3mm; }',
  '  .cover .meta { margin-top: 18mm; color: #64748b; font-size: 9pt; }',
  '  .cover .line { width: 28mm; height: 2mm; background: #2563eb; border-radius: 1mm; margin: 6mm 0; }',
  '  h1, h2, h3, h4 { color: #0f172a; page-break-after: avoid; }',
  '  h2 { font-size: 18pt; margin: 0 0 4mm; padding-bottom: 2mm; border-bottom: 1px solid #e2e8f0; page-break-before: always; }',
  '  h3 { font-size: 13pt; margin: 5mm 0 2mm; }',
  '  h4 { font-size: 11.5pt; margin: 4mm 0 1.5mm; }',
  '  p { margin: 1.6mm 0; }',
  '  blockquote { margin: 3mm 0; padding: 2.5mm 4mm; background: #f8fafc; border-left: 2mm solid #2563eb; color: #475569; }',
  '  table { width: 100%; border-collapse: collapse; margin: 3mm 0 5mm; font-size: 8.8pt; page-break-inside: auto; }',
  '  th, td { border: 1px solid #dbe3ef; padding: 1.8mm 2mm; vertical-align: top; }',
  '  th { background: #f1f5f9; text-align: left; }',
  '  tr { page-break-inside: avoid; }',
  '  img { max-width: 100%; max-height: 190mm; display: block; margin: 3mm auto; page-break-inside: avoid; }',
  '  pre { background: #0b1220; color: #e2e8f0; padding: 3mm 4mm; border-radius: 2mm; font-size: 8.5pt; line-height: 1.5; white-space: pre-wrap; page-break-inside: avoid; }',
  '  code { background: #f1f5f9; padding: .5mm 1.2mm; border-radius: 1mm; font-size: 9pt; }',
  '  pre code { background: transparent; padding: 0; color: inherit; }',
  '  ul, ol { padding-left: 6mm; margin: 1.5mm 0; }',
  '  li { margin: 1mm 0; }',
  '  hr { border: none; border-top: 1px solid #e2e8f0; margin: 5mm 0; }',
  '  strong { color: #0f172a; }',
  '  a { color: #2563eb; text-decoration: none; }',
  '  .content > h2:first-of-type { page-break-before: avoid; }',
  '</style>',
  '</head>',
  '<body>',
  '<section class="cover">',
  '  <div class="brand">CAD AGENT PLATFORM</div>',
  '  <div class="line"></div>',
  '  <h1>面试介绍与问答</h1>',
  '  <p>技术方案 · 架构图 · 模型调用 · 效果 · 成本 · 工期</p>',
  '  <div class="meta">版本 v0.23.0 · 2026-10 · 内部面试资料</div>',
  '</section>',
  '<main class="content">',
  body,
  '</main>',
  '</body>',
  '</html>',
]

const html = lines.join('\n')
await writeFile(tmpPath, html, 'utf-8')

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage()
await page.goto('file://' + tmpPath, { waitUntil: 'load' })
await page.waitForFunction(() => Array.from(document.images).every((img) => img.complete), null, { timeout: 30000 })
await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  displayHeaderFooter: true,
  headerTemplate: '<div style="font-size:8px;color:#94a3b8;width:100%;padding:0 14mm;">CAD Agent Platform · 面试介绍与问答</div>',
  footerTemplate: '<div style="font-size:8px;color:#94a3b8;width:100%;padding:0 14mm;text-align:right;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
})
await browser.close()
await rm(tmpPath)
console.log('pdf saved', pdfPath)
