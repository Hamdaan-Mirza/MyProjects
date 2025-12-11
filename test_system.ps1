# Automated Web Scraper - System Test Script
# Run this after `docker-compose up --build`

Write-Host "`n=== Testing Scraper Dashboard ===" -ForegroundColor Cyan

# Test 1: Check if services are running
Write-Host "`n[1/6] Checking Docker services..." -ForegroundColor Yellow
docker-compose ps

# Test 2: Test MongoDB connection
Write-Host "`n[2/6] Testing MongoDB connection..." -ForegroundColor Yellow
$mongoTest = docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.runCommand({ ping: 1 })"
if ($mongoTest -match "ok") {
    Write-Host "✓ MongoDB is running" -ForegroundColor Green
} else {
    Write-Host "✗ MongoDB connection failed" -ForegroundColor Red
}

# Test 3: Test Redis connection
Write-Host "`n[3/6] Testing Redis connection..." -ForegroundColor Yellow
$redisTest = docker-compose exec -T redis redis-cli ping
if ($redisTest -match "PONG") {
    Write-Host "✓ Redis is running" -ForegroundColor Green
} else {
    Write-Host "✗ Redis connection failed" -ForegroundColor Red
}

# Test 4: Test Backend API health
Write-Host "`n[4/6] Testing Backend API..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/listings/" -Method GET -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Backend API is responding (Status: $($response.StatusCode))" -ForegroundColor Green
        Write-Host "  Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Backend API failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 5: Submit a test job
Write-Host "`n[5/6] Submitting test scraping job..." -ForegroundColor Yellow
$jobPayload = @{
    job = @{
        url = "https://example.com"
        selectors = @{
            item = "div"
            title = "h1"
            link = "a"
        }
    }
} | ConvertTo-Json -Depth 3

try {
    $jobResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" `
        -Method POST `
        -ContentType "application/json" `
        -Body $jobPayload
    
    Write-Host "✓ Job submitted successfully" -ForegroundColor Green
    Write-Host "  Task ID: $($jobResponse.task_id)" -ForegroundColor Gray
    Write-Host "  Status: $($jobResponse.status)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Job submission failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 6: Check if worker is processing
Write-Host "`n[6/6] Checking worker logs (last 10 lines)..." -ForegroundColor Yellow
docker-compose logs --tail=10 worker

# Test 7: Check jobs in MongoDB
Write-Host "`n[BONUS] Checking jobs in MongoDB..." -ForegroundColor Yellow
docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.jobs.find().limit(5).pretty()"

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor White
Write-Host "  1. Visit http://localhost:3000 to see the frontend dashboard" -ForegroundColor White
Write-Host "  2. Check worker logs: docker-compose logs -f worker" -ForegroundColor White
Write-Host "  3. Check backend logs: docker-compose logs -f backend" -ForegroundColor White
Write-Host "  4. View all jobs: docker-compose exec mongo mongosh scraper_db --eval 'db.jobs.find()'" -ForegroundColor White
