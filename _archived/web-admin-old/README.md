# Web Admin Dashboard - Smart TV Digital Signage

React-based admin dashboard for managing content, devices, tags, and content assignments.

## Architecture Role

**Management Interface** - Provides web UI for administrators to:

- Upload and manage media content
- Register and monitor devices (TVs/monitors)
- Create tags for device grouping
- Assign content to devices/tags with priorities
- View device online/offline status

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite 5
- **UI Library**: Ant Design (antd)
- **HTTP Client**: Axios
- **State Management**: React hooks (useState, useEffect)
- **Development Server**: Vite dev server with proxy

## Project Structure

```
web-admin/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ContentList.jsx       # Content table with upload
│   │   ├── DeviceList.jsx        # Device table with activation
│   │   ├── TagManager.jsx        # Tag CRUD operations
│   │   ├── AssignmentManager.jsx # Content → Device/Tag mapping
│   │   └── Dashboard.jsx         # Overview statistics
│   │
│   ├── pages/             # Page components
│   │   ├── Login.jsx
│   │   └── MainLayout.jsx
│   │
│   ├── services/          # API clients
│   │   └── api.js         # Axios instance & API methods
│   │
│   ├── App.jsx            # Root component
│   └── main.jsx           # Entry point
│
├── public/
├── index.html
├── vite.config.js         # Vite configuration (includes proxy)
├── package.json
└── README.md (this file)
```

## Development Setup

### Prerequisites

- Node.js 18+ and npm

### Install Dependencies

```bash
cd web-admin
npm install
```

### Environment Configuration

The dev server uses Vite proxy to forward API calls to the backend server.

No `.env` file needed - proxy configured in `vite.config.js`:

```javascript
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://192.168.5.12:8001',  // Backend API server
        changeOrigin: true,
      }
    }
  }
})
```

### Run Development Server

```bash
npm run dev
```

Access at: **http://localhost:3000**

### How Proxy Works

```
Browser Request:
  http://localhost:3000/api/content/
       ↓
  Vite Dev Server Proxy
       ↓
  http://192.168.5.12:8001/api/content/
       ↓
  Backend API Response
       ↓
  Browser receives response
```

Benefits:
- ✅ No CORS issues during development
- ✅ Work locally without running backend locally
- ✅ Use production backend data

## API Integration

### API Service (`src/services/api.js`)

Axios instance with JWT token interceptor:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',  // Proxied to http://192.168.5.12:8001/api
});

// Automatically add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### API Methods

```javascript
// Authentication
export const authAPI = {
  login: (credentials) => api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

// Content
export const contentAPI = {
  getAll: () => api.get('/content/'),
  upload: (formData) => api.post('/content/', formData),
  update: (id, data) => api.patch(`/content/${id}`, data),
  delete: (id) => api.delete(`/content/${id}`),
  getImage: (id) => `/api/content/${id}/image`,  // Direct URL
  getVideo: (id) => `/api/content/${id}/video`,  // Direct URL
};

// Devices
export const deviceAPI = {
  getAll: () => api.get('/devices/'),
  activate: (id, data) => api.post(`/devices/${id}/activate`, data),
  update: (id, data) => api.put(`/devices/${id}`, data),
  delete: (id) => api.delete(`/devices/${id}`),
};

// Tags & Assignments
export const tagAPI = {
  getAll: () => api.get('/tags/'),
  create: (data) => api.post('/tags/', data),
  delete: (id) => api.delete(`/tags/${id}`),
};

export const assignmentAPI = {
  getAll: () => api.get('/assignments/'),
  create: (data) => api.post('/assignments/', data),
  delete: (id) => api.delete(`/assignments/${id}`),
};
```

## Key Features

### 1. Content Management

Upload images/videos that are stored in Anthias:

```javascript
const handleUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('duration', duration);

  await contentAPI.upload(formData);
};
```

**Note**: Backend creates asset in Anthias and stores metadata in PostgreSQL.

### 2. Device Management

Devices register via viewer apps with activation codes or UUID:

- **Browser Viewer**: 6-digit code activation
- **WebOS Viewer**: UUID-based automatic registration

Admin approves pending devices:

```javascript
const handleActivate = async (deviceId) => {
  await deviceAPI.activate(deviceId, {
    device_name: 'Lobby TV 1',
    device_type: 'webos',
    tags: [1, 2]  // Assign to tags
  });
};
```

### 3. Tag-based Grouping

Create tags for device groups (e.g., "Lobby", "Floor 2"):

```javascript
const handleCreateTag = async () => {
  await tagAPI.create({
    name: 'Lobby TVs',
    description: 'All TVs in lobby area'
  });
};
```

### 4. Content Assignment

Assign content to specific devices OR tags with priority:

```javascript
const handleAssign = async () => {
  await assignmentAPI.create({
    content_id: 42,
    device_id: 1,      // Assign to specific device
    tag_id: null,      // OR assign to tag (mutually exclusive)
    priority: 10       // Higher = shown first
  });
};
```

### 5. Device Status Monitoring

Devices send heartbeat every 30 seconds. Dashboard shows:

- **Online**: `last_seen` < 5 minutes ago
- **Offline**: `last_seen` >= 5 minutes ago

```javascript
const isOnline = (device) => {
  const lastSeen = new Date(device.last_seen);
  const now = new Date();
  return (now - lastSeen) < 5 * 60 * 1000;  // 5 minutes
};
```

## Component Overview

### `ContentList.jsx`

- Upload new content (image/video)
- View content list with thumbnails
- Bulk edit (rename multiple items)
- Delete content
- Toggle active/inactive status

**Preview URLs**: Uses `/api/content/{id}/image` endpoint (requires JWT, proxied through backend)

### `DeviceList.jsx`

- View all registered devices
- Activate pending devices
- Edit device name/type/tags
- Delete devices
- View online/offline status

### `TagManager.jsx`

- Create new tags
- View tag list with device count
- Delete tags (unassigns devices first)

### `AssignmentManager.jsx`

- Assign content to devices or tags
- Set priority levels
- View current assignments
- Remove assignments

### `Dashboard.jsx`

- Total content count
- Total device count
- Online device count
- Recent activity

## Build for Production

```bash
npm run build
```

Output in `dist/` folder. Serve with nginx or other static file server.

**Production nginx config example:**

```nginx
server {
    listen 80;
    server_name admin.example.com;

    root /var/www/signage-admin/dist;
    index index.html;

    # SPA routing - redirect all routes to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://192.168.5.12:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Login not working

Check:

1. Backend running? `curl http://192.168.5.12:8001/docs`
2. Proxy configured in `vite.config.js`?
3. Browser console for error messages
4. Network tab for failed API calls

### Images/videos not showing

Content preview requires authentication. Check:

1. JWT token in localStorage
2. Token not expired (check backend logs)
3. Preview URL format: `/api/content/{id}/image` or `/api/content/{id}/video`

### Device not appearing

Devices must register first via viewer apps:

1. **Browser Viewer**: http://192.168.5.12:8080 → Get 6-digit code → Activate in admin
2. **WebOS Viewer**: http://192.168.5.12:8081 → Auto-registers with UUID

### Bulk edit failing

Check browser console. Common issues:

- HTTP method mismatch (use PATCH not PUT)
- Missing required fields
- Backend Anthias sync failing (database should still update)

## Sync to Server

Web admin runs **locally** in development mode. For production:

```bash
# Build production bundle
npm run build

# Sync dist/ to server
sshpass -p 'Password@2021' scp -r dist/ gzjbbk@192.168.5.12:/var/www/signage-admin/

# Configure nginx on server to serve dist/
```

## Security Notes

- JWT tokens stored in `localStorage`
- Tokens expire after 15 minutes (refresh by re-login)
- All API calls require authentication except `/api/client/*`
- Content preview URLs proxied through backend (not direct Anthias access)

## Important Links

- Root README: `../README.md` - Project overview
- Backend README: `../backend/README.md` - API documentation
- CLAUDE.md: Server credentials and deployment workflow
