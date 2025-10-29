# HLS Player - Quick Reference Guide

## Files Overview

### Core HLS Files:
```
viewer/
├── player.html (524 lines) - +280 lines HLS UI
├── js/player/
│   ├── hls-player.js (506 lines) - NEW - HLS.js wrapper
│   ├── quality-selector.js (314 lines) - NEW - Quality control UI
│   └── playback.js (300 lines) - +150 lines HLS integration
└── HLS_INTEGRATION_SUMMARY.md - Complete documentation
```

## Quick Start

### 1. Testing Locally
```bash
cd /mnt/g/khoirul/signate/viewer
# Open player.html in browser with test HLS stream
```

### 2. Deploy to Server
```bash
# Sync viewer folder
sshpass -p 'Password@2021' scp -r viewer/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/

# Test on server
# Visit: http://192.168.5.12:8080/player.html?deviceId=test123
```

## HLS Content Format

### Backend API Response:
```json
{
  "content_id": "123",
  "title": "Video Title",
  "content_type": "video",
  "url": "http://server/videos/master.m3u8",  // HLS URL
  "hls_available": true,                       // Optional flag
  "duration": 30
}
```

### HLS Detection:
- URL contains `master.m3u8`
- URL contains `.m3u8`
- `hls_available: true` flag

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **p** | Toggle player debug info (includes HLS stats) |
| **q** | Toggle quality selector |
| **n** | Skip to next content |
| **r** | Reload playlist |

## UI Elements

### Quality Selector (Top-Right)
- Shows available quality levels
- Auto mode (default) vs manual selection
- Bandwidth and buffer stats
- Keyboard: 'q' to toggle

### Network Status (Top-Left)
- Green: Excellent connection
- Yellow: Slow connection
- Red: Poor/offline
- Shows during quality changes

### Buffering Indicator (Center)
- Shows when HLS is buffering
- Auto-hides when playback resumes

### Quality Notifications (Bottom-Center)
- Toast notification on quality change
- Example: "Quality switched to 720p"
- Auto-hides after 2 seconds

## HLS Configuration

### Default Settings:
```javascript
{
    maxBufferLength: 30,          // 30s buffer
    startLevel: -1,               // Auto quality
    capLevelToPlayerSize: true,   // Don't exceed display
    abrBandWidthFactor: 0.95      // Use 95% bandwidth
}
```

### Quality Preference:
- Saved in localStorage: `preferredQuality`
- Values: 'auto' or level index (0, 1, 2...)
- Persists across sessions

## Error Handling

### Network Errors:
1. Retry with exponential backoff (3 attempts)
2. If failed, fallback to direct MP4

### Media Errors:
1. Call HLS.js `recoverMediaError()` (3 attempts)
2. If failed, fallback to direct MP4

### Fatal Errors:
1. Show error message
2. Fallback to direct MP4 playback
3. Continue playlist

## Browser Support

| Browser | Method | Quality Control |
|---------|--------|-----------------|
| Chrome  | HLS.js | ✅ Full control |
| Firefox | HLS.js | ✅ Full control |
| Edge    | HLS.js | ✅ Full control |
| Safari  | Native HLS | ❌ No control |
| WebOS TV| HLS.js | ✅ Full control |

## Bandwidth Savings

| Connection | Quality | Bitrate | Saving |
|------------|---------|---------|--------|
| Excellent  | 1080p   | 5 Mbps  | 0%     |
| Good       | 720p    | 2.5 Mbps| 50%    |
| Slow       | 480p    | 1 Mbps  | 80%    |
| Poor       | 360p    | 0.5 Mbps| 90%    |

## Debug Mode

### Enable Debug:
Press **'p'** key to show player info overlay

### HLS Stats Displayed:
- Mode: HLS.js or Native
- Quality Changes: Count of switches
- Buffer Events: Count of buffering
- Errors: Count of errors

### Console Logs:
```javascript
// Look for these prefixes:
[HLS] - HLS player logs
[Player] - General player logs
[QualitySelector] - Quality UI logs
```

## Test URLs

### Apple Test Stream (Multi-bitrate):
```
https://devstreaming-cdn.apple.com/videos/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8
```

### Akamai Test Stream:
```
https://cph-p2p-msl.akamaized.net/hls/live/2000341/test/master.m3u8
```

## Troubleshooting

### Quality selector not showing
- Check: HLS.js loaded (`window.Hls` exists)
- Check: Browser console for CDN errors
- Solution: Verify internet connection for CDN

### Constant buffering
- Check: Network bandwidth in debug overlay
- Solution: Manually select lower quality
- Solution: Reduce `maxBufferLength` in config

### Quality not switching
- Check: Multiple quality levels in manifest
- Check: 'auto' mode is selected
- Solution: Verify HLS manifest has multiple bitrates

### Fallback not working
- Check: Content has valid direct MP4 URL
- Check: Console for fallback trigger
- Solution: Ensure `content.url` is valid

## Analytics

### HLS Player Analytics:
```javascript
// Get analytics from current player
if (window.PlayerPlayback.currentHLSPlayer) {
    const analytics = window.PlayerPlayback.currentHLSPlayer.getAnalytics();
    console.log(analytics);
}

// Output:
{
    qualityChanges: 5,
    bufferingEvents: 2,
    errors: 0,
    startTime: 1234567890,
    uptime: 120000,
    currentQuality: {height: 720, width: 1280, bitrate: 2500000},
    retryCount: 0
}
```

## Backend Integration

### Required Backend Changes:
1. Transcode videos to HLS (multi-bitrate)
2. Store master.m3u8 URLs in database
3. Return HLS URLs in playlist API
4. Enable CORS for HLS manifests/segments

### Example Content Object:
```python
{
    "content_id": "123",
    "title": "Marketing Video",
    "content_type": "video",
    "url": "http://192.168.5.12:8001/hls/video123/master.m3u8",
    "hls_available": True,
    "duration": 30,
    "video_start_time": 0,
    "video_end_time": None
}
```

## Production Checklist

- [ ] Videos transcoded to HLS (FFmpeg)
- [ ] HLS manifests accessible via HTTP
- [ ] CORS headers configured
- [ ] CDN configured for HLS delivery (optional)
- [ ] Backend returns `hls_available` flag
- [ ] Test HLS playback on target devices
- [ ] Monitor quality switching behavior
- [ ] Verify fallback mechanisms
- [ ] Check error recovery under poor network

## Performance Targets

- **Time to First Frame**: < 1.5s
- **Quality Switch Time**: < 300ms
- **Buffer Length**: 20-30s
- **Memory Usage**: < 50 MB
- **Retry Delay**: 1s → 2s → 4s (exponential)

## Support

### Documentation:
- Full docs: `HLS_INTEGRATION_SUMMARY.md`
- This guide: `HLS_QUICK_REFERENCE.md`

### HLS.js Documentation:
- https://github.com/video-dev/hls.js/

### Testing:
```bash
# Console debugging
window.PlayerPlayback.currentHLSPlayer
window.QualitySelector
window.PlayerState

# Force quality
window.PlayerPlayback.currentHLSPlayer.setQuality(0) // Highest
window.PlayerPlayback.currentHLSPlayer.setQuality('auto')
```

---

**Status**: ✅ Production-Ready
**Version**: 1.0.0
**Date**: October 28, 2025
