# Server Information

## Production Server
- **IP Address**: 192.168.5.12
- **SSH User**: gzjbbk
- **SSH Password**: Password@2021

## Service Ports (ALL ON SERVER)
- **Port 8000**: Anthias (Digital Signage CMS)
- **Port 8001**: Backend API (FastAPI in Docker) ✅ RUNNING
- **Port 3000**: Web Admin (React/Vite Dev Mode) - Run locally, proxies API to server
- **Port 5433**: PostgreSQL Database ✅ RUNNING
- **Port 8080**: Monitor Viewer (Static HTML) ✅ RUNNING

## URLs
- **Monitor Viewer**: http://192.168.5.12:8080/
- **Web Admin**: http://localhost:3000/ (development - proxies to server)
- **Backend API**: http://192.168.5.12:8001/
- **API Docs**: http://192.168.5.12:8001/docs

## Current Status (ALL FIXED!)
✅ Backend API running in Docker on server (port 8001) - REBUILT with CORS fix!
✅ PostgreSQL database running in Docker on server (port 5433)
✅ Monitor Viewer running on server (port 8080)
✅ Monitor Viewer configured to use correct backend (port 8001, NOT 8000!)
✅ CORS configuration includes server IP (192.168.5.12:8080) - Monitor registration working!
✅ Web Admin can run locally and proxy API calls to server
✅ Dockerfile optimized with PYTHONDONTWRITEBYTECODE=1 to prevent build failures

## Important Notes
- ⚠️ **ALL services MUST run on SERVER (192.168.5.12), NOT localhost**
- ✅ Backend API is running in Docker container (signage-backend)
- ✅ Monitor viewer now points to correct backend (8001) - device registration should work!
- Monitor viewer has heartbeat mechanism (sends every 30s after activation)
- Dashboard shows online/offline based on last_seen < 5 minutes
- Web Admin development server (localhost:3000) proxies /api requests to server backend
