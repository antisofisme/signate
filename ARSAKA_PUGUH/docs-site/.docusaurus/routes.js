import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/blog',
    component: ComponentCreator('/blog', '630'),
    exact: true
  },
  {
    path: '/blog/archive',
    component: ComponentCreator('/blog/archive', '388'),
    exact: true
  },
  {
    path: '/blog/initial-release',
    component: ComponentCreator('/blog/initial-release', 'e59'),
    exact: true
  },
  {
    path: '/blog/tags',
    component: ComponentCreator('/blog/tags', 'a06'),
    exact: true
  },
  {
    path: '/blog/tags/documentation',
    component: ComponentCreator('/blog/tags/documentation', '5a2'),
    exact: true
  },
  {
    path: '/blog/tags/release',
    component: ComponentCreator('/blog/tags/release', 'd9a'),
    exact: true
  },
  {
    path: '/docs',
    component: ComponentCreator('/docs', 'f69'),
    routes: [
      {
        path: '/docs/',
        component: ComponentCreator('/docs/', '2bf'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/advanced/best-practices',
        component: ComponentCreator('/docs/advanced/best-practices', '867'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/advanced/multi-tenant',
        component: ComponentCreator('/docs/advanced/multi-tenant', 'ad8'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/advanced/scoping',
        component: ComponentCreator('/docs/advanced/scoping', 'a71'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/advanced/troubleshooting',
        component: ComponentCreator('/docs/advanced/troubleshooting', 'd25'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/api-reference/authentication',
        component: ComponentCreator('/docs/api-reference/authentication', 'bfb'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/api-reference/decisions-api',
        component: ComponentCreator('/docs/api-reference/decisions-api', '631'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/api-reference/rules-api',
        component: ComponentCreator('/docs/api-reference/rules-api', '5c8'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/api-reference/sdk-usage',
        component: ComponentCreator('/docs/api-reference/sdk-usage', 'b56'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/category/advanced',
        component: ComponentCreator('/docs/category/advanced', '345'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/category/api-reference',
        component: ComponentCreator('/docs/category/api-reference', '6be'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/category/getting-started',
        component: ComponentCreator('/docs/category/getting-started', '01f'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/category/user-guides',
        component: ComponentCreator('/docs/category/user-guides', '0cf'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/getting-started/first-project',
        component: ComponentCreator('/docs/getting-started/first-project', 'b2f'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/getting-started/first-rule',
        component: ComponentCreator('/docs/getting-started/first-rule', '5fd'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/getting-started/first-tenant',
        component: ComponentCreator('/docs/getting-started/first-tenant', 'd17'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/getting-started/quick-start',
        component: ComponentCreator('/docs/getting-started/quick-start', 'c34'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/control/deployment',
        component: ComponentCreator('/docs/user-guides/control/deployment', '270'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/control/environments',
        component: ComponentCreator('/docs/user-guides/control/environments', 'b8b'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/control/rollback',
        component: ComponentCreator('/docs/user-guides/control/rollback', '6a2'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/decisions/rule-builder',
        component: ComponentCreator('/docs/user-guides/decisions/rule-builder', 'd2a'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/decisions/rules',
        component: ComponentCreator('/docs/user-guides/decisions/rules', '651'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/decisions/testing',
        component: ComponentCreator('/docs/user-guides/decisions/testing', '12b'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/decisions/versioning',
        component: ComponentCreator('/docs/user-guides/decisions/versioning', 'c8d'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/iam/access-control',
        component: ComponentCreator('/docs/user-guides/iam/access-control', 'af9'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/iam/permissions',
        component: ComponentCreator('/docs/user-guides/iam/permissions', '5e7'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/iam/roles',
        component: ComponentCreator('/docs/user-guides/iam/roles', 'ca0'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/iam/users',
        component: ComponentCreator('/docs/user-guides/iam/users', '71d'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/workflows/creating',
        component: ComponentCreator('/docs/user-guides/workflows/creating', '58d'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/workflows/monitoring',
        component: ComponentCreator('/docs/user-guides/workflows/monitoring', '81e'),
        exact: true,
        sidebar: "tutorialSidebar"
      },
      {
        path: '/docs/user-guides/workflows/triggers',
        component: ComponentCreator('/docs/user-guides/workflows/triggers', '01d'),
        exact: true,
        sidebar: "tutorialSidebar"
      }
    ]
  },
  {
    path: '/',
    component: ComponentCreator('/', '82c'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
