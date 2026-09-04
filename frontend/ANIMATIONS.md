# 前端动画系统使用指南

## 🎨 动画指令

### v-animate

在元素上添加滚动触发动画。

#### 基本用法

```vue
<template>
  <!-- 简单用法：元素进入视口时淡入上移 -->
  <div v-animate>内容</div>
  
  <!-- 指定动画类型 -->
  <div v-animate="'fade-left'">从左滑入</div>
  
  <!-- 配置选项 -->
  <div v-animate="{ type: 'scale', duration: 800, delay: 200 }">
    缩放动画，持续800ms，延迟200ms
  </div>
</template>
```

#### 可用动画类型

| 类型 | 效果 |
|------|------|
| `fade` | 淡入 |
| `fade-up` | 淡入上移（默认） |
| `fade-down` | 淡入下移 |
| `fade-left` | 从右滑入 |
| `fade-right` | 从左滑入 |
| `scale` | 缩放进入 |
| `slide-up` | 从下滑入 |
| `slide-down` | 从上滑入 |
| `slide-left` | 从右滑入 |
| `slide-right` | 从左滑入 |
| `rotate` | 旋转进入 |
| `bounce` | 弹跳进入 |

#### 配置选项

```typescript
interface AnimateOptions {
  type?: AnimateType      // 动画类型
  duration?: number       // 持续时间（毫秒），默认 600
  delay?: number          // 延迟时间（毫秒），默认 0
  easing?: string         // 缓动函数，默认 'ease-out'
  once?: boolean          // 是否只执行一次，默认 true
}
```

### v-animate-group

子元素交错动画。

```vue
<template>
  <!-- 列表项依次出现 -->
  <ul v-animate-group="'fade-up'">
    <li v-for="item in items" :key="item.id">
      {{ item.name }}
    </li>
  </ul>
</template>
```

---

## 🎭 过渡组件

### AnimateGroup

包裹 `<transition-group>` 的组件。

```vue
<template>
  <AnimateGroup name="fade-up" tag="div">
    <div v-for="item in items" :key="item.id">
      {{ item.name }}
    </div>
  </AnimateGroup>
</template>

<script setup>
import AnimateGroup from '@/components/AnimateGroup.vue'
</script>
```

#### 可用过渡名称

- `fade-up` - 淡入上移
- `fade-scale` - 淡入缩放
- `slide-left` - 左滑
- `slide-right` - 右滑
- `bounce` - 弹跳
- `flip` - 翻转

---

## 🎬 路由过渡

在 `router/index.ts` 中为路由设置过渡动画：

```typescript
const routes = [
  {
    path: '/chat',
    component: Chat,
    meta: {
      transition: 'slide-left'  // 页面切换动画
    }
  }
]
```

可用的路由过渡：
- `fade` - 淡入淡出
- `slide-left` - 左滑
- `slide-right` - 右滑
- `slide-up` - 上滑
- `scale` - 缩放

---

## 💫 CSS 工具类

### 悬浮效果

```html
<!-- 悬浮时上移并显示阴影 -->
<div class="hover-lift">卡片内容</div>

<!-- 悬浮时缩放 -->
<div class="hover-scale">按钮内容</div>
```

### 渐变文字

```html
<h1 class="text-gradient">渐变标题</h1>
```

### 骨架屏

```html
<div class="skeleton" style="width: 200px; height: 20px;"></div>
```

---

## 🎯 使用示例

### 列表项交错动画

```vue
<template>
  <div class="list">
    <div 
      v-for="(item, index) in items" 
      :key="item.id"
      v-animate="{ delay: index * 100 }"
      class="list-item"
    >
      {{ item.name }}
    </div>
  </div>
</template>
```

### 卡片入场动画

```vue
<template>
  <div class="cards">
    <div 
      v-for="card in cards" 
      :key="card.id"
      v-animate="{ type: 'scale', duration: 500 }"
      class="card hover-lift"
    >
      <h3>{{ card.title }}</h3>
      <p>{{ card.content }}</p>
    </div>
  </div>
</template>
```

### 打字机效果

```vue
<template>
  <div class="typing-effect">
    <span 
      v-for="(char, index) in text" 
      :key="index"
      class="char"
      :style="{ animationDelay: `${index * 50}ms` }"
    >
      {{ char }}
    </span>
  </div>
</template>

<style scoped>
.char {
  opacity: 0;
  animation: fadeIn 0.3s ease forwards;
}

@keyframes fadeIn {
  to { opacity: 1; }
}
</style>
```

---

## ⚡ 性能提示

1. **使用 `v-if` 控制动画触发**
   ```vue
   <div v-if="show" v-animate>内容</div>
   ```

2. **避免在大量元素上使用复杂动画**
   - 列表超过 50 项时考虑虚拟滚动
   - 使用 `will-change` 提示浏览器优化

3. **使用 `transform` 和 `opacity`**
   - 这两个属性不会触发重排
   - 性能最好

4. **合理使用 `once: true`**
   - 避免重复触发动画
   - 节省性能

---

## 🔧 自定义动画

在 `src/styles/index.css` 中添加自定义动画：

```css
/* 自定义弹跳动画 */
@keyframes custom-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}

.custom-bounce {
  animation: custom-bounce 1s ease infinite;
}
```

然后在指令中使用：

```vue
<div v-animate="{ type: 'custom' }">自定义动画</div>
```
