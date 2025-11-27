# Offline Caching System

Sistem caching offline untuk monitor viewer menggunakan **IndexedDB** untuk menyimpan media files secara lokal di browser.

## 🎯 Tujuan

1. **Hemat Bandwidth** - Download konten sekali saja, tidak streaming terus-menerus
2. **Hemat Kuota** - Hanya download konten baru saat ada update playlist
3. **Performa Lebih Cepat** - Play dari cache lokal, tidak ada delay streaming
4. **Offline Playback** - Bisa play konten meskipun koneksi internet terputus

## 🔧 Cara Kerja

### 1. Initialization (Saat Viewer Start)
```
Monitor Viewer Start
  ↓
Initialize IndexedDB (SignageMediaCache)
  ↓
Load Playlist dari Backend
  ↓
Sync Cache: Download konten yang belum ada
  ↓
Play Content dari Cache
```

### 2. Download & Cache Process
```
Get Playlist dari Backend
  ↓
Cek setiap konten:
  - Sudah di cache? → Skip
  - Belum di cache? → Download & Save to IndexedDB
  ↓
Cache Ready for Playback
```

### 3. Playback Process
```
Play Content
  ↓
Cek Cache: Ada di IndexedDB?
  ├─ Yes → Buat Blob URL → Play from Cache 📦
  └─ No  → Stream dari URL 📡
```

### 4. Playlist Update Process
```
Playlist Berubah (setiap 10 detik cek)
  ↓
Compare Old vs New Playlist
  ↓
Sync Cache:
  - Hapus konten yang tidak ada di playlist baru 🗑️
  - Download konten baru yang belum di cache ⬇️
  ↓
Cache Updated
```

## 📦 IndexedDB Structure

**Database Name:** `SignageMediaCache`
**Version:** 1
**Object Store:** `mediaFiles`

### Schema
```javascript
{
  content_id: number,        // Primary Key
  title: string,             // Content title
  url: string,              // Original URL (for reference)
  content_type: string,     // 'image' or 'video'
  mime_type: string,        // 'image/jpeg', 'video/mp4', etc.
  blob: Blob,               // Actual media file data
  size: number,             // File size in bytes
  timestamp: number         // When cached (milliseconds)
}
```

### Indexes
- `url` - Index untuk lookup by URL
- `timestamp` - Index untuk sort by cache time

## 🔄 API Functions

### Initialize Cache
```javascript
await initMediaCache()
```
Membuat atau membuka database IndexedDB.

### Check if Cached
```javascript
const isCached = await isContentCached(contentId)
```
Returns `true` jika konten sudah di cache.

### Get Cached Content
```javascript
const cached = await getCachedContent(contentId)
```
Returns cache entry object atau `undefined`.

### Download and Cache
```javascript
await downloadAndCacheContent(content)
```
Download konten dari URL dan simpan ke cache.

### Get Blob URL for Playback
```javascript
const blobUrl = await getCachedBlobUrl(contentId)
```
Returns blob URL untuk digunakan di `<img>` atau `<video>`.

### Sync Cache with Playlist
```javascript
await syncCacheWithPlaylist(newPlaylist)
```
- Hapus konten yang tidak ada di playlist
- Download konten baru yang belum di cache

### Delete from Cache
```javascript
await deleteFromCache(contentId)
```
Hapus konten spesifik dari cache.

## 💾 Storage Capacity

Browser mengizinkan IndexedDB storage:

- **Chrome/Edge**: ~60% dari disk space available (bisa sampai 100+ GB)
- **Firefox**: ~50% dari disk space available
- **Safari**: ~1 GB (iOS), ~10% dari disk (macOS)

### Estimasi Kapasitas

Asumsi video 1920x1080 @ 30fps, H.264:
- **1 menit video**: ~10-20 MB
- **10 konten video (@ 30 detik)**: ~100-200 MB
- **50 konten video (@ 30 detik)**: ~500 MB - 1 GB

Asumsi image 1920x1080 PNG/JPEG:
- **1 image**: ~500 KB - 2 MB
- **50 images**: ~25-100 MB

**Total untuk 50 konten mixed (30 images + 20 videos):**
~350 MB - 600 MB ✅ Sangat cukup!

## 🚀 Performance Benefits

### Sebelum (Streaming Mode)
```
Play Content:
  Request → Network → Stream → Play
  - Latency: ~100-500ms
  - Bandwidth: Continuous streaming
  - Data usage: Ulang setiap kali play
```

### Sesudah (Cache Mode)
```
First Play:
  Request → Network → Download → Cache → Play
  - Latency: ~100-500ms (download once)

Subsequent Plays:
  Cache → Blob URL → Play
  - Latency: ~5-10ms ⚡
  - Bandwidth: Zero! 🎉
  - Data usage: Hanya sekali saat download
```

### Contoh Penghematan

Playlist dengan 10 konten (total 500 MB):

**Tanpa Cache (Streaming):**
- Play 1 loop = 500 MB downloaded
- Play 10 loops/hari = 5 GB/hari 😱
- Play 30 hari = 150 GB/bulan 💸

**Dengan Cache:**
- Download 1x = 500 MB
- Play unlimited = 0 MB tambahan 🎉
- Total 30 hari = 500 MB (+ update) ✅

**Penghematan: ~99.7% bandwidth!**

## 🔍 Monitoring & Debugging

### Check Cache in Browser DevTools

1. **Buka DevTools** (F12)
2. **Go to Application tab**
3. **Expand IndexedDB**
4. **Select** `SignageMediaCache` → `mediaFiles`
5. **View** all cached content

### Console Logs

Sistem memberikan log yang jelas:

```javascript
✅ IndexedDB opened successfully
📦 Media cache initialized
⬇️  Downloading content 35: Banner Promo
✅ Cached content 35 (15.2 MB)
🔄 Cache synced: +3 downloaded, -1 removed
📦 Using cached content (ID: 35)
📡 Content not cached, streaming (ID: 42)
```

### Indicators

- `📦` = Using cache
- `📡` = Streaming
- `⬇️` = Downloading
- `🗑️` = Removing
- `🔄` = Syncing

## ⚙️ Configuration

```javascript
// Cache database settings
const DB_NAME = 'SignageMediaCache'
const DB_VERSION = 1
const STORE_NAME = 'mediaFiles'

// Playlist refresh interval
const PLAYLIST_REFRESH_INTERVAL = 10000 // 10 seconds
```

## 🧪 Testing

### Test Cache Functionality

1. **Open Viewer** → http://192.168.5.12:8080/
2. **Activate Device** in Web Admin
3. **Assign Content** to device
4. **Check Console**:
   ```
   ⬇️  Downloading content...
   ✅ Cached content...
   📦 Using cached content...
   ```
5. **Check DevTools** → Application → IndexedDB
6. **Verify**: Content ada di cache

### Test Offline Playback

1. **Buka Viewer** dengan content cached
2. **Open DevTools** → Network tab
3. **Set to Offline** mode
4. **Content should still play** dari cache! 🎉

### Test Cache Sync

1. **Add new content** di Web Admin
2. **Assign to device**
3. **Wait 10 seconds** (playlist refresh)
4. **Check Console**: Should see download log
5. **New content** will be cached automatically

### Test Cache Cleanup

1. **Remove content** from device in Web Admin
2. **Wait 10 seconds**
3. **Check Console**: Should see removal log
4. **Check DevTools**: Content removed from cache

## ⚠️ Known Limitations

1. **Safari iOS**: Limited to ~1GB storage
2. **Private/Incognito Mode**: Cache cleared when closing browser
3. **Low Disk Space**: Browser may refuse to cache
4. **Large Files**: Video >100MB may fail to cache on some browsers

## 🐛 Troubleshooting

### Content Not Caching

**Problem**: Console shows "Content not cached, streaming"

**Solutions**:
1. Check browser support (needs IndexedDB)
2. Check disk space available
3. Check file size (<100MB recommended)
4. Check browser console for errors

### Cache Not Syncing

**Problem**: New content not downloading automatically

**Solutions**:
1. Check playlist refresh is running
2. Check network connectivity
3. Check backend API is reachable
4. Manually reload: Press 'r' key

### Memory Leak

**Problem**: Browser using too much memory

**Solutions**:
- Blob URLs are auto-revoked when changing content
- Cache is bounded by playlist size
- Clear cache: Delete IndexedDB in DevTools

## 🔐 Security

- Cache stored in browser's origin-isolated storage
- Content only accessible by same origin
- No cross-site access possible
- Cache cleared when browser data is cleared

## 📊 Future Enhancements

Planned improvements:

- [ ] Cache size limit with LRU eviction
- [ ] Compression for images before caching
- [ ] Progressive download with priority queue
- [ ] Cache statistics dashboard
- [ ] Manual cache control in Web Admin
- [ ] Offline mode indicator in viewer UI

---

**Status**: ✅ Implemented & Deployed
**Last Updated**: 2025-10-23
**Version**: 1.0
