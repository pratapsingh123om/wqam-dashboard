# Debug Guide for PDF Download and Plots

## Current Issues:
1. PDF download returns 404
2. Plots/graphs not showing

## Debug Steps:

### 1. Check Browser Console (F12)
After uploading a PDF, check the console for:
- `[DEBUG] Latest report:` - Should show timeseries count
- `[DEBUG] Rendering chart X for Y:` - Should show chart data
- Any errors related to charts or PDF download

### 2. Check Backend Logs
```powershell
docker-compose logs backend --tail 50
```

Look for:
- `[DEBUG] Report created with ID:` - Confirms report was created
- `[DEBUG] Report has X timeseries entries` - Confirms timeseries data
- `[DEBUG] PDF request - REPORT_HISTORY length:` - Shows if reports are available

### 3. Test PDF Endpoint Directly
After uploading a file, the report should be in REPORT_HISTORY. The PDF endpoint checks:
- If REPORT_HISTORY is empty → 404
- If first report is None → 404

### 4. Check Plots Data
The plots need:
- `latestReport.timeseries` to exist
- Each series to have `points` array
- Each point to have `timestamp` and `value`

## Common Issues:

### Issue 1: REPORT_HISTORY is empty
**Cause:** Backend restarted, losing in-memory data
**Solution:** Upload the file again after backend restart

### Issue 2: Timeseries is empty
**Cause:** No parameters matched in the uploaded file
**Solution:** Check if the PDF has recognizable parameter columns (pH, DO, BOD, COD, TDS, etc.)

### Issue 3: Points array is empty
**Cause:** All values were NaN or invalid
**Solution:** Check the uploaded file has numeric data

## Next Steps:
1. Upload a PDF file
2. Check browser console (F12) for debug messages
3. Check backend logs for debug output
4. Share the console output and logs if issues persist

