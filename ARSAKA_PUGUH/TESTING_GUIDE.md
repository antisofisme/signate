# 🧪 ARSAKA_PUGUH Phase A+ - Testing Guide

**Status**: ✅ Test data ready, API working
**Frontend URL**: http://31.97.111.175:3000/
**Backend API**: http://31.97.111.175:25536/api/

---

## 📋 Test Data Summary

Database sudah diisi dengan **5 sample decisions** dan **2 workflows**:

| Decision Type | Amount | Status | Requestor |
|---------------|--------|--------|-----------|
| Purchase Request | $1,500 | **Pending Approval** | John Doe |
| Capital Expenditure | $75,000 | **Pending Approval** | IT Department |
| Vendor Contract | $25,000 | **Allowed** | Jane Smith |
| Purchase Request | $299 | **Allowed** | HR Team |
| Budget Allocation | $50,000 | **Denied** | Mike Johnson |

---

## 🎯 Manual Testing Checklist

### Step 1: Open Frontend

1. Buka browser
2. Go to: **http://31.97.111.175:3000/**
3. ✅ Verify: Page loads without errors
4. ✅ Verify: Navigation menu shows (Decisions, Approvals, Audit)

### Step 2: Test Decision List

1. Click **"Decisions"** di navigation
2. ✅ Verify: Table shows **5 decisions**
3. ✅ Verify: Kolom visible:
   - Decision ID
   - Type
   - Outcome (colored badges)
   - Created At
4. ✅ Verify: Outcome badges colored correctly:
   - 🟡 **Yellow** = Pending Approval (2 items)
   - 🟢 **Green** = Allowed (2 items)
   - 🔴 **Red** = Denied (1 item)
5. ✅ Verify: Data sorted by newest first
6. ✅ Verify: Can click row to see detail

### Step 3: Test Decision Detail

1. Click on **first decision** (Office Supplies - $1,500)
2. ✅ Verify: Detail page loads
3. ✅ Verify: Shows:
   - Decision ID
   - Type: `purchase_request`
   - Outcome: **Requires Approval**
   - Context: Office Supplies, $1,500, John Doe
   - Metadata: Budget code, urgency
4. ✅ Verify: "Back to List" button works
5. Test another decision:
   - Click **"Budget Allocation"** (Denied)
   - ✅ Verify: Shows denied status
   - ✅ Verify: Context shows Marketing, $50,000

### Step 4: Test Approval Inbox

1. Click **"Approvals"** di navigation
2. ✅ Verify: Shows **2 pending workflows**:
   - Finance Manager → Office Supplies ($1,500)
   - CFO → Server Infrastructure ($75,000)
3. ✅ Verify: Kolom visible:
   - Workflow ID
   - Decision Type
   - Approver Role
   - Current State
   - Created At
4. ✅ Verify: All workflows show "Pending Approval" state
5. ✅ Verify: Decision context visible (item, amount, requestor)

### Step 5: Test Audit Trail

1. Click **"Audit"** di navigation
2. ⚠️ Expected: May show empty or "Not Found" (audit endpoint belum implemented)
3. ✅ Verify: Page doesn't crash
4. ✅ Verify: Navigation still works

### Step 6: Test Sorting & Filtering

**Decision List**:
1. ✅ Verify: Click column headers to sort
2. ✅ Verify: Data re-sorts correctly

**Approval Inbox**:
1. ✅ Verify: Workflows sorted by created_at descending
2. ✅ Verify: Only pending approvals shown

### Step 7: Test Responsive UI

1. ✅ Verify: Resize browser window
2. ✅ Verify: Table scrolls horizontally on small screens
3. ✅ Verify: Navigation menu stays visible

---

## 🔧 API Testing (Optional - via curl)

### Test 1: Get All Decisions
```bash
curl "http://31.97.111.175:25536/api/decisions?tenant_id=550e8400-e29b-41d4-a716-446655440000" | jq
```
**Expected**: JSON with 5 decisions

### Test 2: Get Pending Workflows
```bash
curl "http://31.97.111.175:25536/api/workflows?tenant_id=550e8400-e29b-41d4-a716-446655440000&state=PENDING_APPROVAL" | jq
```
**Expected**: JSON with 2 workflows

### Test 3: Get Decision Detail
```bash
curl "http://31.97.111.175:25536/api/decisions/650e8400-e29b-41d4-a716-446655440001?tenant_id=550e8400-e29b-41d4-a716-446655440000" | jq
```
**Expected**: Detailed JSON for Office Supplies decision

---

## ✅ Success Criteria

Phase A+ testing passes if:

- ✅ **Frontend accessible** at http://31.97.111.175:3000/
- ✅ **Decision List** shows 5 decisions with correct data
- ✅ **Decision Detail** shows full context and metadata
- ✅ **Approval Inbox** shows 2 pending workflows
- ✅ **Navigation** works between all pages
- ✅ **Sorting** works on tables
- ✅ **No console errors** in browser DevTools
- ✅ **No 404 errors** on API calls (check Network tab)

---

## 🐛 Troubleshooting

### Issue: Empty tables

**Check**:
```bash
# SSH to VPS
ssh root@31.97.111.175

# Check database
docker exec postgresql-1f85ac2c-3200-7c4a-6af6-c8802fa6b6e2 psql -U atlas_user -d arsaka_puguh -c "SELECT COUNT(*) FROM decisions;"
```

**Solution**: Re-run insert script:
```bash
docker exec -i postgresql-1f85ac2c-3200-7c4a-6af6-c8802fa6b6e2 psql -U atlas_user -d arsaka_puguh < /tmp/insert_test_data_correct.sql
```

### Issue: 404 errors in browser console

**Check**:
1. Open DevTools → Network tab
2. Look for failed API calls
3. Verify URL includes `/api` prefix

**Solution**: Already fixed - frontend uses `http://31.97.111.175:25536/api`

### Issue: CORS errors

**Check**: Backend CORS configuration includes frontend URL

**Solution**: Already configured - CORS allows `http://31.97.111.175:3000`

---

## 📊 Test Results Template

Copy this and fill in as you test:

```
ARSAKA_PUGUH Phase A+ - Test Results
Date: ___________
Tester: ___________

[ ] Frontend loads at http://31.97.111.175:3000/
[ ] Decision List shows 5 decisions
[ ] Decision Detail works
[ ] Approval Inbox shows 2 workflows
[ ] Audit Trail page loads
[ ] Sorting works
[ ] No console errors
[ ] No API 404 errors

Notes:
_________________________________
_________________________________
_________________________________

Overall Status: PASS / FAIL
```

---

## 🎉 Next Steps After Testing

If all tests pass:
1. ✅ Phase A+ deployment **complete**
2. ✅ Visibility layer **working**
3. 🚀 Ready for Phase B (Write Operations)

If tests fail:
1. Check browser console for errors
2. Check Network tab for failed requests
3. Verify backend is running: `curl http://31.97.111.175:25536/api/decisions?tenant_id=550e8400-e29b-41d4-a716-446655440000`
4. Contact support with error screenshots

---

**Testing completed!** 🎯
