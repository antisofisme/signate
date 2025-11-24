# Console Interceptor Flow Diagrams

## 1. Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Player-Vite Application                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │   User Code      │          │  Third-Party Libs │            │
│  │                  │          │                   │            │
│  │ console.log()    │          │ console.error()   │            │
│  │ console.warn()   │          │ console.debug()   │            │
│  └────────┬─────────┘          └────────┬──────────┘            │
│           │                             │                        │
│           └──────────────┬──────────────┘                        │
│                          │                                       │
│                          ▼                                       │
│           ┌──────────────────────────────┐                      │
│           │   Browser Console (Replaced) │                      │
│           │   ConsoleInterceptor Layer   │                      │
│           └──────────┬───────────────────┘                      │
│                      │                                           │
│         ┌────────────┴────────────┐                             │
│         │                         │                             │
│         ▼                         ▼                             │
│  ┌─────────────┐          ┌──────────────┐                     │
│  │  Original   │          │  Capture &   │                     │
│  │  Console    │          │  Buffer Log  │                     │
│  │  (Visual)   │          │  Entry       │                     │
│  └─────────────┘          └──────┬───────┘                     │
│                                   │                             │
│                                   ▼                             │
│                          ┌─────────────────┐                    │
│                          │  Serialize Args │                    │
│                          │  (Circular Safe)│                    │
│                          └────────┬────────┘                    │
│                                   │                             │
│                                   ▼                             │
│                          ┌─────────────────┐                    │
│                          │  Buffer (Max    │                    │
│                          │  100 entries)   │                    │
│                          └────────┬────────┘                    │
│                                   │                             │
│                    ┌──────────────┴───────────────┐             │
│                    │                                │            │
│                    ▼                                ▼            │
│           ┌─────────────────┐            ┌──────────────┐       │
│           │  Auto Flush     │            │  Immediate   │       │
│           │  (30s interval) │            │  (on error)  │       │
│           └────────┬────────┘            └──────┬───────┘       │
│                    │                            │               │
│                    └────────────┬───────────────┘               │
│                                 │                               │
│                                 ▼                               │
│                        ┌──────────────────┐                     │
│                        │ SharedAPIClient  │                     │
│                        │ POST /api/...    │                     │
│                        └────────┬─────────┘                     │
│                                 │                               │
└─────────────────────────────────┼───────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │   Backend API (FastAPI)  │
                    │ /api/client/console-logs │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   PostgreSQL DB      │
                    │   console_logs table │
                    └──────────────────────┘
```

---

## 2. SharedLogger vs ConsoleInterceptor - NO CONFLICT

```
┌─────────────────────────────────────────────────────────────────┐
│                    Initialization Sequence                       │
└─────────────────────────────────────────────────────────────────┘

Step 1: Application Starts
┌──────────────────────────────────────┐
│ SharedLogger Class Instantiated      │
│                                      │
│ originalConsole = {                  │
│   log: console.log.bind(console)     │  ← Captures REAL browser console
│ }                                    │
└──────────────────────────────────────┘

Step 2: ConsoleInterceptor Initialized (in main.ts)
┌──────────────────────────────────────┐
│ ConsoleInterceptor.init()            │
│                                      │
│ originalConsole = {                  │
│   log: console.log.bind(console)     │  ← Also captures REAL browser console
│ }                                    │
│                                      │
│ console.log = interceptedLog         │  ← REPLACES browser console
└──────────────────────────────────────┘

Step 3: User Code Logs
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  User calls: console.log("test")                              │
│      │                                                         │
│      ▼                                                         │
│  ConsoleInterceptor.interceptedLog("test")                    │
│      │                                                         │
│      ├─► originalConsole.log("test")  ← Shows in browser     │
│      │                                                         │
│      └─► captureLog("test")           ← Buffers for backend   │
│                                                                │
└────────────────────────────────────────────────────────────────┘

Step 4: SharedLogger Logs
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  App calls: SharedLogger.log("app message")                   │
│      │                                                         │
│      ▼                                                         │
│  SharedLogger internal logic                                  │
│      │                                                         │
│      └─► this.originalConsole.log("app message")              │
│             │                                                  │
│             └─► REAL browser console (BYPASSES interceptor)   │
│                                                                │
│  NO LOOP - Different console reference!                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. Circular Reference Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│           console.log(objectWithCircularRef)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │ serializeConsoleArgs()   │
              └──────────┬───────────────┘
                         │
                         ▼
           ┌─────────────────────────────┐
           │ For each arg in args:       │
           │                             │
           │ if (primitive)              │
           │   return String(arg)        │
           │                             │
           │ if (object)                 │
           │   use safeJSONStringify()   │
           └─────────┬───────────────────┘
                     │
                     ▼
      ┌──────────────────────────────────┐
      │ safeJSONStringify(obj)           │
      │                                  │
      │ replacer = createCircularReplacer()│
      └──────────┬───────────────────────┘
                 │
                 ▼
   ┌─────────────────────────────────────┐
   │ JSON.stringify(obj, replacer)       │
   │                                     │
   │ For each property:                  │
   │   if (seen.has(value))              │
   │     return "[Circular Reference]"   │
   │                                     │
   │   if (depth > maxDepth)             │
   │     return "[Max Depth Exceeded]"   │
   │                                     │
   │   if (string.length > maxLength)    │
   │     return truncated + "[truncated]"│
   │                                     │
   │   seen.add(value)                   │
   │   continue traversing               │
   └─────────┬───────────────────────────┘
             │
             ▼
  ┌──────────────────────────┐
  │ Return:                  │
  │ {                        │
  │   json: "...",           │
  │   hadCircular: true,     │
  │   wasTruncated: false    │
  │ }                        │
  └──────────────────────────┘
```

---

## 4. Buffer & Flush Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     Buffer Management                            │
└─────────────────────────────────────────────────────────────────┘

Incoming Console Logs
       │
       ▼
┌──────────────┐
│ Capture Log  │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────┐
│ Add to Buffer (Array)       │
│                             │
│ buffer.push(logEntry)       │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐     YES    ┌─────────────────┐
│ buffer.length >= 100?       │──────────► │  AUTO FLUSH     │
└──────┬──────────────────────┘            └─────────────────┘
       │ NO
       ▼
┌─────────────────────────────┐     YES    ┌─────────────────┐
│ level === 'error'?          │──────────► │ IMMEDIATE FLUSH │
└──────┬──────────────────────┘            └─────────────────┘
       │ NO
       ▼
┌─────────────────────────────┐
│ Wait for Periodic Flush     │
│ (setInterval 30s)           │
└─────────────────────────────┘


Periodic Timer (every 30 seconds)
       │
       ▼
┌─────────────────────────────┐     NO     ┌─────────────────┐
│ buffer.length > 0?          │──────────► │   DO NOTHING    │
└──────┬──────────────────────┘            └─────────────────┘
       │ YES
       ▼
┌─────────────────────────────┐
│      FLUSH TO BACKEND       │
└─────────────────────────────┘
```

---

## 5. Retry Mechanism (Exponential Backoff)

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flush Logs                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │ Copy buffer → logsToSend │
              │ Clear buffer = []        │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │ sendWithRetry(attempt=1) │
              └──────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │ SharedAPIClient.post()         │
        └──────┬────────────┬────────────┘
               │            │
         SUCCESS          FAILURE
               │            │
               ▼            ▼
      ┌─────────────┐   ┌──────────────────────┐
      │   LOG OK    │   │ attempt < maxRetries?│
      └─────────────┘   └──────┬───────────────┘
                               │
                         YES   │   NO
                     ┌─────────┴────────┐
                     │                  │
                     ▼                  ▼
         ┌────────────────────┐   ┌──────────────┐
         │ Calculate Delay    │   │  GIVE UP     │
         │                    │   │  Log Error   │
         │ delay = 1000 *     │   └──────────────┘
         │   2^(attempt-1)    │
         │                    │
         │ Attempt 1: 1000ms  │
         │ Attempt 2: 2000ms  │
         │ Attempt 3: 4000ms  │
         └─────────┬──────────┘
                   │
                   ▼
         ┌────────────────────┐
         │ setTimeout(delay)  │
         └─────────┬──────────┘
                   │
                   ▼
         ┌────────────────────────┐
         │ sendWithRetry(attempt+1)│
         └────────────────────────┘
```

---

## 6. Memory Management Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                  Memory Leak Prevention                          │
└─────────────────────────────────────────────────────────────────┘

1. Buffer Size Limit
   ┌──────────────────────────┐
   │ if buffer.length >= 100  │
   │   flush() immediately    │  ← Prevents unbounded growth
   └──────────────────────────┘

2. Argument Truncation
   ┌──────────────────────────┐
   │ if string.length > 10000 │
   │   truncate to 10000      │  ← Prevents huge payloads
   └──────────────────────────┘

3. Object Depth Limit
   ┌──────────────────────────┐
   │ if depth > 10            │
   │   stop traversing        │  ← Prevents deep recursion
   └──────────────────────────┘

4. Circular Reference Detection
   ┌──────────────────────────┐
   │ if seen.has(obj)         │
   │   return "[Circular]"    │  ← Prevents infinite loops
   └──────────────────────────┘

5. Periodic Cleanup
   ┌──────────────────────────┐
   │ Every 30s:               │
   │   flush and clear buffer │  ← Prevents accumulation
   └──────────────────────────┘

6. Device Deactivation Cleanup
   ┌──────────────────────────┐
   │ On device:cleared event: │
   │   clearBuffer()          │  ← Cleanup on logout
   └──────────────────────────┘
```

---

## 7. Backend Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend → Backend                          │
└─────────────────────────────────────────────────────────────────┘

Frontend (Player-Vite)
       │
       ▼
┌──────────────────────────────┐
│ ConsoleInterceptor.flush()   │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ SharedAPIClient.post()       │
│                              │
│ POST /api/client/console-logs│
│                              │
│ Headers:                     │
│   Authorization: Bearer XXX  │
│   Content-Type: application/json│
│                              │
│ Body:                        │
│ {                            │
│   device_id: 123,            │
│   logs: [                    │
│     {                        │
│       level: "error",        │
│       args: ["...", "..."],  │
│       timestamp: "...",      │
│       stackTrace: "..."      │
│     }                        │
│   ]                          │
│ }                            │
└──────────┬───────────────────┘
           │
           ▼
Backend (FastAPI)
       │
       ▼
┌──────────────────────────────┐
│ POST /api/client/console-logs│
│ /batch                       │
│                              │
│ 1. Verify device_token       │
│ 2. Validate device_id        │
│ 3. Parse logs array          │
│ 4. Insert into DB            │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ PostgreSQL                   │
│                              │
│ INSERT INTO console_logs     │
│ (device_id, level, args,     │
│  timestamp, stack_trace)     │
│ VALUES (?, ?, ?, ?, ?)       │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Response                     │
│                              │
│ {                            │
│   success: true,             │
│   data: {                    │
│     received: 50,            │
│     stored: 50               │
│   }                          │
│ }                            │
└──────────────────────────────┘
```

---

## 8. Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Development & Testing                          │
└─────────────────────────────────────────────────────────────────┘

Phase 1: Local Development
┌──────────────────────────────┐
│ 1. Implement circular replacer│
│ 2. Write unit tests          │
│ 3. Implement interceptor     │
│ 4. Test in isolation         │
└──────────┬───────────────────┘
           │
           ▼
Phase 2: Integration
┌──────────────────────────────┐
│ 1. Add to main.ts            │
│ 2. Test with existing app    │
│ 3. Verify no conflicts       │
│ 4. Check memory usage        │
└──────────┬───────────────────┘
           │
           ▼
Phase 3: Backend
┌──────────────────────────────┐
│ 1. Create backend endpoint   │
│ 2. Create DB migration       │
│ 3. Test end-to-end           │
│ 4. Verify data persistence   │
└──────────┬───────────────────┘
           │
           ▼
Phase 4: Production
┌──────────────────────────────┐
│ 1. Deploy to staging         │
│ 2. Monitor performance       │
│ 3. Check payload sizes       │
│ 4. Deploy to production      │
└──────────────────────────────┘
```

---

## 9. Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Comprehensive Error Handling                  │
└─────────────────────────────────────────────────────────────────┘

┌────────────────────────────┐
│ captureLog(method, args)   │
└──────────┬─────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ try {                        │
│   serializeArgs()            │
│   buffer.push()              │
│ }                            │
└──────────┬─────────┬─────────┘
           │         │
        SUCCESS   FAILURE
           │         │
           ▼         ▼
      Continue  ┌─────────────────────┐
                │ catch (error) {     │
                │   SharedLogger.error│
                │   // SILENT FAIL    │
                │   // Do NOT throw   │
                │ }                   │
                └─────────────────────┘


┌────────────────────────────┐
│ flush()                    │
└──────────┬─────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ try {                        │
│   await APIClient.post()     │
│ }                            │
└──────────┬─────────┬─────────┘
           │         │
        SUCCESS   FAILURE
           │         │
           ▼         ▼
      Log OK    ┌─────────────────────┐
                │ catch (error) {     │
                │   if (attempt < 3)  │
                │     retry()         │
                │   else              │
                │     log & give up   │
                │ }                   │
                └─────────────────────┘


┌────────────────────────────┐
│ safeJSONStringify()        │
└──────────┬─────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ try {                        │
│   JSON.stringify(replacer)   │
│ }                            │
└──────────┬─────────┬─────────┘
           │         │
        SUCCESS   FAILURE
           │         │
           ▼         ▼
      Return    ┌─────────────────────┐
      JSON      │ catch {             │
                │   return String(val)│
                │ }                   │
                └─────────────────────┘
```

---

## 10. Configuration Options Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Runtime Configuration Priority                      │
└─────────────────────────────────────────────────────────────────┘

Priority 1: URL Parameters (Highest)
┌──────────────────────────────────┐
│ ?console_interceptor=false       │
│ ?console_interceptor_debug=true  │
└──────────┬───────────────────────┘
           │ If set, use this
           ▼
Priority 2: localStorage
┌──────────────────────────────────┐
│ CONSOLE_INTERCEPTOR_ENABLED=true │
│ CONSOLE_INTERCEPTOR_FLUSH=60000  │
└──────────┬───────────────────────┘
           │ If not URL param
           ▼
Priority 3: Config File
┌──────────────────────────────────┐
│ config.consoleInterceptor.enabled│
│ config.consoleInterceptor.flush  │
└──────────┬───────────────────────┘
           │ Default fallback
           ▼
Priority 4: DEFAULT_CONFIG
┌──────────────────────────────────┐
│ Hard-coded defaults              │
│ enabled: true                    │
│ flushInterval: 30000             │
└──────────────────────────────────┘
```

---

## Summary

This console interceptor architecture provides:

1. **Zero Conflicts**: Separate layers for app logging vs browser console capturing
2. **Memory Safety**: Buffer limits, truncation, circular reference handling
3. **Reliability**: Exponential backoff, silent failures, preserve console
4. **Performance**: Lazy serialization, smart batching, periodic flushing
5. **Flexibility**: Runtime configuration, enable/disable on-the-fly
6. **Maintainability**: Clean TypeScript, clear interfaces, testable components

**Next Steps**: Implement according to architecture in `/docs/CONSOLE_INTERCEPTOR_ARCHITECTURE.md`
