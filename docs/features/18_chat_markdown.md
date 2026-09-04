# 优化 #18：对话页面优化（Markdown 渲染）

## 改动文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/package.json` | 修改 | 添加 markdown-it 依赖 |
| `frontend/src/views/Chat.vue` | 修改 | Markdown 渲染、代码高亮 |

## 实现方案

### 1. 安装依赖
```bash
cd frontend
npm install markdown-it highlight.js
```

### 2. 创建 Markdown 组件
```vue
<!-- frontend/src/components/MarkdownRenderer.vue -->
<template>
  <div class="markdown-body" v-html="renderedContent"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const props = defineProps({
  content: String
})

const md = new MarkdownIt({
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(str, { language: lang }).value
    }
    return ''
  }
})

const renderedContent = computed(() => md.render(props.content || ''))
</script>
```

### 3. 在 Chat.vue 中使用
```vue
<template>
  <div class="message">
    <MarkdownRenderer :content="message.content" />
    <el-button @click="copyMessage(message.content)">复制</el-button>
  </div>
</template>
```

## 功能特性

1. **Markdown 渲染**：标题、列表、表格、引用等
2. **代码高亮**：支持多种编程语言
3. **复制按钮**：一键复制消息内容
4. **引用链接**：[1] 可点击跳转到源文档

## 样式优化

```css
.markdown-body {
  line-height: 1.6;
}
.markdown-body pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body code {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}
```
