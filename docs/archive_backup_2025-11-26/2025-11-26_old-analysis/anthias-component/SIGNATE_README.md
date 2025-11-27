# Signate Core Platform

Forked from Anthias open-source digital signage platform.

## 🎯 About

This is the core platform for Signate, an advanced digital signage solution. Built on the solid foundation of Anthias with enhancements for:

- Multi-tenant architecture
- Cloud management capabilities  
- Advanced scheduling and analytics
- Enterprise-grade features

## 📋 Current Status

🔄 **Fork in Progress**

- [x] Core files copied from Anthias
- [ ] Rebranding (Anthias → Signate)
- [ ] Module renaming
- [ ] Configuration updates
- [ ] Feature extensions

## 🛠️ Technology Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: React 19 + TypeScript + Redux Toolkit
- **Database**: PostgreSQL / SQLite
- **Cache**: Redis + Celery
- **Infrastructure**: Docker + nginx

## 🚀 Development

```bash
# Install dependencies
pip install -r requirements/requirements.txt
npm install

# Run development server
python manage.py runserver
npm run dev
```

## 📁 Structure

```
signate-core/
├── anthias_app/        # Main Django app (to be renamed)
├── anthias_django/     # Django config (to be renamed)
├── api/                # REST API endpoints
├── static/src/         # React frontend source
├── templates/          # Django templates
├── docker/             # Container configuration
├── lib/                # Python utilities
└── requirements/       # Dependencies
```

## 🔧 Next Steps

1. Rebrand Anthias → Signate
2. Rename modules and update imports
3. Extend models for multi-tenancy
4. Add cloud management features
5. Implement analytics system

## ⚖️ License

Based on Anthias (AGPL-3.0). See original license terms in LICENSE file.

---

*Building the future of digital signage with Signate.*