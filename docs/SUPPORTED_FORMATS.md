# Supported Media Formats

This document lists all media formats supported by the Smart TV Digital Signage system.

## Image Formats

The following image formats are supported and can be uploaded and displayed on the monitor viewer:

### Fully Supported (Recommended)
- **JPEG/JPG** - `.jpg`, `.jpeg`
  - Common format, good compression
  - MIME type: `image/jpeg`
  - ✅ Best for photographs and complex images

- **PNG** - `.png`
  - Lossless compression, supports transparency
  - MIME type: `image/png`
  - ✅ Best for graphics, logos, screenshots

- **WebP** - `.webp`
  - Modern format with excellent compression
  - MIME type: `image/webp`
  - ✅ Best for web delivery (smaller file size)

### Supported (May have limitations)
- **GIF** - `.gif`
  - Supports animation
  - MIME type: `image/gif`
  - ⚠️ Limited color palette (256 colors)

- **SVG** - `.svg`
  - Vector format, scalable
  - MIME type: `image/svg+xml`
  - ⚠️ May not render complex SVGs correctly

- **BMP** - `.bmp`
  - Uncompressed bitmap
  - MIME type: `image/bmp`
  - ⚠️ Large file size, not recommended

## Video Formats

The following video formats are supported using HTML5 video playback:

### Fully Supported (Recommended)
- **MP4** - `.mp4`
  - Codec: H.264 (video) + AAC (audio)
  - MIME type: `video/mp4`
  - ✅ Best compatibility across all browsers
  - ✅ Good compression and quality

### Supported (Browser dependent)
- **WebM** - `.webm`
  - Codec: VP8/VP9 (video) + Vorbis/Opus (audio)
  - MIME type: `video/webm`
  - ⚠️ Not supported in Safari/older browsers

- **Ogg** - `.ogv`, `.ogg`
  - Codec: Theora (video) + Vorbis (audio)
  - MIME type: `video/ogg`
  - ⚠️ Limited browser support

## Format Detection

The system automatically detects the media type based on:
1. **File MIME type** - Determined by the browser during upload
2. **Content-Type header** - Set by the upload process

### Classification Rules
- Files with MIME type starting with `image/` → Image content
- Files with MIME type starting with `video/` → Video content
- Other types → Rejected

## Browser Compatibility

### Chrome/Chromium (Recommended)
✅ All image formats
✅ MP4 (H.264)
✅ WebM (VP8/VP9)
✅ Ogg Theora

### Firefox
✅ All image formats
✅ MP4 (H.264) - with plugins
✅ WebM (VP8/VP9)
✅ Ogg Theora

### Safari
✅ All image formats
✅ MP4 (H.264)
❌ WebM
❌ Ogg Theora

### Edge
✅ All image formats
✅ MP4 (H.264)
✅ WebM (VP9)
⚠️ Ogg Theora (limited)

## Recommended Formats

For best compatibility and performance:

### Images
1. **PNG** - For graphics, logos, text
2. **JPEG** - For photographs
3. **WebP** - For modern browsers (best compression)

### Videos
1. **MP4 with H.264 codec** - Best universal compatibility
   - Resolution: 1920x1080 or lower
   - Bitrate: 2-5 Mbps for HD content
   - Frame rate: 30 fps

## File Size Recommendations

- **Images**: Maximum 5 MB per file
- **Videos**: Maximum 100 MB per file

## Upload Validation

The backend validates:
1. File has a valid MIME type
2. MIME type starts with `image/` or `video/`
3. File content matches declared MIME type

## Metadata Extraction

For video files, the system automatically extracts:
- Duration (seconds)
- Width (pixels)
- Height (pixels)
- Frame rate (fps)
- Video codec
- Audio codec
- File size (bytes)

For image files:
- Width (pixels)
- Height (pixels)
- File size (bytes)

## Testing Checklist

To verify format support:

### Image Testing
- [ ] Upload JPEG image
- [ ] Upload PNG image with transparency
- [ ] Upload WebP image
- [ ] Upload GIF (static)
- [ ] Upload GIF (animated)
- [ ] Verify all images display correctly on viewer

### Video Testing
- [ ] Upload MP4 (H.264) video
- [ ] Upload WebM video
- [ ] Verify video plays automatically
- [ ] Verify video loops correctly
- [ ] Check metadata extraction accuracy

## Troubleshooting

### Image not displaying
- Check MIME type is `image/*`
- Try converting to PNG or JPEG
- Check file size < 5 MB

### Video not playing
- Check MIME type is `video/*`
- Convert to MP4 with H.264 codec
- Check file size < 100 MB
- Ensure video has valid duration

### Metadata extraction failed
- Check file is not corrupted
- Try re-encoding video with ffmpeg
- Verify file has valid video/audio streams

## Future Enhancements

Planned format support:
- [ ] PDF documents (as images)
- [ ] HTML5 content (embedded webpages)
- [ ] MPEG-DASH/HLS streaming
- [ ] Live video streams (RTSP/WebRTC)
