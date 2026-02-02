// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Getting Started',
      link: {
        type: 'generated-index',
        title: 'Getting Started',
        description: 'Learn how to get started with ATLAS PUGUH.',
      },
      items: [
        'getting-started/quick-start',
        'getting-started/first-tenant',
        'getting-started/first-project',
        'getting-started/first-rule',
      ],
    },
    {
      type: 'category',
      label: 'User Guides',
      link: {
        type: 'generated-index',
        title: 'User Guides',
        description: 'Detailed guides for using ATLAS PUGUH features.',
      },
      items: [
        {
          type: 'category',
          label: 'IAM',
          items: [
            'user-guides/iam/users',
            'user-guides/iam/roles',
            'user-guides/iam/permissions',
            'user-guides/iam/access-control',
          ],
        },
        {
          type: 'category',
          label: 'Decisions',
          items: [
            'user-guides/decisions/rules',
            'user-guides/decisions/rule-builder',
            'user-guides/decisions/testing',
            'user-guides/decisions/versioning',
          ],
        },
        {
          type: 'category',
          label: 'Workflows',
          items: [
            'user-guides/workflows/creating',
            'user-guides/workflows/triggers',
            'user-guides/workflows/monitoring',
          ],
        },
        {
          type: 'category',
          label: 'Control',
          items: [
            'user-guides/control/environments',
            'user-guides/control/deployment',
            'user-guides/control/rollback',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      link: {
        type: 'generated-index',
        title: 'API Reference',
        description: 'Complete API documentation for ATLAS PUGUH.',
      },
      items: [
        'api-reference/authentication',
        'api-reference/rules-api',
        'api-reference/decisions-api',
        'api-reference/sdk-usage',
      ],
    },
    {
      type: 'category',
      label: 'Advanced',
      link: {
        type: 'generated-index',
        title: 'Advanced Topics',
        description: 'Advanced configuration and best practices.',
      },
      items: [
        'advanced/multi-tenant',
        'advanced/scoping',
        'advanced/best-practices',
        'advanced/troubleshooting',
      ],
    },
  ],
};

module.exports = sidebars;
