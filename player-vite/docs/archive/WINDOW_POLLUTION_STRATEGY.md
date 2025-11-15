# Window Pollution Refactor Strategy

## 🎯 PROBLEM

84 references to `window.*` objects throughout codebase:
- 21 assignments (exports)
- 63 usages (consumers)
- Heavy conditional checks `if (window.PlayerHLS)`

## ⚠️ RISK ANALYSIS

**HIGH RISK** areas:
1. **Conditional checks** - `if (window.PlayerHLS)` used for lazy initialization
2. **Cross-module communication** - Shell calling Player services
3. **Dynamic loading** - Services initialized at different times
4. **WebOS compatibility** - Some window.* might be needed for WebOS IPK

## 🔧 REFACTOR OPTIONS

### Option 1: Keep Window + Add ES6 (SAFE) ⭐ RECOMMENDED
**Effort:** 1 hour
**Risk:** Low
**Impact:** +3 points (88/100)

```typescript
// Keep window assignment for backward compat
export const PlayerHLS = new PlayerHLSClass();
window.PlayerHLS = PlayerHLS; // @deprecated - use import instead

// New code uses imports
import { PlayerHLS } from '@player/services';
```

**Pros:**
- ✅ Zero breaking changes
- ✅ Gradual migration
- ✅ Easy rollback

**Cons:**
- ⚠️ Still has window pollution
- ⚠️ Grade hanya naik +3

---

### Option 2: Service Locator Pattern (MEDIUM)
**Effort:** 3-4 hours
**Risk:** Medium
**Impact:** +5 points (95/100)

```typescript
// Create service registry
class ServiceRegistry {
  private services = new Map();

  register<T>(name: string, service: T) {
    this.services.set(name, service);
  }

  get<T>(name: string): T {
    return this.services.get(name);
  }
}

export const services = new ServiceRegistry();

// Usage
services.register('PlayerHLS', PlayerHLS);
const hls = services.get<PlayerHLSClass>('PlayerHLS');
```

**Pros:**
- ✅ Centralized service management
- ✅ Type-safe with generics
- ✅ Easy testing

**Cons:**
- ⚠️ Need to update 84 references
- ⚠️ 3-4 hours effort
- ⚠️ Potential runtime errors if service not registered

---

### Option 3: Full Dependency Injection (HIGH RISK)
**Effort:** 8-12 hours
**Risk:** High
**Impact:** +6 points (96/100)

Complete DI system with constructor injection.

**Pros:**
- ✅ Perfect architecture
- ✅ Easy testing
- ✅ No globals

**Cons:**
- ❌ Major refactor (all services)
- ❌ High risk of breaking
- ❌ 8-12 hours

---

## 📊 RECOMMENDATION

### **Go with Option 1: Hybrid Approach**

**Phase 1** (NOW - 1 hour):
1. Keep all `window.*` assignments
2. Add `@deprecated` JSDoc comments
3. Update critical paths to use ES6 imports
4. Add type-safe imports to main.ts

**Phase 2** (FUTURE - when time permits):
5. Create ServiceRegistry
6. Gradually migrate window.* → services.get()
7. Remove window assignments

**Benefits:**
- ✅ Safe migration path
- ✅ No breaking changes today
- ✅ Foundation for future improvement
- ✅ Grade improvement: B+ → A- → A

## 🎯 ACTION PLAN (Phase 1)

1. **Add deprecation comments** (10 min)
2. **Create centralized import file** (10 min)
3. **Update main.ts initialization** (20 min)
4. **Update critical consumers** (20 min)
5. **Test & verify** (10 min)

**Total:** ~1 hour
**Grade improvement:** 90 → 93 (A-)

---

**Decision needed:** Which option do you want?
- [ ] Option 1: Hybrid (Safe, 1 hour, +3 points) ⭐ RECOMMENDED
- [ ] Option 2: Service Locator (Medium, 4 hours, +5 points)
- [ ] Option 3: Full DI (High risk, 12 hours, +6 points)
