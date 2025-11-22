#!/bin/bash
################################################################################
# Autonomous IPUMS NHGIS Downloader
#
# Downloads all 266 IPUMS NHGIS datasets in batches with automatic retry/debug
################################################################################

set -e

LOG="logs/ipums_autonomous_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

log "================================================================================"
log "AUTONOMOUS IPUMS NHGIS DOWNLOADER"
log "================================================================================"

# Download all 5 batches
for BATCH in 1 2 3 4 5; do
    log ""
    log "--------------------------------------------------------------------"
    log "BATCH $BATCH: Starting..."
    log "--------------------------------------------------------------------"

    BATCH_LOG="logs/nhgis_batch${BATCH}_$(date +%Y%m%d_%H%M%S).log"

    if python scripts/03b_download_nhgis_batch.py --batch $BATCH >> "$BATCH_LOG" 2>&1; then
        SUCCESS=$(grep "✅" "$BATCH_LOG" | wc -l | xargs)
        FAILED=$(grep "❌" "$BATCH_LOG" | wc -l | xargs)
        log "Batch $BATCH: $SUCCESS succeeded, $FAILED failed"
    else
        log "⚠️  Batch $BATCH had errors - check $BATCH_LOG"
    fi

    # Small delay between batches
    sleep 5
done

# Count results
TOTAL=$(find data/cache/02_DEMOGRAPHICS_SOCIAL/ipums_nhgis -name "*.zip" 2>/dev/null | wc -l | xargs)

log ""
log "================================================================================"
log "IPUMS NHGIS DOWNLOAD COMPLETE"
log "Total extracts downloaded: $TOTAL/266"
log "================================================================================"
