import type { Directive } from 'vue'

// 动画类型
type AnimateType = 
  | 'fade' 
  | 'fade-up' 
  | 'fade-down' 
  | 'fade-left' 
  | 'fade-right'
  | 'scale' 
  | 'slide-up' 
  | 'slide-down' 
  | 'slide-left' 
  | 'slide-right'
  | 'rotate'
  | 'bounce'

interface AnimateOptions {
  type?: AnimateType
  duration?: number
  delay?: number
  easing?: string
  once?: boolean
}

// 默认配置
const defaults: AnimateOptions = {
  type: 'fade-up',
  duration: 600,
  delay: 0,
  easing: 'ease-out',
  once: true
}

// 动画样式映射
const animations: Record<AnimateType, { from: string; to: string }> = {
  'fade': {
    from: 'opacity: 0',
    to: 'opacity: 1'
  },
  'fade-up': {
    from: 'opacity: 0; transform: translateY(30px)',
    to: 'opacity: 1; transform: translateY(0)'
  },
  'fade-down': {
    from: 'opacity: 0; transform: translateY(-30px)',
    to: 'opacity: 1; transform: translateY(0)'
  },
  'fade-left': {
    from: 'opacity: 0; transform: translateX(30px)',
    to: 'opacity: 1; transform: translateX(0)'
  },
  'fade-right': {
    from: 'opacity: 0; transform: translateX(-30px)',
    to: 'opacity: 1; transform: translateX(0)'
  },
  'scale': {
    from: 'opacity: 0; transform: scale(0.9)',
    to: 'opacity: 1; transform: scale(1)'
  },
  'slide-up': {
    from: 'transform: translateY(100%)',
    to: 'transform: translateY(0)'
  },
  'slide-down': {
    from: 'transform: translateY(-100%)',
    to: 'transform: translateY(0)'
  },
  'slide-left': {
    from: 'transform: translateX(100%)',
    to: 'transform: translateX(0)'
  },
  'slide-right': {
    from: 'transform: translateX(-100%)',
    to: 'transform: translateX(0)'
  },
  'rotate': {
    from: 'opacity: 0; transform: rotate(-180deg) scale(0.5)',
    to: 'opacity: 1; transform: rotate(0) scale(1)'
  },
  'bounce': {
    from: 'opacity: 0; transform: scale(0.3)',
    to: 'opacity: 1; transform: scale(1)'
  }
}

// 解析参数
function parseOptions(value: AnimateType | AnimateOptions): AnimateOptions {
  if (typeof value === 'string') {
    return { ...defaults, type: value }
  }
  return { ...defaults, ...value }
}

// Intersection Observer 实例
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target as HTMLElement
        const options = (el as any).__animateOptions as AnimateOptions
        
        if (options) {
          const anim = animations[options.type || 'fade-up']
          
          // 设置初始状态
          el.style.cssText = `
            ${anim.from};
            transition: all ${options.duration}ms ${options.easing} ${options.delay}ms;
          `
          
          // 触发动画
          requestAnimationFrame(() => {
            el.style.cssText = anim.to
          })
          
          // 如果只执行一次，取消观察
          if (options.once) {
            observer.unobserve(el)
          }
        }
      }
    })
  },
  {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }
)

// v-animate 指令
export const vAnimate: Directive = {
  mounted(el: HTMLElement, binding) {
    const options = parseOptions(binding.value)
    const anim = animations[options.type || 'fade-up']
    
    // 保存配置
    ;(el as any).__animateOptions = options
    
    // 设置初始状态（隐藏）
    el.style.cssText = anim.from
    
    // 开始观察
    observer.observe(el)
  },
  
  unmounted(el: HTMLElement) {
    observer.unobserve(el)
  }
}

// v-animate-group 指令（交错动画）
export const vAnimateGroup: Directive = {
  mounted(el: HTMLElement, binding) {
    const children = el.children
    const options = parseOptions(binding.value)
    
    Array.from(children).forEach((child, index) => {
      const childEl = child as HTMLElement
      const anim = animations[options.type || 'fade-up']
      const delay = (options.delay || 0) + index * 100
      
      childEl.style.cssText = `
        ${anim.from};
        transition: all ${options.duration}ms ${options.easing} ${delay}ms;
      `
      
      const childObserver = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              requestAnimationFrame(() => {
                childEl.style.cssText = anim.to
              })
              childObserver.unobserve(childEl)
            }
          })
        },
        { threshold: 0.1 }
      )
      
      childObserver.observe(childEl)
    })
  }
}

// 导出所有指令
export default {
  install(app: any) {
    app.directive('animate', vAnimate)
    app.directive('animate-group', vAnimateGroup)
  }
}
