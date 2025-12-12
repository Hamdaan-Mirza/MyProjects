# Google Maps Scraper - Automated Test Suite
# Run this after: docker-compose up -d

Write-Host "`n=== Google Maps Scraper Test Suite ===" -ForegroundColor Cyan
Write-Host "Starting tests at $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray

$test1Pass = $false
$test2Pass = $false
$test3Pass = $false
$test4Pass = $false

# Test 1: Basic scrape
Write-Host "[Test 1/4] Basic Search Query..." -ForegroundColor Yellow
$job1 = @{ 
    job = @{ 
        type = "google_maps"
        query = "coffee shops in seattle"
        limit = 5
    }
} | ConvertTo-Json -Depth 3

try {
    $taskResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/run-job/" -Method POST -ContentType "application/json" -Body $job1
    Write-Host "  Job submitted: $($taskResponse.task_id)" -ForegroundColor Gray
    Write-Host "  Waiting 30s for scrape to complete..." -ForegroundColor Gray
    Start-Sleep -Seconds 30

    $result = docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.listings.countDocuments({job_query: 'coffee shops in seattle'})" 2>$null
    $count = [int]($result -replace '[^0-9]','')

    if ($count -ge 5) {
        Write-Host "  [PASS] $count listings scraped`n" -ForegroundColor Green
        $test1Pass = $true
    } else {
        Write-Host "  [FAIL] Only $count listings scraped, expected at least 5`n" -ForegroundColor Red
        $test1Pass = $false
    }
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)`n" -ForegroundColor Red
    $test1Pass = $false
}

# Test 2: Deduplication
Write-Host "[Test 2/4] Duplicate Prevention..." -ForegroundColor Yellow
try {
    # Check for duplicate titles in the same job_query
    $dupCheck = docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.listings.aggregate([{`$match: {job_query: 'coffee shops in seattle'}}, {`$group: {_id: '`$title', count: {`$sum: 1}}}, {`$match: {count: {`$gt: 1}}}, {`$count: 'duplicates'}])" 2>$null
    
    if ($dupCheck -match '"duplicates"') {
        Write-Host "  [FAIL] Found duplicate titles in database`n" -ForegroundColor Red
        $test2Pass = $false
    } else {
        Write-Host "  [PASS] No duplicate titles found for same query`n" -ForegroundColor Green
        $test2Pass = $true
    }
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)`n" -ForegroundColor Red
    $test2Pass = $false
}

# Test 3: API Integration
Write-Host "[Test 3/4] API Endpoint..." -ForegroundColor Yellow
try {
    $apiResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/listings/"
    $apiCount = $apiResponse.Count
    
    if ($apiCount -gt 0) {
        Write-Host "  [PASS] API returned $apiCount results`n" -ForegroundColor Green
        $test3Pass = $true
    } else {
        Write-Host "  [WARN] API returned 0 results`n" -ForegroundColor Yellow
        $test3Pass = $false
    }
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)`n" -ForegroundColor Red
    $test3Pass = $false
}

# Test 4: Data Quality
Write-Host "[Test 4/4] Data Quality Check..." -ForegroundColor Yellow
try {
    $sample = docker-compose exec -T mongo mongosh scraper_db --quiet --eval "db.listings.findOne({source: 'google_maps'})" 2>$null
    
    if (($sample -match 'title') -and ($sample -match 'scraped_at') -and ($sample -match 'job_query')) {
        Write-Host "  [PASS] Data contains required fields`n" -ForegroundColor Green
        $test4Pass = $true
    } else {
        Write-Host "  [FAIL] Missing required fields in data`n" -ForegroundColor Red
        $test4Pass = $false
    }
} catch {
    Write-Host "  [FAIL] $($_.Exception.Message)`n" -ForegroundColor Red
    $test4Pass = $false
}

# Summary
Write-Host "=== Test Summary ===" -ForegroundColor Cyan
$passCount = @($test1Pass, $test2Pass, $test3Pass, $test4Pass) | Where-Object {$_} | Measure-Object | Select-Object -ExpandProperty Count
Write-Host "Passed: $passCount/4 tests" -ForegroundColor $(if ($passCount -eq 4) {"Green"} else {"Yellow"})

if ($passCount -eq 4) {
    Write-Host "`nAll tests passed! Google Maps scraper is working correctly.`n" -ForegroundColor Green
} else {
    Write-Host "`nSome tests failed. Check logs with: docker-compose logs worker celery`n" -ForegroundColor Yellow
}

Write-Host "Completed at $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
