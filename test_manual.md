# Manual Testing Guide

## Prerequisites
1. Ensure Docker Desktop is running
2. Have `.env` file configured (copy from `.env.example`)
3. Services are running: `docker-compose up --build`

---

## Test 1: Verify All Services Are Running

```powershell
docker-compose ps
```

**Expected output:** All 5 services should show "Up" status:
- `mongo`
- `redis`
- `backend`
- `worker`
- `frontend`

---

## Test 2: Test Backend API Directly

### Get empty listings (initially empty)
```powershell
curl http://localhost:8000/api/listings/
```
**Expected:** `[]` or `[{...}]` (JSON array)

### Submit a test job
```powershell
curl -X POST http://localhost:8000/api/run-job/ `
  -H "Content-Type: application/json" `
  -d '{\"job\": {\"url\": \"https://example.com\", \"selectors\": {\"item\": \"div\", \"title\": \"h1\", \"link\": \"a\"}}}'
```
**Expected:** 
```json
{"status": "scheduled", "task_id": "some-uuid"}
```

---

## Test 3: Verify Job Was Created in MongoDB

```powershell
docker-compose exec mongo mongosh scraper_db --eval "db.jobs.find().pretty()"
```

**Expected:** Should show job document with:
- `status: "pending"` or `"running"` or `"completed"`
- `created_at` timestamp
- `job` object with your URL and selectors

---

## Test 4: Check Worker Is Processing Jobs

```powershell
# Watch worker logs in real-time
docker-compose logs -f worker
```

**Expected output:**
```
Worker started. Polling every 10s for jobs...
Processing job <id>: {'url': 'https://example.com', ...}
Job <id> completed successfully
```

Press `Ctrl+C` to stop watching logs.

---

## Test 5: Verify Frontend Is Accessible

Open browser: **http://localhost:3000**

**Expected:**
- Page loads with title "Scraped Listings"
- Table showing any scraped items (may be empty initially)
- No console errors (press F12 to check)

---

## Test 6: Check Individual Container Logs

### Backend logs
```powershell
docker-compose logs backend
```
Look for Django startup messages and no errors.

### Worker logs
```powershell
docker-compose logs worker
```
Look for "Worker started" and job processing messages.

### Frontend logs
```powershell
docker-compose logs frontend
```
Look for Vite dev server running on port 3000.

---

## Test 7: Test Complete End-to-End Flow

### Step 1: Clear existing data (optional)
```powershell
docker-compose exec mongo mongosh scraper_db --eval "db.jobs.deleteMany({})"
docker-compose exec mongo mongosh scraper_db --eval "db.listings.deleteMany({})"
```

### Step 2: Submit a real scraping job
```powershell
$job = @{
    job = @{
        url = "https://quotes.toscrape.com/"
        selectors = @{
            item = ".quote"
            title = ".text"
            link = "a"
        }
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $job
```

### Step 3: Wait and monitor
```powershell
# Watch worker process it (wait ~10-30 seconds)
docker-compose logs -f worker
```

### Step 4: Check results in MongoDB
```powershell
docker-compose exec mongo mongosh scraper_db --eval "db.listings.find().limit(5).pretty()"
```

### Step 5: Check API returns results
```powershell
curl http://localhost:8000/api/listings/
```

### Step 6: Refresh frontend
Visit http://localhost:3000 and see the scraped quotes!

---

## Troubleshooting

### Backend won't start
```powershell
# Check logs
docker-compose logs backend

# Common fix: rebuild
docker-compose down
docker-compose up --build backend
```

### Worker not processing
```powershell
# Check if Playwright installed
docker-compose exec worker playwright --version

# Check MongoDB connection from worker
docker-compose exec worker python -c "from pymongo import MongoClient; print(MongoClient('mongodb://mongo:27017').server_info())"

# Restart worker
docker-compose restart worker
```

### Frontend can't reach backend
```powershell
# Check if backend is listening
curl http://localhost:8000/api/listings/

# Check Vite proxy in vite.config.js
# Ensure target is 'http://backend:8000'
```

### Jobs stuck in "pending"
```powershell
# Check worker is running
docker-compose ps worker

# Check worker logs for errors
docker-compose logs worker

# Manually check a job
docker-compose exec mongo mongosh scraper_db --eval "db.jobs.findOne()"
```

### Playwright browser errors
```powershell
# Reinstall browsers in worker container
docker-compose exec worker playwright install chromium --with-deps

# Or rebuild worker
docker-compose up --build worker
```

---

## Quick Health Check Command

Run all checks at once:
```powershell
.\test_system.ps1
```

Or manually:
```powershell
Write-Host "Services:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`nBackend:" -ForegroundColor Cyan
curl -s http://localhost:8000/api/listings/ | ConvertFrom-Json

Write-Host "`nJobs:" -ForegroundColor Cyan
docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.jobs.countDocuments({})"

Write-Host "`nListings:" -ForegroundColor Cyan
docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({})"
```

---

## Success Indicators ✓

Your system is working correctly if:

1. ✓ All 5 Docker containers show "Up" status
2. ✓ `curl http://localhost:8000/api/listings/` returns JSON
3. ✓ POST to `/api/run-job/` returns `{"status": "scheduled"}`
4. ✓ Worker logs show "Processing job" messages
5. ✓ MongoDB contains job documents in `jobs` collection
6. ✓ Frontend loads at http://localhost:3000
7. ✓ After job completes, listings appear in MongoDB and frontend
