import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Windows Folder Remark Tool',
  description: 'A lightweight CLI tool to add remarks/comments to Windows folders via Desktop.ini',
  base: '/windows-folder-remark/',
  lang: 'en-US',

  locales: {
    root: {
      label: 'English',
      lang: 'en-US'
    },
    zh: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/'
    }
  },

  themeConfig: {
    nav: () => [
      { text: 'Guide', link: '/en/guide/' },
      { text: '中文', link: '/zh/' }
    ],

    sidebar: {
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
      ],
      '/zh/': [
        {
          text: '指南',
          items: [
            { text: '介绍', link: '/zh/' },
            { text: '快速开始', link: '/zh/guide/getting-started' },
            { text: '使用方法', link: '/zh/guide/usage' },
            { text: 'API 参考', link: '/zh/guide/api' }
          ]
        }
      ]
    }
  }
})
