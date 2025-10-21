# Anthias Ready Files

File-file yang sudah siap pakai untuk deployment Anthias dengan custom viewer.

## 📁 Contents

### `docker-compose.dev.yml`
Docker Compose file yang sudah dikonfigurasi dengan:
- ✅ Container names dengan prefix `anthias-` 
- ✅ Volume mounting untuk custom viewers
- ✅ Proper networking configuration
- ✅ Redis naming yang benar

### `nginx.development.conf`
Nginx configuration yang sudah include:
- ✅ Custom viewer endpoint `/viewer`
- ✅ Proper content-type headers untuk HTML
- ✅ Static file serving configuration
- ✅ API proxy configuration

### `custom-viewers/viewer.html`
Enhanced custom viewer dengan features:
- ✅ **Horizontal slide layout** (bukan vertical scrolling)
- ✅ **Fullscreen slideshow** dengan keyboard navigation
- ✅ **Configuration panel** dengan localStorage
- ✅ **API integration** dengan Anthias backend
- ✅ **Touch/swipe support** untuk mobile devices
- ✅ **Responsive design** untuk berbagai screen sizes

## 🚀 Usage

1. **Copy docker-compose.dev.yml**:
   ```bash
   cp docker-compose.dev.yml /path/to/anthias/
   ```

2. **Copy nginx config**:
   ```bash
   cp nginx.development.conf /path/to/anthias/docker/nginx/
   ```

3. **Copy custom viewer**:
   ```bash
   mkdir -p /path/to/anthias/static/custom-viewers/
   cp custom-viewers/viewer.html /path/to/anthias/static/custom-viewers/
   ```

4. **Start Anthias**:
   ```bash
   cd /path/to/anthias
   docker-compose -f docker-compose.dev.yml up -d
   ```

5. **Access viewer**:
   ```
   http://anthias.local:8000/viewer
   ```

## 🎯 Features

### Keyboard Controls
- **Arrow Keys**: Navigate slides
- **Spacebar**: Play/pause slideshow
- **F**: Toggle fullscreen
- **Escape**: Exit fullscreen

### Configuration
- **Slide Duration**: 1-30 seconds
- **Autoplay**: On/off
- **Loop**: On/off
- **Server URL**: Configurable

### Browser Support
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers

---

*Files ini sudah tested dan ready untuk production deployment.*