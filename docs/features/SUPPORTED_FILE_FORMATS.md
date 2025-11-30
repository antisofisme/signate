# Supported File Formats

**Last Updated**: 2025-11-29
**Status**: ✅ IMPLEMENTED - Semua ekstensi sudah ditambahkan

---

## Overview

Dokumentasi ini mencatat semua ekstensi file yang didukung untuk upload konten di CMS Signage, serta rekomendasi ekstensi tambahan yang bisa ditambahkan.

---

## Currently Supported (Production)

### IMAGE (11 ekstensi)

| Extension | MIME Type | Status | Notes |
|-----------|-----------|--------|-------|
| `.jpg` | image/jpeg | ✅ Active | |
| `.jpeg` | image/jpeg | ✅ Active | |
| `.png` | image/png | ✅ Active | |
| `.webp` | image/webp | ✅ Active | |
| `.gif` | image/gif | ✅ Active | |
| `.bmp` | image/bmp | ✅ Active | |
| `.tiff` | image/tiff | ✅ Active | Print quality |
| `.tif` | image/tiff | ✅ Active | Print quality |
| `.heic` | image/heic | ✅ Active | iPhone photos |
| `.heif` | image/heif | ✅ Active | iPhone photos |
| `.avif` | image/avif | ✅ Active | Modern format |

### VIDEO (16 ekstensi)

| Extension | MIME Type | Status | Notes |
|-----------|-----------|--------|-------|
| `.mp4` | video/mp4 | ✅ Active | |
| `.webm` | video/webm | ✅ Active | |
| `.mkv` | video/x-matroska | ✅ Active | |
| `.avi` | video/x-msvideo | ✅ Active | |
| `.mov` | video/quicktime | ✅ Active | |
| `.m4v` | video/x-m4v | ✅ Active | |
| `.flv` | video/x-flv | ✅ Active | |
| `.wmv` | video/x-ms-wmv | ✅ Active | Windows Media |
| `.mpg` | video/mpeg | ✅ Active | Legacy MPEG |
| `.mpeg` | video/mpeg | ✅ Active | Legacy MPEG |
| `.3gp` | video/3gpp | ✅ Active | Mobile video |
| `.3g2` | video/3gpp2 | ✅ Active | Mobile video |
| `.mts` | video/mp2t | ✅ Active | HD Camcorder |
| `.m2ts` | video/mp2t | ✅ Active | HD Camcorder |
| `.ts` | video/mp2t | ✅ Active | MPEG-TS |
| `.ogv` | video/ogg | ✅ Active | Ogg Video |

### AUDIO (14 ekstensi)

| Extension | MIME Type | Status | Notes |
|-----------|-----------|--------|-------|
| `.mp3` | audio/mpeg | ✅ Active | |
| `.aac` | audio/aac | ✅ Active | |
| `.m4a` | audio/mp4 | ✅ Active | |
| `.ogg` | audio/ogg | ✅ Active | |
| `.wav` | audio/wav | ✅ Active | |
| `.flac` | audio/flac | ✅ Active | |
| `.wma` | audio/x-ms-wma | ✅ Active | |
| `.mpeg` | audio/mpeg | ✅ Active | WhatsApp audio |
| `.opus` | audio/opus | ✅ Active | Modern codec |
| `.amr` | audio/amr | ✅ Active | Mobile recordings |
| `.aiff` | audio/aiff | ✅ Active | Apple format |
| `.aif` | audio/aiff | ✅ Active | Apple format |
| `.oga` | audio/ogg | ✅ Active | Ogg Audio |
| `.weba` | audio/webm | ✅ Active | WebM Audio |

---

## Previously Recommended (Now Implemented)

Ekstensi-ekstensi berikut sudah ditambahkan pada 2025-11-29:

### IMAGE - Tambahan (5 ekstensi)

| Extension | MIME Type | Keterangan | Priority |
|-----------|-----------|------------|----------|
| `.tiff` | image/tiff | Print quality, professional | HIGH |
| `.tif` | image/tiff | Alias for tiff | HIGH |
| `.heic` | image/heic | Apple/iPhone photos | HIGH |
| `.heif` | image/heif | Apple/iPhone photos | HIGH |
| `.avif` | image/avif | Modern format, better compression | MEDIUM |

**Code untuk ditambahkan:**
```python
# upload_content.py & file_security.py
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp',
    '.tiff', '.tif',   # Print quality
    '.heic', '.heif',  # iPhone photos
    '.avif',           # Modern format
}
```

### VIDEO - Tambahan (8 ekstensi)

| Extension | MIME Type | Keterangan | Priority |
|-----------|-----------|------------|----------|
| `.wmv` | video/x-ms-wmv | Windows Media Video | HIGH |
| `.mpg` | video/mpeg | Legacy MPEG | HIGH |
| `.mpeg` | video/mpeg | Legacy MPEG | HIGH |
| `.3gp` | video/3gpp | Mobile video | MEDIUM |
| `.3g2` | video/3gpp2 | Mobile video | MEDIUM |
| `.mts` | video/mp2t | HD Camcorder (AVCHD) | MEDIUM |
| `.m2ts` | video/mp2t | HD Camcorder (Blu-ray) | MEDIUM |
| `.ts` | video/mp2t | MPEG Transport Stream | MEDIUM |
| `.ogv` | video/ogg | Ogg Video | LOW |

**Code untuk ditambahkan:**
```python
# upload_content.py & file_security.py
VIDEO_EXTENSIONS = {
    '.mp4', '.webm', '.mkv', '.avi', '.mov', '.m4v', '.flv',
    '.wmv',           # Windows Media
    '.mpg', '.mpeg',  # Legacy MPEG
    '.3gp', '.3g2',   # Mobile
    '.mts', '.m2ts',  # HD Camcorder
    '.ts',            # MPEG Transport Stream
    '.ogv',           # Ogg Video
}
```

### AUDIO - Tambahan (7 ekstensi)

| Extension | MIME Type | Keterangan | Priority |
|-----------|-----------|------------|----------|
| `.mpeg` | audio/mpeg | MPEG Audio (WhatsApp) | HIGH |
| `.opus` | audio/opus | Modern codec, efficient | MEDIUM |
| `.amr` | audio/amr | Mobile recordings | MEDIUM |
| `.aiff` | audio/aiff | Apple audio format | MEDIUM |
| `.aif` | audio/aiff | Alias for aiff | MEDIUM |
| `.oga` | audio/ogg | Ogg Audio | LOW |
| `.weba` | audio/webm | WebM Audio | LOW |

**Code untuk ditambahkan:**
```python
# upload_content.py & file_security.py
AUDIO_EXTENSIONS = {
    '.mp3', '.aac', '.m4a', '.ogg', '.wav', '.flac', '.wma',
    '.mpeg',          # MPEG Audio (WhatsApp)
    '.opus',          # Modern codec
    '.amr',           # Mobile recordings
    '.aiff', '.aif',  # Apple format
    '.oga',           # Ogg Audio
    '.weba',          # WebM Audio
}
```

---

## MIME Type Mappings

Untuk `file_security.py`, tambahkan MIME type berikut:

```python
MIME_TYPES = {
    "image": {
        # Existing
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/bmp", "image/x-ms-bmp",
        # New
        "image/tiff", "image/heic", "image/heif", "image/avif",
    },
    "video": {
        # Existing
        "video/mp4", "video/x-msvideo", "video/x-matroska",
        "video/quicktime", "video/webm", "video/x-flv", "video/x-ms-wmv",
        # New
        "video/mpeg", "video/3gpp", "video/3gpp2", "video/mp2t", "video/ogg",
    },
    "audio": {
        # Existing
        "audio/mpeg", "audio/wav", "audio/x-wav", "audio/flac",
        "audio/aac", "audio/ogg", "audio/mp4", "audio/x-ms-wma",
        # New
        "audio/opus", "audio/amr", "audio/aiff", "audio/x-aiff", "audio/webm",
    },
}
```

---

## Forbidden Extensions (Security Risk)

Ekstensi berikut **TIDAK BOLEH** ditambahkan karena security risk:

| Extension | Reason |
|-----------|--------|
| `.svg` | Can contain JavaScript/XSS attacks |
| `.html`, `.htm` | Can contain scripts |
| `.js`, `.jsx`, `.ts`, `.tsx` | Executable scripts |
| `.php`, `.asp`, `.aspx`, `.jsp` | Server-side scripts |
| `.exe`, `.bat`, `.cmd`, `.sh`, `.ps1` | Executables |
| `.dll`, `.so`, `.dylib` | Libraries |
| `.zip`, `.rar`, `.7z`, `.tar`, `.gz` | Archives (can contain malware) |
| `.pdf` | Can contain scripts (optional with sanitization) |

---

## File Size Limits

| Type | Default Max Size | Environment Variable |
|------|------------------|---------------------|
| Image | 50 MB | `MAX_IMAGE_SIZE_MB` |
| Video | 500 MB | `MAX_VIDEO_SIZE_MB` |
| Audio | 100 MB | `MAX_AUDIO_SIZE_MB` |

---

## Files to Modify

Untuk implementasi, update file berikut:

1. **Backend:**
   - `backend-python/services/content/use_cases/upload_content.py`
     - `IMAGE_EXTENSIONS`
     - `VIDEO_EXTENSIONS`
     - `AUDIO_EXTENSIONS`

   - `backend-python/shared/file_security.py`
     - `ALLOWED_EXTENSIONS`
     - `MIME_TYPES`

2. **Frontend (optional - untuk file picker filter):**
   - `cms-vite/src/features/contents/components/UploadModal.tsx`
     - Update `accept` attribute pada file input

---

## Implementation Checklist

- [x] Update `upload_content.py` dengan ekstensi baru (2025-11-29)
- [x] Update `file_security.py` dengan ekstensi dan MIME types baru (2025-11-29)
- [x] Update `cms-vite/src/lib/constants/app.ts` - ALLOWED_*_TYPES (2025-11-29)
- [x] Update `UploadModal.tsx` - UI display extensions (2025-11-29)
- [x] Update `video_routes.py` - Dynamic MIME type detection (2025-11-29)
- [x] Update `player-videojs.ts` - Comprehensive MIME type detection (2025-11-29)
- [x] Deploy ke server VPS (2025-11-29)
- [ ] Test upload untuk setiap ekstensi baru
- [ ] Verify di production

---

## Sample Files for Testing

File contoh tersedia di `file-contoh/`:

| File | Extension | Current Status |
|------|-----------|----------------|
| `*.jpg` | .jpg | ✅ Supported |
| `*.jpeg` | .jpeg | ✅ Supported |
| `*.png` | .png | ✅ Supported |
| `*.gif` | .gif | ✅ Supported |
| `*.webp` | .webp | ✅ Supported |
| `*.mp4` | .mp4 | ✅ Supported |
| `*.avi` | .avi | ✅ Supported |
| `*.mov` | .mov | ✅ Supported |
| `*.webm` | .webm | ✅ Supported |
| `*.wmv` | .wmv | ✅ Supported |
| `*.mp3` | .mp3 | ✅ Supported |
| `*.ogg` | .ogg | ✅ Supported |
| `*.wav` | .wav | ✅ Supported |
| `WhatsApp Audio *.mpeg` | .mpeg | ✅ Supported |
| `*.tiff` | .tiff | ✅ Supported |
| `*.svg` | .svg | ❌ FORBIDDEN - security risk |

---

## References

- [MDN MIME Types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types)
- [IANA Media Types](https://www.iana.org/assignments/media-types/media-types.xhtml)
- [FFmpeg Supported Formats](https://ffmpeg.org/general.html#Supported-File-Formats_002c-Codecs-or-Features)
