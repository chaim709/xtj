import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "公考知识库",
  description: "行测申论备考指南 - 精准定位，高效备考",
  lang: 'zh-CN',
  
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'theme-color', content: '#3eaf7c' }],
    ['meta', { name: 'keywords', content: '公考,行测,申论,公务员考试,备考指南' }],
  ],

  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    logo: '/logo.svg',
    siteTitle: '公考知识库',
    
    nav: [
      { text: '🏠 首页', link: '/' },
      { 
        text: '🧩 题库',
        items: [
          { text: '📝 专项练习', link: '/tiku/practice' },
          { text: '📕 错题本', link: '/tiku/mistakes' },
          { text: '📊 统计分析', link: '/tiku/stats' },
        ]
      },
      { 
        text: '📚 行测',
        items: [
          { text: '📊 资料分析', link: '/xingce/ziliao/' },
          { text: '📖 言语理解', link: '/xingce/yanyu/' },
          { text: '📏 数量关系', link: '/xingce/shuliang/' },
          { text: '🎨 判断推理', link: '/xingce/panduan/' },
        ]
      },
      { text: '📜 申论', link: '/shenlun/' },
      { text: '🅰 常识', link: '/changshi/' },
      { text: '📋 公基', link: '/gongji/' },
      { text: '🔧 工具', link: '/utils/' },
    ],

    sidebar: {
      '/xingce/ziliao/': [
        {
          text: '📊 资料分析',
          items: [
            { text: '概述', link: '/xingce/ziliao/' },
            { text: '增长率计算', link: '/xingce/ziliao/zengzhang' },
            { text: '比重计算', link: '/xingce/ziliao/bizhong' },
            { text: '平均数计算', link: '/xingce/ziliao/pingjun' },
            { text: '倍数计算', link: '/xingce/ziliao/beishu' },
            { text: '速算技巧', link: '/xingce/ziliao/susuan' },
          ]
        }
      ],
      '/xingce/yanyu/': [
        {
          text: '📖 言语理解',
          items: [
            { text: '概述', link: '/xingce/yanyu/' },
            { text: '片段阅读', link: '/xingce/yanyu/pianduan' },
            { text: '逻辑填空', link: '/xingce/yanyu/tiankong' },
            { text: '语句表达', link: '/xingce/yanyu/yuju' },
          ]
        }
      ],
      '/xingce/shuliang/': [
        {
          text: '📏 数量关系',
          items: [
            { text: '概述', link: '/xingce/shuliang/' },
            { text: '数字推理', link: '/xingce/shuliang/shuzi' },
            { text: '数学运算', link: '/xingce/shuliang/yunsuan' },
          ]
        }
      ],
      '/xingce/panduan/': [
        {
          text: '🎨 判断推理',
          items: [
            { text: '概述', link: '/xingce/panduan/' },
            { text: '图形推理', link: '/xingce/panduan/tuxing' },
            { text: '定义判断', link: '/xingce/panduan/dingyi' },
            { text: '类比推理', link: '/xingce/panduan/leibi' },
            { text: '逻辑判断', link: '/xingce/panduan/luoji' },
          ]
        }
      ],
      '/shenlun/': [
        {
          text: '📜 申论',
          items: [
            { text: '概述', link: '/shenlun/' },
            { text: '概括归纳', link: '/shenlun/gaigui' },
            { text: '综合分析', link: '/shenlun/fenxi' },
            { text: '提出对策', link: '/shenlun/duice' },
            { text: '公文写作', link: '/shenlun/gongwen' },
            { text: '大作文', link: '/shenlun/zuowen' },
          ]
        }
      ],
      '/changshi/': [
        {
          text: '🧠 常识判断',
          items: [
            { text: '常识判断概述', link: '/changshi/' },
          ]
        }
      ],
      '/gongji/': [
        {
          text: '📋 公共基础知识',
          items: [
            { text: '公基概述', link: '/gongji/' },
          ]
        }
      ],
      '/utils/': [
        {
          text: '🔧 备考工具',
          items: [
            { text: '工具与资源', link: '/utils/' },
          ]
        }
      ],
      '/tiku/': [
        {
          text: '🧩 题库功能',
          items: [
            { text: '题库首页', link: '/tiku/' },
            { text: '专项练习', link: '/tiku/practice' },
            { text: '错题本', link: '/tiku/mistakes' },
            { text: '统计分析', link: '/tiku/stats' },
          ]
        }
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com' }
    ],

    footer: {
      message: '与刷题系统数据同步',
      copyright: 'Copyright © 2024-2026 公考知识库'
    },

    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换'
            }
          }
        }
      }
    },

    outline: {
      label: '页面导航',
      level: [2, 3]
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    lastUpdated: {
      text: '最后更新于',
      formatOptions: {
        dateStyle: 'short',
        timeStyle: 'short'
      }
    },

    returnToTopLabel: '回到顶部',
    sidebarMenuLabel: '菜单',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
  }
})
