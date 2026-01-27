// @ts-check
// Docusaurus Configuration for ATLAS PUGUH Documentation

const lightCodeTheme = require('prism-react-renderer/themes/github');
const darkCodeTheme = require('prism-react-renderer/themes/dracula');

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'ATLAS PUGUH Documentation',
  tagline: 'Constitutional Law System for AI Decisions',
  favicon: 'img/favicon.ico',

  // Production URL
  url: 'https://docs.puguh.atlashub.com',
  baseUrl: '/',

  // GitHub pages deployment config (optional)
  organizationName: 'atlashub',
  projectName: 'puguh-docs',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Internationalization
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/atlashub/puguh/tree/main/docs-site/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: {
          showReadingTime: true,
          blogTitle: 'Changelog',
          blogDescription: 'Latest updates and releases for ATLAS PUGUH',
          postsPerPage: 10,
          editUrl: 'https://github.com/atlashub/puguh/tree/main/docs-site/',
        },
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Social card
      image: 'img/puguh-social-card.png',

      navbar: {
        title: 'PUGUH Docs',
        logo: {
          alt: 'ATLAS PUGUH Logo',
          src: 'img/logo.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'tutorialSidebar',
            position: 'left',
            label: 'Documentation',
          },
          { to: '/blog', label: 'Changelog', position: 'left' },
          {
            href: 'https://admin-puguh.atlashub.com',
            label: 'Go to App',
            position: 'right',
          },
          {
            href: 'https://github.com/atlashub/puguh',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },

      footer: {
        style: 'dark',
        links: [
          {
            title: 'Docs',
            items: [
              {
                label: 'Getting Started',
                to: '/docs/getting-started/quick-start',
              },
              {
                label: 'User Guides',
                to: '/docs/user-guides/iam/users',
              },
              {
                label: 'API Reference',
                to: '/docs/api-reference/authentication',
              },
            ],
          },
          {
            title: 'Product',
            items: [
              {
                label: 'Dashboard',
                href: 'https://admin-puguh.atlashub.com',
              },
              {
                label: 'Pricing',
                href: 'https://admin-puguh.atlashub.com/pricing',
              },
              {
                label: 'Status',
                href: 'https://status.atlashub.com',
              },
            ],
          },
          {
            title: 'Company',
            items: [
              {
                label: 'About',
                href: 'https://atlashub.com/about',
              },
              {
                label: 'Blog',
                to: '/blog',
              },
              {
                label: 'Contact',
                href: 'https://atlashub.com/contact',
              },
            ],
          },
        ],
        copyright: `Copyright ${new Date().getFullYear()} ATLAS PUGUH. Built with Docusaurus.`,
      },

      prism: {
        theme: lightCodeTheme,
        darkTheme: darkCodeTheme,
        additionalLanguages: ['bash', 'json', 'python', 'typescript'],
      },

      // Color mode
      colorMode: {
        defaultMode: 'light',
        disableSwitch: false,
        respectPrefersColorScheme: true,
      },

      // Announcement bar (optional)
      announcementBar: {
        id: 'support_us',
        content:
          'New to PUGUH? Check out our <a target="_blank" rel="noopener noreferrer" href="/docs/getting-started/quick-start">Quick Start Guide</a>!',
        backgroundColor: '#f59e0b',
        textColor: '#1f2937',
        isCloseable: true,
      },
    }),
};

module.exports = config;
