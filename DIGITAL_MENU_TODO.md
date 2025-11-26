# Digital Menu Feature - Remaining Tasks

**Created**: 2025-11-26
**Status**: Backend Complete ✅ | Frontend & Testing Pending ⏳

---

## 📊 Overview

Digital Menu feature untuk hotel services (Restaurant, Laundry, Spa, etc.) dengan:
- Multi-organization support
- Excel import/export
- Public URL viewer dengan QR code
- Auto-generated QR codes
- Analytics tracking
- Responsive lazy loading

---

## ✅ Completed Tasks

### 1. Backend Implementation (100%)
- ✅ Database migration `049_create_menu_tables.sql` (5 tables)
- ✅ SQLAlchemy models (MenuModel, MenuItemModel, etc.)
- ✅ Repositories dengan organization filtering
- ✅ Infrastructure (QRCodeGenerator, ExcelImporter/Exporter)
- ✅ Use cases (CreateMenu, BulkImport, GetPublicMenu)
- ✅ Admin API routes (authenticated)
- ✅ Public API routes (no auth)
- ✅ Routes registered in `main.py`
- ✅ QR codes static file mounting

**Files Created**:
```
backend-python/
├── migrations/049_create_menu_tables.sql
└── services/menu/
    ├── __init__.py
    ├── dtos.py (18 DTOs)
    ├── routes.py (admin endpoints)
    ├── public_routes.py (public viewer endpoints)
    ├── repositories/
    │   ├── __init__.py
    │   ├── models.py (5 models)
    │   ├── menu_repo.py
    │   └── menu_analytics_repo.py
    ├── infrastructure/
    │   ├── __init__.py
    │   ├── qr_code_generator.py
    │   └── excel_importer.py
    └── use_cases/
        ├── __init__.py
        ├── create_menu.py
        ├── bulk_import_items.py
        └── get_public_menu.py
```

---

## ⏳ Pending Tasks

### TASK 1: Deploy & Test Backend API

**Priority**: HIGH (Must do first!)

#### 1.1 Run Database Migration

```bash
# Backup database first
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db" \
  > backups/pre_migration_049_$(date +%Y%m%d_%H%M%S).sql

# Upload migration file
sshpass -p 'Password@2021' scp \
  backend-python/migrations/049_create_menu_tables.sql \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/migrations/

# Run migration
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /home/gzjbbk/signate/backend-python/migrations/049_create_menu_tables.sql"

# Verify tables created
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db -c '\dt menu*'"
```

#### 1.2 Sync Backend Code to Server

```bash
# Sync menu service folder
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  backend-python/services/menu/ \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/menu/

# Sync updated main.py
sshpass -p 'Password@2021' scp \
  backend-python/main.py \
  gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/
```

#### 1.3 Install Python Dependencies

```bash
# Add to requirements.txt if not exist:
# - qrcode==7.4.2
# - pillow==10.1.0
# - pandas==2.1.3
# - openpyxl==3.1.2

# Install on server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml exec backend-api pip install qrcode pillow pandas openpyxl"
```

#### 1.4 Restart Backend

```bash
# Restart backend service
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml restart backend-api"

# Check logs
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker logs signage-backend-python --tail 50"
```

#### 1.5 Test API Endpoints

```bash
# Test admin endpoints (authenticated)
# 1. Get auth token
curl -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Save token
export TOKEN="<access_token>"

# 2. Create menu
curl -X POST http://192.168.5.12:8001/api/v1/menus \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Restaurant Menu",
    "menu_type": "restaurant",
    "description": "Main restaurant menu",
    "show_prices": true,
    "display_mode": "grid"
  }'

# 3. List menus
curl -X GET http://192.168.5.12:8001/api/v1/menus \
  -H "Authorization: Bearer $TOKEN"

# 4. Download Excel template
curl -X GET http://192.168.5.12:8001/api/v1/menus/excel-template \
  -H "Authorization: Bearer $TOKEN" \
  -o menu_template.xlsx

# 5. Test public endpoint (no auth)
# Get public_url_code from create menu response
curl -X GET http://192.168.5.12:8001/api/v1/public/menu/<PUBLIC_CODE>
```

#### 1.6 Verify QR Code Generation

```bash
# Check QR code directory created
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "ls -la /data/signage/content/qr_codes/"

# Access QR code via URL
# http://192.168.5.12:8001/qr_codes/menu_<ID>_org_<ORG_ID>.png
```

**Expected Results**:
- ✅ All 5 tables created (menus, menu_items, menu_import_history, menu_views, menu_categories)
- ✅ API endpoints respond correctly
- ✅ QR codes generated and accessible
- ✅ Excel template downloads successfully
- ✅ Public endpoint accessible without authentication

---

### TASK 2: Implement Frontend CMS

**Priority**: HIGH

#### 2.1 Create Feature Structure

```bash
mkdir -p cms-vite/src/features/menus/{api,types,hooks,components,pages,utils}
```

#### 2.2 API Client (`cms-vite/src/features/menus/api/menuApi.ts`)

```typescript
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

// Types
export interface Menu {
  id: number;
  name: string;
  menu_type: string;
  description?: string;
  is_active: boolean;
  show_prices: boolean;
  display_mode: string;
  theme_color?: string;
  public_url_code: string;
  public_url?: string;
  qr_code_path?: string;
  qr_code_url?: string;
  items_count: number;
  created_at: string;
}

export interface MenuItem {
  id: number;
  name: string;
  description?: string;
  price?: number;
  currency: string;
  category?: string;
  image_url?: string;
  video_url?: string;
  display_order: number;
  is_active: boolean;
  is_featured: boolean;
}

// API calls
export const menuApi = {
  // Menus
  list: (params?: { skip?: number; limit?: number; menu_type?: string }) =>
    apiClient.get('/api/v1/menus', { params }),

  create: (data: any) =>
    apiClient.post('/api/v1/menus', data),

  get: (id: number) =>
    apiClient.get(`/api/v1/menus/${id}`),

  update: (id: number, data: any) =>
    apiClient.patch(`/api/v1/menus/${id}`, data),

  delete: (id: number) =>
    apiClient.delete(`/api/v1/menus/${id}`),

  // Items
  listItems: (menuId: number, params?: any) =>
    apiClient.get(`/api/v1/menus/${menuId}/items`, { params }),

  addItem: (menuId: number, data: any) =>
    apiClient.post(`/api/v1/menus/${menuId}/items`, data),

  // Import/Export
  importExcel: (menuId: number, file: File, replaceExisting: boolean) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(
      `/api/v1/menus/${menuId}/import?replace_existing=${replaceExisting}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  },

  downloadTemplate: () =>
    apiClient.get('/api/v1/menus/excel-template', { responseType: 'blob' }),
};
```

#### 2.3 React Query Hooks (`cms-vite/src/features/menus/hooks/useMenus.ts`)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { menuApi } from '../api/menuApi';
import { toast } from 'sonner';

export const useMenus = (params?: any) => {
  return useQuery({
    queryKey: ['menus', params],
    queryFn: () => menuApi.list(params),
  });
};

export const useMenu = (id: number) => {
  return useQuery({
    queryKey: ['menu', id],
    queryFn: () => menuApi.get(id),
    enabled: !!id,
  });
};

export const useCreateMenu = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: menuApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menus'] });
      toast.success('Menu created successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to create menu');
    },
  });
};

export const useDeleteMenu = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: menuApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menus'] });
      toast.success('Menu deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.message || 'Failed to delete menu');
    },
  });
};
```

#### 2.4 Main Components to Create

1. **MenuList.tsx** - Table with menus
   - Show: name, type, items count, status, public URL, QR code
   - Actions: Edit, Delete, Manage Items, View QR

2. **MenuForm.tsx** - Create/edit form
   - Fields: name, type, description, display settings, contact buttons
   - Validation with React Hook Form + Zod

3. **MenuItemsManager.tsx** - Manage items for menu
   - List items with drag-and-drop reorder
   - Add/edit/delete items
   - Import from Excel button

4. **ExcelImportModal.tsx** - Excel upload
   - Download template button
   - File upload with validation
   - Show import results (success/errors)

5. **QRCodeDisplay.tsx** - Show/download QR code
   - Display QR code image
   - Download button
   - Copy public URL to clipboard

6. **MenusPage.tsx** - Main page
   - Combine all components
   - Route: `/menus`

#### 2.5 Update Routing & Sidebar

```typescript
// cms-vite/src/routes/index.tsx
import { MenusPage } from '@/features/menus/pages/MenusPage';

// Add route
{
  path: '/menus',
  element: <MenusPage />,
}

// cms-vite/src/shared/components/layout/Sidebar.tsx
// Add menu item
{
  name: 'Digital Menus',
  icon: 'UtensilsCrossed', // or 'Menu'
  href: '/menus',
}
```

**Files to Create**:
```
cms-vite/src/features/menus/
├── api/
│   └── menuApi.ts
├── types/
│   └── menu.ts
├── hooks/
│   ├── useMenus.ts
│   ├── useMenuItems.ts
│   └── useMenuImport.ts
├── components/
│   ├── MenuList.tsx
│   ├── MenuForm.tsx
│   ├── MenuItemsManager.tsx
│   ├── ExcelImportModal.tsx
│   ├── QRCodeDisplay.tsx
│   └── PublicUrlCopy.tsx
├── pages/
│   └── MenusPage.tsx
└── utils/
    └── menuHelpers.ts
```

---

### TASK 3: Create Public Menu Viewer App

**Priority**: MEDIUM

#### 3.1 Create New Vite App

```bash
cd /mnt/g/khoirul/signate
npm create vite@latest menu-viewer-vite -- --template react-ts
cd menu-viewer-vite
npm install
npm install @tanstack/react-query axios react-intersection-observer
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### 3.2 Structure

```
menu-viewer-vite/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── menuApi.ts (public API calls)
│   ├── components/
│   │   ├── MenuHeader.tsx
│   │   ├── MenuItemGrid.tsx
│   │   ├── MenuItemCard.tsx
│   │   ├── MenuItemModal.tsx
│   │   ├── ContactButtons.tsx
│   │   └── LoadingSpinner.tsx
│   ├── hooks/
│   │   ├── usePublicMenu.ts
│   │   └── useIntersectionObserver.ts
│   └── styles/
│       └── index.css
└── nginx.conf
```

#### 3.3 Key Features to Implement

1. **Infinite Scroll** - IntersectionObserver with React Query infinite query
2. **Lazy Image Loading** - Images load as they enter viewport
3. **Contact Buttons** - WhatsApp/Phone with click tracking
4. **Responsive Layout** - Grid/List/Carousel based on menu settings
5. **Category Filtering** - Filter by category
6. **Search** - Client-side search by name

#### 3.4 Deployment

```bash
# Build
npm run build

# Docker service in docker-compose.yml
menu-viewer:
  container_name: signage-menu-viewer
  image: nginx:alpine
  restart: unless-stopped
  ports:
    - 8081:80
  volumes:
    - ../menu-viewer-vite/dist:/usr/share/nginx/html:ro
    - ../menu-viewer-vite/nginx.conf:/etc/nginx/nginx.conf:ro
  networks:
    - signage-network
```

#### 3.5 Public URL Pattern

```
Player URL: https://player.zhmhotels.online/menu/<PUBLIC_CODE>
or
Menu Viewer URL: https://menu.zhmhotels.online/<PUBLIC_CODE>
```

---

### TASK 4: Integration Testing

**Priority**: HIGH

#### 4.1 Test Scenarios

1. **Admin Flow**:
   - Login to CMS
   - Create menu
   - Verify QR code generated
   - Download Excel template
   - Import items from Excel
   - Verify items imported correctly
   - View public URL
   - Download QR code

2. **Public Viewer Flow**:
   - Scan QR code or visit public URL
   - Verify menu loads
   - Test infinite scroll
   - Test image lazy loading
   - Click contact button
   - Verify analytics tracked

3. **Multi-tenant Isolation**:
   - Create menu in Org A
   - Login as Org B admin
   - Verify cannot see Org A menu
   - Verify public URL still works

#### 4.2 Analytics Verification

```bash
# Check menu views tracked
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db -c 'SELECT * FROM menu_views ORDER BY viewed_at DESC LIMIT 10;'"

# Check import history
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db -c 'SELECT * FROM menu_import_history ORDER BY imported_at DESC LIMIT 5;'"
```

---

## 📝 Important Notes

### Dependencies to Install

**Backend (Python)**:
```txt
qrcode==7.4.2
pillow==10.1.0
pandas==2.1.3
openpyxl==3.1.2
```

**Frontend CMS (already have most)**:
- React Query (installed)
- React Hook Form (installed)
- Zod (installed)
- Sonner (for toasts)

**Menu Viewer**:
- React Query
- Axios
- react-intersection-observer
- Tailwind CSS

### Excel Template Format

| Column | Name | Required | Type |
|--------|------|----------|------|
| A | Name | Yes | Text |
| B | Price | No | Number |
| C | Description | No | Text |
| D | Category | No | Text |
| E | Image URL | No | URL |
| F | Video URL | No | URL |

### Public URL Format

```
Public URL: https://player.zhmhotels.online/menu/<12-char-code>
QR Code URL: https://api.zhmhotels.online/qr_codes/menu_<ID>_org_<ORG_ID>.png
```

### Analytics Tracked

- **menu_views table**:
  - viewer_ip
  - user_agent
  - device_type (mobile/tablet/desktop)
  - contact_clicked (boolean)
  - contact_type (whatsapp/phone)
  - viewed_at

---

## 🚀 Quick Start Commands

### Deploy Backend
```bash
# 1. Backup DB
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec signage-postgres pg_dump -U signage_user -d signage_db > /tmp/backup_$(date +%Y%m%d).sql"

# 2. Upload & run migration
sshpass -p 'Password@2021' scp backend-python/migrations/049_create_menu_tables.sql gzjbbk@192.168.5.12:/tmp/
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "docker exec -i signage-postgres psql -U signage_user -d signage_db < /tmp/049_create_menu_tables.sql"

# 3. Sync code
sshpass -p 'Password@2021' rsync -avz --exclude '__pycache__' \
  backend-python/services/menu/ gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/services/menu/
sshpass -p 'Password@2021' scp backend-python/main.py gzjbbk@192.168.5.12:/home/gzjbbk/signate/backend-python/

# 4. Install deps & restart
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 \
  "cd /home/gzjbbk/signate && docker-compose -f docker/docker-compose.yml exec backend-api pip install qrcode pillow pandas openpyxl && docker-compose -f docker/docker-compose.yml restart backend-api"
```

### Test API
```bash
# Get token
TOKEN=$(curl -s -X POST http://192.168.5.12:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.data.access_token')

# Create test menu
curl -X POST http://192.168.5.12:8001/api/v1/menus \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Restaurant",
    "menu_type": "restaurant",
    "description": "Test menu",
    "show_prices": true
  }' | jq
```

---

## 📊 Timeline Estimate

- **Task 1** (Deploy & Test Backend): 2-3 hours
- **Task 2** (Frontend CMS): 2-3 days
- **Task 3** (Public Viewer): 1-2 days
- **Task 4** (Integration Testing): 1 day

**Total**: 4-6 days for complete implementation

---

## 🎯 Success Criteria

- ✅ Backend API fully functional
- ✅ CMS admin can create/manage menus
- ✅ Excel import works with error handling
- ✅ QR codes auto-generated
- ✅ Public viewer accessible without auth
- ✅ Infinite scroll & lazy loading work smoothly
- ✅ Analytics tracking working
- ✅ Multi-tenant isolation verified
- ✅ Mobile responsive

---

**Last Updated**: 2025-11-26 10:30 WIB
**Next Action**: Deploy & Test Backend (Task 1)
