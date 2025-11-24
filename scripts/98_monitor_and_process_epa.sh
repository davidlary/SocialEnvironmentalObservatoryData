#!/bin/bash
################################################################################
# EPA AQS Monitor and Auto-Process
#
# Waits for EPA download to complete, then automatically processes and maps
################################################################################

set -e

LOG="logs/epa_autoprocess_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

log "======================================================================"
log "EPA AQS AUTO-PROCESS MONITOR"
log "======================================================================"

# Monitor EPA download
EPA_PID=47549
log "Monitoring EPA AQS download (PID: $EPA_PID)..."

while kill -0 $EPA_PID 2>/dev/null; do
    COUNT=$(find data/cache/01_AIR_ATMOSPHERE/epa_aqs -name "*.csv" 2>/dev/null | wc -l | xargs)
    log "EPA AQS: $COUNT files..."
    sleep 30
done

FINAL=$(find data/cache/01_AIR_ATMOSPHERE/epa_aqs -name "*.csv" 2>/dev/null | wc -l | xargs)
log "✅ EPA AQS download complete: $FINAL files"

# Process to TSVs
log "Processing EPA AQS to TSV files..."
if python scripts/04_process_cached_data.py --source epa_aqs >> "$LOG" 2>&1; then
    TSV=$(find data/processed/01_AIR_ATMOSPHERE -name "*.tsv" 2>/dev/null | wc -l | xargs)
    log "✅ TSV processing complete: $TSV files"
else
    log "❌ TSV processing failed"
    exit 1
fi

# Generate maps
log "Generating maps..."
if python scripts/05_generate_maps.py --all >> "$LOG" 2>&1; then
    MAPS=$(find data/processed/01_AIR_ATMOSPHERE -name "*.png" 2>/dev/null | wc -l | xargs)
    log "✅ Map generation complete: $MAPS maps"
else
    log "❌ Map generation failed"
    exit 1
fi

log "======================================================================"
log "✅ EPA AQS PIPELINE COMPLETE"
log "Files: $FINAL | TSVs: $TSV | Maps: $MAPS"
log "======================================================================"
