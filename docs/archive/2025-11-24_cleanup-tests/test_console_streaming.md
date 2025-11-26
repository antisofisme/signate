# Test Console Streaming

## 1. Buka Player Browser
http://192.168.5.12:8080/

## 2. Buka Console Browser (F12)

## 3. Paste dan Jalankan Script Ini:

```javascript
// Generate test logs
console.log('[TEST] Console streaming test 1');
console.info('[TEST] This is an info message');
console.warn('[TEST] This is a warning message');  
console.error('[TEST] This is an error message');
console.log('[TEST] Console streaming test 2');

// Check if interceptor is active
setTimeout(() => {
  console.log('[TEST] Delayed log after 2 seconds');
}, 2000);

setTimeout(() => {
  console.log('[TEST] Delayed log after 5 seconds');
}, 5000);
```

## 4. Monitor Console Output

Cari pesan seperti:
- `[ConsoleInterceptor] Captured log: [TEST]...`
- `[ConsoleInterceptor] Uploading batch...`
- `[ConsoleInterceptor] Batch uploaded successfully`

## 5. Tunggu 5-10 Detik

Console interceptor akan batch dan upload setiap 5 detik atau ketika ada 20 logs.

## 6. Check CMS UI

Buka device modal → Console tab. Logs harus muncul dalam 10 detik.

## Expected Flow:
1. Player console.log → Intercepted
2. Batched (max 20 logs or 5 seconds)
3. POST to /api/v1/devices/7650/console/upload
4. Backend broadcasts via Redis
5. CMS WebSocket receives
6. UI updates with new logs
