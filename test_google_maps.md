# Google Maps Scraper - Test Cases

## Test Case 1: Basic Search Query

**Objective:** Test scraping a simple search query

### Setup:
```powershell
# Clear existing data
docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.deleteMany({'source': 'google_maps'})"
```

### Test:
```powershell
# Submit job for "coffee shops in seattle"
$job = @{
    job = @{
        type = "google_maps"
        query = "coffee shops in seattle"
        limit = 10
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job
```

### Wait and Verify:
```powershell
# Wait 30 seconds
Start-Sleep -Seconds 30

# Check results
docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.find({'source': 'google_maps'}).limit(5).pretty()"
```

### Expected Results:
- ✅ 10 listings scraped
- ✅ Each has `title` (business name)
- ✅ Each has `job_query: "coffee shops in seattle"`
- ✅ Each has `source: "google_maps"`
- ✅ `scraped_at` timestamp present

---

## Test Case 2: Specific Location with Category

**Objective:** Test location-specific search

### Test:
```powershell
$job = @{
    job = @{
        type = "google_maps"
        query = "restaurants in New York, NY"
        limit = 15
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job
```

### Verify:
```powershell
Start-Sleep -Seconds 40
docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({'source': 'google_maps', 'job_query': 'restaurants in New York, NY'})"
```

### Expected Results:
- ✅ 15 listings scraped
- ✅ All have location-relevant names

---

## Test Case 3: Large Dataset (Scrolling Test)

**Objective:** Test scrolling mechanism works correctly

### Test:
```powershell
$job = @{
    job = @{
        type = "google_maps"
        query = "hotels in las vegas"
        limit = 30
    }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job
```

### Monitor:
```powershell
# Watch worker logs in real-time
docker-compose logs -f worker
```

### Expected Results:
- ✅ Logs show "Scraped 10/30... Scraped 20/30... Scraped 30/30..."
- ✅ All 30 listings collected
- ✅ No infinite loop (job completes)

---

## Test Case 4: Duplicate Prevention

**Objective:** Verify deduplication works

### Test:
```powershell
# Run same query twice
$job = @{
    job = @{
        type = "google_maps"
        query = "pizza near times square"
        limit = 5
    }
} | ConvertTo-Json -Depth 3

# First run
Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job
Start-Sleep -Seconds 30

# Count results
docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({'job_query': 'pizza near times square'})"
```

Then run the same job again and verify count doesn't increase.

### Expected Results:
- ✅ Count stays the same (no duplicates created)
- ✅ `first_seen` timestamp unchanged on re-scrape
- ✅ `scraped_at` timestamp updated

---

## Test Case 5: API Endpoint Integration

**Objective:** Verify API returns Google Maps data correctly

### Test:
```powershell
# After running any scrape job above
curl "http://localhost:8000/api/listings/?source=google_maps"
```

### Expected Results:
```json
[
  {
    "id": "...",
    "title": "Starbucks",
    "url": "https://www.google.com/maps/search/...",
    "price": null,
    "first_seen": "2025-12-11T..."
  }
]
```

---

## Quick Automated Test Suite

```powershell
# test_google_maps.ps1
Write-Host "=== Google Maps Scraper Test Suite ===" -ForegroundColor Cyan

# Test 1: Basic scrape
Write-Host "`nTest 1: Basic Search..." -ForegroundColor Yellow
$job1 = @{ job = @{ type = "google_maps"; query = "coffee shops in seattle"; total = 5 }} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job1
Write-Host "Waiting 30s for scrape to complete..." -ForegroundColor Gray
Start-Sleep -Seconds 30

$result = docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({'job_query': 'coffee shops in seattle'})"
$count = [int]($result -replace '[^0-9]','')

if ($count -ge 5) {
    Write-Host "✓ Test 1 PASSED: $count listings scraped" -ForegroundColor Green
} else {
    Write-Host "✗ Test 1 FAILED: Only $count listings scraped" -ForegroundColor Red
}

# Test 2: Deduplication
Write-Host "`nTest 2: Deduplication..." -ForegroundColor Yellow
Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job1
Write-Host "Waiting 30s..." -ForegroundColor Gray
Start-Sleep -Seconds 30

$result2 = docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({'job_query': 'coffee shops in seattle'})"
$count2 = [int]($result2 -replace '[^0-9]','')

if ($count2 -eq $count) {
    Write-Host "✓ Test 2 PASSED: No duplicates ($count2 = $count)" -ForegroundColor Green
} else {
    Write-Host "✗ Test 2 FAILED: Count changed ($count2 vs $count)" -ForegroundColor Red
}

# Test 3: API endpoint
Write-Host "`nTest 3: API Integration..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/listings/"
    if ($response.Count -gt 0) {
        Write-Host "✓ Test 3 PASSED: API returning $($response.Count) results" -ForegroundColor Green
    } else {
        Write-Host "⚠ Test 3 WARNING: API returned 0 results" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Test 3 FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 4: Check data quality
Write-Host "`nTest 4: Data Quality..." -ForegroundColor Yellow
$sample = docker-compose exec mongo mongosh scraper_db --quiet --eval "db.listings.findOne({'source': 'google_maps'})"
if ($sample -match "title" -and $sample -match "scraped_at") {
    Write-Host "✓ Test 4 PASSED: Data has required fields" -ForegroundColor Green
} else {
    Write-Host "✗ Test 4 FAILED: Missing required fields" -ForegroundColor Red
}

Write-Host "`n=== Test Suite Complete ===" -ForegroundColor Cyan
```

---

## How to Run Tests

### Run individual test:
Copy any test case command and paste in PowerShell

### Run full suite:
```powershell
cd scraper-dashboard
.\test_google_maps.ps1
```

### Debug failed tests:
```powershell
# Check worker logs
docker-compose logs worker --tail=50

# Check celery logs
docker-compose logs celery --tail=20

# Check job status
docker-compose exec mongo mongosh scraper_db --quiet --eval "db.jobs.find().sort({created_at:-1}).limit(3).pretty()"
```

---

## Performance Benchmarks

| Test Case | Expected Time | Max Acceptable |
|-----------|--------------|----------------|
| 5 listings | 15-20s | 30s |
| 10 listings | 20-30s | 45s |
| 20 listings | 30-45s | 60s |
| 30+ listings | 45-60s | 90s |

If tests exceed max acceptable time, check:
- Network latency
- Docker resource limits
- Google Maps rate limiting
