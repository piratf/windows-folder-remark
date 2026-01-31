import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Windows 文件夹备注工具',
  description: '一个轻量级的命令行工具，通过 Desktop.ini 为 Windows 文件夹添加备注/评论。无系统驻留，无数据上传，安全放心，用完即走。',
  base: '/windows-folder-remark/',
  lang: 'zh-CN',

  locales: {
    root: {
      label: '简体中文',
      lang: 'zh-CN'
    },
    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/'
    }
  },

  head: [
    ['link', { rel: 'alternate', hreflang: 'zh-CN', href: 'https://piratf.github.io/windows-folder-remark/' }],
    ['link', { rel: 'alternate', hreflang: 'en-US', href: 'https://piratf.github.io/windows-folder-remark/en/' }],
    ['link', { rel: 'alternate', hreflang: 'x-default', href: 'https://piratf.github.io/windows-folder-remark/en/' }]
  ],

  sitemap: {
    hostname: 'https://piratf.github.io',
    transformItems(items) {
      return items.map((item) => {
        return {
          url: '/windows-folder-remark' + (item.url.startsWith('/') ? '' : '/') + item.url,
          changefreq: 'weekly',
        }
      })
    }
  },

  themeConfig: {
    nav: () => [
      { text: '指南', link: '/guide/' },
      { text: 'English', link: '/en/' }
    ],

    sidebar: {
      '/': [
        {
          text: '指南',
          items: [
            { text: '介绍', link: '/' },
            { text: '快速开始', link: '/guide/getting-started' },
            { text: '使用方法', link: '/guide/usage' },
            { text: 'API 参考', link: '/guide/api' }
          ]
        }
      ],
      '/en/': [
        {
          text: 'Guide',
          items: [
            { text: 'Introduction', link: '/en/' },
            { text: 'Getting Started', link: '/en/guide/getting-started' },
            { text: 'Usage', link: '/en/guide/usage' },
            { text: 'API Reference', link: '/en/guide/api' }
          ]
        }
      ]
    }
  }
})
