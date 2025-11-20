# WSL2 Development Guide

## File Watching Limitation

When developing on WSL2 with project files on Windows mount (`/mnt/g/`, `/mnt/c/`, etc.), file watching (HMR and auto-reload) **will not work** due to architectural limitations.

This is a known WSL2 limitation when files are on Windows filesystem (NTFS) accessed through the `/mnt/` mount points.

## Why This Happens

- WSL2 uses a virtualized Linux kernel
- Windows filesystem is mounted via 9P protocol
- File system events (inotify, fs.watch) don't cross the WSL2-Windows boundary reliably
- Both Vite's native HMR and polling-based watchers (chokidar) are affected

## Workarounds

### Option 1: Manual Server Restart (Recommended for WSL2)

When you make changes to code, manually restart the dev server:

```bash
# Press Ctrl+C to stop the server
# Then restart:
npm run dev
```

This is the most reliable approach when working on Windows mounts.

### Option 2: Move Project to WSL2 Native Filesystem

Move your project from `/mnt/g/` to WSL2's native filesystem (e.g., `~/projects/`):

```bash
# Move project to WSL2 home directory
mv /mnt/g/khoirul/signate/player-vite ~/player-vite
cd ~/player-vite

# Now HMR will work
npm run dev
```

**Pros:**
- ✅ HMR works perfectly
- ✅ File operations are faster

**Cons:**
- ❌ Files not easily accessible from Windows Explorer
- ❌ May need to sync files between Windows and WSL2

### Option 3: Develop on Windows (Not WSL)

Edit files using a Windows-based editor and run dev server from Windows:

```powershell
# In PowerShell or CMD (NOT WSL)
cd G:\khoirul\signate\player-vite
npm run dev
```

**Pros:**
- ✅ HMR works
- ✅ Files accessible in Windows

**Cons:**
- ❌ Loses Linux development environment benefits

### Option 4: Use VS Code Remote-WSL

If using VS Code, install the "Remote - WSL" extension:

1. Install "Remote - WSL" extension in VS Code
2. Open project in WSL mode: `code .` from WSL terminal
3. All file operations go through WSL, HMR might work better

## Current Setup

This project includes a watch script (`npm run dev:watch`) that attempts to use polling with chokidar, but **it will not work on `/mnt/` mounts**.

```bash
# This will NOT detect file changes on /mnt/g/
npm run dev:watch
```

## Recommended Workflow for WSL2 + Windows Mount

1. **Use manual restart** when developing:
   ```bash
   npm run dev
   # Make changes to code
   # Press Ctrl+C
   # Run again: npm run dev
   ```

2. **Or use a helper alias** in your `.bashrc`:
   ```bash
   # Add to ~/.bashrc
   alias restart='killall node; npm run dev'
   ```

   Then simply type:
   ```bash
   restart
   ```

## Alternative: Docker Development

Consider using Docker for a consistent development environment:

```bash
# Create docker-compose.yml for development
docker-compose up --build
```

This isolates the environment and file watching works within the container.

## References

- [WSL2 File Watcher Issue](https://github.com/microsoft/WSL/issues/4739)
- [Vite on WSL2](https://vitejs.dev/guide/troubleshooting.html#dev-server)
- [Node.js fs.watch on WSL2](https://github.com/nodejs/node/issues/45899)

## Summary

**For best experience on WSL2 with Windows mount:**
- Accept manual server restart as normal workflow
- Or move project to WSL2 native filesystem (`~/`)
- Or develop directly on Windows (not recommended for this project)

The project is fully functional - only hot reload is affected. All builds, tests, and production deployments work perfectly.
