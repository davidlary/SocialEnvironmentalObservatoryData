#!/bin/bash
################################################################################
# Autonomous Download and Processing Pipeline
#
# This script runs fully autonomously:
# 1. Waits for EPA AQS download to complete
# 2. Processes EPA data to TSVs
# 3. Generates EPA maps
# 4. Downloads all IPUMS NHGIS batches (266 datasets)
# 5. Processes IPUMS data when complete
#
# Can run for HOURS/DAYS without intervention
################################################################################

set -e  # Exit on error

LOGFILE="logs/autonomous_pipeline_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOGFILE"
}

log "================================================================================"
log "AUTONOMOUS PIPELINE STARTED"
log "================================================================================"

################################################################################
# PHASE 1: Wait for EPA AQS Download
################################################################################

log "PHASE 1: Monitoring EPA AQS download..."

# Monitor the background process
EPA_PID=47549
while kill -0 $EPA_PID 2>/dev/null; do
    # Count files every 30 seconds
    COUNT=$(find data/cache/01_AIR_ATMOSPHERE/epa_aqs -name "*.csv" | wc -l | xargs)
    log "  EPA AQS: $COUNT/243 files downloaded..."
    sleep 30
done

log "✅ EPA AQS download complete!"

# Verify completion
FINAL_COUNT=$(find data/cache/01_AIR_ATMOSPHERE/epa_aqs -name "*.csv" | wc -l | xargs)
log "Final count: $FINAL_COUNT files"

################################################################################
# PHASE 2: Process EPA AQS Data
################################################################################

log ""
log "PHASE 2: Processing EPA AQS data to TSV files..."

if python scripts/04_process_cached_data.py --source epa_aqs >> "$LOGFILE" 2>&1; then
    TSV_COUNT=$(find data/processed/01_AIR_ATMOSPHERE -name "*.tsv" | wc -l | xargs)
    log "✅ EPA AQS processing complete: $TSV_COUNT TSV files generated"
else
    log "❌ EPA AQS processing failed - check $LOGFILE"
fi

################################################################################
# PHASE 3: Generate EPA AQS Maps
################################################################################

log ""
log "PHASE 3: Generating EPA AQS maps..."

if python scripts/05_generate_maps.py --all >> "$LOGFILE" 2>&1; then
    MAP_COUNT=$(find data/processed/01_AIR_ATMOSPHERE -name "*.png" | wc -l | xargs)
    log "✅ EPA AQS map generation complete: $MAP_COUNT maps generated"
else
    log "❌ EPA AQS map generation failed - check $LOGFILE"
fi

################################################################################
# PHASE 4: Download All IPUMS NHGIS Batches
################################################################################

log ""
log "PHASE 4: Starting IPUMS NHGIS downloads (ALL 266 datasets)..."
log "WARNING: This will take MANY HOURS due to extract preparation times"

for BATCH in 1 2 3 4 5; do
    log ""
    log "------------------------------------------------------------"
    log "Starting IPUMS NHGIS Batch $BATCH..."
    log "------------------------------------------------------------"

    if python scripts/03b_download_nhgis_batch.py --batch $BATCH >> "$LOGFILE" 2>&1; then
        log "✅ Batch $BATCH complete"
    else
        log "⚠️  Batch $BATCH had some failures - check $LOGFILE"
    fi

    # Small delay between batches
    sleep 10
done

log ""
log "✅ All IPUMS NHGIS batches submitted"

# Count downloaded files
NHGIS_COUNT=$(find data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis -name "*.zip" 2>/dev/null | wc -l | xargs)
log "IPUMS NHGIS extracts downloaded: $NHGIS_COUNT"

################################################################################
# PHASE 5: Process IPUMS NHGIS Data (if processor exists)
################################################################################

log ""
log "PHASE 5: Processing IPUMS NHGIS data..."

if [ -f "scripts/04_process_cached_data.py" ]; then
    if python scripts/04_process_cached_data.py --source ipums_nhgis >> "$LOGFILE" 2>&1; then
        log "✅ IPUMS NHGIS processing complete"
    else
        log "⚠️  IPUMS NHGIS processing not yet implemented or failed"
    fi
else
    log "⚠️  IPUMS processor not yet implemented - data cached for future processing"
fi

################################################################################
# COMPLETION SUMMARY
################################################################################

log ""
log "================================================================================"
log "AUTONOMOUS PIPELINE COMPLETE"
log "================================================================================"
log ""
log "SUMMARY:"
log "  EPA AQS:"
log "    - Downloaded: $FINAL_COUNT CSV files"
log "    - TSV files: $TSV_COUNT"
log "    - Maps: $MAP_COUNT"
log ""
log "  IPUMS NHGIS:"
log "    - Extracts: $NHGIS_COUNT/266 datasets"
log ""
log "All logs saved to: $LOGFILE"
log "================================================================================"
