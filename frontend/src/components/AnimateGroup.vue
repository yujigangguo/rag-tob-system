<template>
  <div class="animate-group">
    <transition-group :name="name" :tag="tag" :appear="appear">
      <slot />
    </transition-group>
  </div>
</template>

<script setup lang="ts">
interface Props {
  name?: string
  tag?: string
  appear?: boolean
}

withDefaults(defineProps<Props>(), {
  name: 'fade-up',
  tag: 'div',
  appear: true
})
</script>

<style scoped>
/* 淡入上移 */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 0.4s ease;
}

.fade-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

.fade-up-move {
  transition: transform 0.4s ease;
}

/* 淡入缩放 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.4s ease;
}

.fade-scale-enter-from {
  opacity: 0;
  transform: scale(0.9);
}

.fade-scale-leave-to {
  opacity: 0;
  transform: scale(1.1);
}

.fade-scale-move {
  transition: transform 0.4s ease;
}

/* 滑入左 */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.4s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

.slide-left-move {
  transition: transform 0.4s ease;
}

/* 滑入右 */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.4s ease;
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-move {
  transition: transform 0.4s ease;
}

/* 弹跳 */
.bounce-enter-active {
  animation: bounce-in 0.5s;
}

.bounce-leave-active {
  animation: bounce-in 0.5s reverse;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

/* 翻转 */
.flip-enter-active,
.flip-leave-active {
  transition: all 0.6s ease;
}

.flip-enter-from {
  opacity: 0;
  transform: rotateY(90deg);
}

.flip-leave-to {
  opacity: 0;
  transform: rotateY(-90deg);
}

.flip-move {
  transition: transform 0.6s ease;
}
</style>
