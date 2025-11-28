#!/bin/bash
#
# Wait for CDC EPHT API to come back online and download radon data
#
# Usage: ./scripts/wait_and_download_cdc_epht.sh

echo "================================================================================"
echo "CDC EPHT API Availability Checker"
echo "================================================================================"
echo ""

# Check interval (seconds)
CHECK_INTERVAL=300  # 5 minutes

# Max attempts before giving up
MAX_ATTEMPTS=288  # 24 hours worth of 5-minute checks

# Load API key from .env
if [ -f .env ]; then
    export $(grep CDC_EPHT_API_KEY .env | xargs)
else
    echo "❌ Error: .env file not found"
    exit 1
fi

if [ -z "$CDC_EPHT_API_KEY" ]; then
    echo "❌ Error: CDC_EPHT_API_KEY not set in .env"
    exit 1
fi

echo "✅ API key loaded from .env"
echo ""

# Function to check if API is available
check_api() {
    local response=$(curl -s "https://ephtracking.cdc.gov/apigateway/api/v1/getCoreHolder/479/17/0?apiToken=$CDC_EPHT_API_KEY&measureId=479&stratificationLevelId=1&isSmoothed=false&year=2021")

    # Check if response contains error or is valid JSON array
    if echo "$response" | grep -q '"code": 400'; then
        return 1  # API still down
    elif echo "$response" | grep -q '\[' ; then
        return 0  # API returned array (data available)
    else
        return 1  # Unknown response
    fi
}

# Check if API is currently available
echo "Checking API status..."
if check_api; then
    echo "✅ API is online!"
else
    echo "⚠️  API is currently down for maintenance"
    echo ""
    echo "Will check every $CHECK_INTERVAL seconds ($(($CHECK_INTERVAL / 60)) minutes)"
    echo "Maximum wait time: $(($MAX_ATTEMPTS * $CHECK_INTERVAL / 3600)) hours"
    echo ""
    echo "Press Ctrl+C to cancel"
    echo ""

    attempt=1
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Attempt $attempt/$MAX_ATTEMPTS - Checking API..."

        if check_api; then
            echo ""
            echo "================================================================================"
            echo "✅ API IS BACK ONLINE!"
            echo "================================================================================"
            break
        fi

        if [ $attempt -lt $MAX_ATTEMPTS ]; then
            echo "   Still down. Waiting $(($CHECK_INTERVAL / 60)) minutes..."
            sleep $CHECK_INTERVAL
        fi

        attempt=$((attempt + 1))
    done

    if [ $attempt -gt $MAX_ATTEMPTS ]; then
        echo ""
        echo "❌ API did not come back online within $(($MAX_ATTEMPTS * $CHECK_INTERVAL / 3600)) hours"
        echo "   Please try again later or check https://ephtracking.cdc.gov/ for status"
        exit 1
    fi
fi

# API is online - download data
echo ""
echo "================================================================================"
echo "DOWNLOADING RADON DATA"
echo "================================================================================"
echo ""

# Download all years (2013-2022)
python scripts/03_download_source.py --source cdc_epht_radon --variable radon_testing --years 2013 2014 2015 2016 2017 2018 2019 2020 2021 2022

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "================================================================================"
    echo "✅ DOWNLOAD COMPLETE"
    echo "================================================================================"
    echo ""
    echo "Downloaded radon data for years 2013-2022"
    echo ""
    echo "Next steps:"
    echo "  1. Check data/cache/05_RADIATION/cdc_epht_radon/"
    echo "  2. Run: python scripts/04_process_cached_data.py"
    echo "  3. Run: python scripts/05_generate_maps.py --category 05_RADIATION"
else
    echo ""
    echo "❌ Download failed (exit code: $exit_code)"
    echo "   Check logs/main.log for details"
    exit $exit_code
fi
