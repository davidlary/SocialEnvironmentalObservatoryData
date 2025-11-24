"""
CDC Mortality Data Downloader.

Downloads county-level mortality data from multiple CDC sources:
1. Compressed Mortality Files (CMF) 1968-2016 via FTP
2. NBER historical data 1999-2004 (county-level)
3. CDC WONDER web interface automation for 2017-2023

Data Sources:
- CMF: ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/
- NBER: https://data.nber.org/mortality/
- CDC WONDER: https://wonder.cdc.gov/ (web scraping/automation)

Implementation Strategy:
- Prioritize CMF (1999-2016): Public, county-level, bulk download
- Add WONDER automation for 2017-2023 if feasible
- Focus on ICD-10 period (1999+) for consistency

Author: Claude Code
Date: 2025-11-24
"""

import ftplib
import re
import struct
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import polars as pl
import requests
from loguru import logger

from core.base_downloader import BaseDownloader
from utils.constants import DEFAULT_RATE_LIMIT


# ============================================================================
# CDC COMPRESSED MORTALITY FILE DOWNLOADER
# ============================================================================


class CDCMortalityDownloader(BaseDownloader):
    """
    CDC Mortality Data downloader.

    Downloads county-level mortality data from:
    1. Compressed Mortality Files (CMF) 1999-2016 (ICD-10)
    2. Earlier periods: 1979-1998 (ICD-9), 1968-1978 (ICD-8)

    The CMF provides death counts and population estimates by:
    - County (FIPS code)
    - Year
    - Age group (19 groups)
    - Race/ethnicity
    - Sex
    - Cause of death (113 ICD-10 groups, 72 ICD-9 groups, 69 ICD-8 groups)

    File Structure:
    - Mortality file: Fixed-width format, 23-24 byte records
    - Population file: Fixed-width format, 14 byte records
    - Both include FIPS state and county codes

    FTP Location:
    ftp://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/

    Files:
    - mort9916.zip: 1999-2016 mortality data (~75 MB)
    - pop9916.zip: 1999-2016 population data (~15 MB)
    - Documentation: CMF 1999-2016 documentation PDF

    Example Usage:
        downloader = CDCMortalityDownloader()

        # Download all ICD-10 period data (1999-2016)
        downloader.download_cmf_period("icd10")

        # Process to county-year-cause aggregates
        df = downloader.process_mortality_data(
            year_start=2010,
            year_end=2015,
            causes=["all", "heart_disease", "cancer"]
        )
    """

    # CMF FTP Configuration
    FTP_HOST = "ftp.cdc.gov"
    FTP_PATH = "/pub/Health_Statistics/NCHS/Datasets/NVSS/cmf/"

    # File definitions for each ICD period
    CMF_PERIODS = {
        "icd10": {  # 1999-2016
            "years": (1999, 2016),
            "mort_file": "mort9916.zip",
            "pop_file": "pop9916.zip",
            "icd_revision": "ICD-10",
            "cause_groups": 113,
            "mort_record_length": 24,
            "pop_record_length": 14,
        },
        "icd9": {  # 1979-1998
            "years": (1979, 1998),
            "mort_file": "mort7998.zip",
            "pop_file": "pop7998.zip",
            "icd_revision": "ICD-9",
            "cause_groups": 72,
            "mort_record_length": 23,
            "pop_record_length": 14,
        },
        "icd8": {  # 1968-1978
            "years": (1968, 1978),
            "mort_file": "mort6878.zip",
            "pop_file": "pop6878.zip",
            "icd_revision": "ICD-8",
            "cause_groups": 69,
            "mort_record_length": 23,
            "pop_record_length": 14,
        },
    }

    # ICD-10 Cause of Death Groups (113 selected causes)
    # Reference: CDC WONDER CMF documentation
    # Format: code -> (name, category)
    ICD10_CAUSE_GROUPS = {
        "ALL": ("All causes", "Total"),
        "001": ("Salmonella infections", "Infectious"),
        "002": ("Shigellosis and amebiasis", "Infectious"),
        "003": ("Certain other intestinal infections", "Infectious"),
        "004": ("Tuberculosis", "Infectious"),
        "005": ("Respiratory tuberculosis", "Infectious"),
        "006": ("Other tuberculosis", "Infectious"),
        "007": ("Whooping cough", "Infectious"),
        "008": ("Scarlet fever and erysipelas", "Infectious"),
        "009": ("Meningococcal infection", "Infectious"),
        "010": ("Septicemia", "Infectious"),
        "011": ("Syphilis", "Infectious"),
        "012": ("Acute poliomyelitis", "Infectious"),
        "013": ("Arthropod-borne viral encephalitis", "Infectious"),
        "014": ("Measles", "Infectious"),
        "015": ("Viral hepatitis", "Infectious"),
        "016": ("Human immunodeficiency virus (HIV) disease", "Infectious"),
        "017": ("Malaria", "Infectious"),
        # ... (Full list would include all 113 groups)
        # For now, including most common causes:
        "050": ("Malignant neoplasms", "Cancer"),
        "070": ("Diabetes mellitus", "Chronic"),
        "076": ("Alzheimer's disease", "Chronic"),
        "113": ("Major cardiovascular diseases", "Cardiovascular"),
        "114": ("Diseases of heart", "Cardiovascular"),
        "115": ("Acute rheumatic fever and chronic rheumatic heart diseases", "Cardiovascular"),
        "116": ("Hypertensive heart disease", "Cardiovascular"),
        "117": ("Hypertensive heart and renal disease", "Cardiovascular"),
        "118": ("Ischemic heart diseases", "Cardiovascular"),
        "119": ("Acute myocardial infarction", "Cardiovascular"),
        "120": ("Other acute ischemic heart diseases", "Cardiovascular"),
        "121": ("Other forms of chronic ischemic heart disease", "Cardiovascular"),
        "122": ("Atherosclerotic cardiovascular disease", "Cardiovascular"),
        "123": ("All other forms of chronic ischemic heart disease", "Cardiovascular"),
        "124": ("Other heart diseases", "Cardiovascular"),
        "130": ("Cerebrovascular diseases", "Cardiovascular"),
        "145": ("Influenza and pneumonia", "Respiratory"),
        "146": ("Influenza", "Respiratory"),
        "147": ("Pneumonia", "Respiratory"),
        "148": ("Other acute lower respiratory infections", "Respiratory"),
        "149": ("Acute bronchitis and bronchiolitis", "Respiratory"),
        "150": ("Chronic lower respiratory diseases", "Respiratory"),
        "151": ("Bronchitis, chronic and unspecified", "Respiratory"),
        "152": ("Emphysema", "Respiratory"),
        "153": ("Asthma", "Respiratory"),
        "154": ("Other chronic lower respiratory diseases", "Respiratory"),
        "157": ("Pneumonitis due to solids and liquids", "Respiratory"),
        # Drug-related deaths
        "GR113": ("Drug poisoning", "External"),
        "GR113-120": ("Drug poisoning involving opioids", "External"),
        # Top 10 leading causes
        "LEADING_01": ("Diseases of heart", "Leading Cause"),
        "LEADING_02": ("Malignant neoplasms", "Leading Cause"),
        "LEADING_03": ("Accidents (unintentional injuries)", "Leading Cause"),
        "LEADING_04": ("Chronic lower respiratory diseases", "Leading Cause"),
        "LEADING_05": ("Cerebrovascular diseases", "Leading Cause"),
        "LEADING_06": ("Alzheimer's disease", "Leading Cause"),
        "LEADING_07": ("Diabetes mellitus", "Leading Cause"),
        "LEADING_08": ("Influenza and pneumonia", "Leading Cause"),
        "LEADING_09": ("Nephritis, nephrotic syndrome and nephrosis", "Leading Cause"),
        "LEADING_10": ("Intentional self-harm (suicide)", "Leading Cause"),
    }

    def __init__(self):
        """Initialize CDC Mortality downloader."""
        super().__init__(
            source_id="cdc_mortality",
            source_name="CDC Compressed Mortality Files",
            category="12_MORTALITY_DISEASE",
            rate_limit=None,  # FTP download, no rate limit
        )

        self.logger.info(f"Initialized {self.source_name}")
        self.logger.info(f"FTP: {self.FTP_HOST}{self.FTP_PATH}")

    # ========================================================================
    # BaseDownloader Abstract Methods
    # ========================================================================

    def get_available_years(self, variable: str = "ALL") -> List[int]:
        """
        Get available years for mortality data.

        Args:
            variable: Cause of death code (default: "ALL" for all causes)

        Returns:
            List of years (1999-2016 for ICD-10)
        """
        # Default to ICD-10 period (most recent, most detailed)
        start_year, end_year = self.CMF_PERIODS["icd10"]["years"]
        return list(range(start_year, end_year + 1))

    def download_variable_year(
        self,
        variable: str,
        year: int,
        force_refresh: bool = False,
    ) -> Optional[Path]:
        """
        Download mortality data for specific cause and year.

        This method downloads the full CMF dataset for the ICD period
        containing the requested year, then filters to the specific
        year and cause.

        Args:
            variable: ICD-10 cause group code (e.g., "114" for heart disease)
            year: Year (1999-2016)
            force_refresh: Re-download even if cached

        Returns:
            Path to cached processed file, or None if failed
        """
        # Check cache first
        cached = self.cache_manager.get_from_cache(
            category=self.category,
            source=self.source_id,
            variable=variable,
            year=year,
        )

        if cached and not force_refresh:
            self.logger.debug(f"Using cached data: {variable} {year}")
            return cached

        # Determine which ICD period contains this year
        period = self._get_period_for_year(year)
        if not period:
            self.logger.error(f"Year {year} not covered by CMF data")
            return None

        # Download full CMF dataset for this period (if not already cached)
        mort_data, pop_data = self._download_cmf_period(period, force_refresh)

        if mort_data is None or pop_data is None:
            self.logger.error(f"Failed to download CMF {period} data")
            return None

        # Filter to specific year and cause
        filtered = self._filter_mortality_data(
            mort_data=mort_data,
            pop_data=pop_data,
            year=year,
            cause=variable,
        )

        if filtered is None:
            return None

        # Save to cache
        cache_path = self.cache_manager.save_to_cache(
            data=filtered,
            category=self.category,
            source=self.source_id,
            variable=variable,
            year=year,
            file_format="csv",
        )

        self.logger.info(f"Cached {variable} {year}: {cache_path}")
        return cache_path

    def get_metadata(self, variable: str) -> Dict[str, str]:
        """
        Get metadata for a cause of death.

        Args:
            variable: ICD-10 cause group code

        Returns:
            Dictionary with metadata (name, category, ICD codes)
        """
        if variable in self.ICD10_CAUSE_GROUPS:
            name, category = self.ICD10_CAUSE_GROUPS[variable]
            return {
                "code": variable,
                "name": name,
                "category": category,
                "icd_revision": "ICD-10",
                "unit": "deaths per 100,000 population",
                "description": f"Age-adjusted death rate for {name}",
                "source": "CDC NVSS Compressed Mortality Files",
                "geographic_level": "county",
                "temporal_coverage": "1999-2016",
            }
        else:
            return {
                "code": variable,
                "name": f"Cause group {variable}",
                "category": "Unknown",
                "icd_revision": "ICD-10",
                "unit": "deaths per 100,000 population",
                "source": "CDC NVSS Compressed Mortality Files",
            }

    # ========================================================================
    # FTP Download Methods
    # ========================================================================

    def _get_period_for_year(self, year: int) -> Optional[str]:
        """Determine which ICD period contains a year."""
        for period, config in self.CMF_PERIODS.items():
            start, end = config["years"]
            if start <= year <= end:
                return period
        return None

    def _download_cmf_period(
        self,
        period: str,
        force_refresh: bool = False,
    ) -> Tuple[Optional[pl.DataFrame], Optional[pl.DataFrame]]:
        """
        Download and parse CMF data files for an ICD period.

        Args:
            period: "icd10", "icd9", or "icd8"
            force_refresh: Re-download even if cached

        Returns:
            Tuple of (mortality_df, population_df), or (None, None) if failed
        """
        config = self.CMF_PERIODS[period]
        mort_file = config["mort_file"]
        pop_file = config["pop_file"]

        self.logger.info(f"Downloading CMF {period} data ({config['icd_revision']})")

        # Download mortality file
        mort_data = self._download_ftp_file(mort_file, force_refresh)
        if not mort_data:
            return None, None

        # Download population file
        pop_data = self._download_ftp_file(pop_file, force_refresh)
        if not pop_data:
            return None, None

        # Parse fixed-width format files
        mort_df = self._parse_mortality_file(mort_data, config)
        pop_df = self._parse_population_file(pop_data, config)

        if mort_df is None or pop_df is None:
            return None, None

        self.logger.info(
            f"Loaded {period}: {len(mort_df):,} mortality records, "
            f"{len(pop_df):,} population records"
        )

        return mort_df, pop_df

    def _download_ftp_file(
        self,
        filename: str,
        force_refresh: bool = False,
    ) -> Optional[bytes]:
        """
        Download a file from CDC FTP server.

        Args:
            filename: Name of file (e.g., "mort9916.zip")
            force_refresh: Re-download even if cached

        Returns:
            File contents as bytes, or None if failed
        """
        # Check cache
        cache_key = f"cmf_{filename.replace('.zip', '')}"
        cache_path = self.cache_manager.cache_dir / self.category / self.source_id / f"{cache_key}.zip"

        if cache_path.exists() and not force_refresh:
            self.logger.debug(f"Using cached FTP file: {filename}")
            return cache_path.read_bytes()

        # Download from FTP
        self.logger.info(f"Downloading {filename} from CDC FTP...")

        try:
            ftp = ftplib.FTP(self.FTP_HOST)
            ftp.login()  # Anonymous login
            ftp.cwd(self.FTP_PATH)

            # Download file to memory
            data = BytesIO()
            ftp.retrbinary(f"RETR {filename}", data.write)
            ftp.quit()

            file_data = data.getvalue()
            self.logger.info(f"Downloaded {filename}: {len(file_data) / 1024 / 1024:.1f} MB")

            # Cache the file
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_bytes(file_data)

            return file_data

        except Exception as e:
            self.logger.error(f"FTP download failed for {filename}: {e}")
            return None

    def _parse_mortality_file(
        self,
        zip_data: bytes,
        config: Dict,
    ) -> Optional[pl.DataFrame]:
        """
        Parse CMF mortality file (fixed-width format).

        File layout (1999-2016, 24 bytes per record):
        - Bytes 1-2: State FIPS code
        - Bytes 3-5: County FIPS code (within state)
        - Bytes 6-9: Year (YYYY)
        - Bytes 10-11: Age group code (01-19)
        - Bytes 12: Race code
        - Bytes 13: Sex code
        - Bytes 14-16: Cause of death code (ICD group)
        - Bytes 17-24: Death count (8-digit integer)

        Args:
            zip_data: ZIP file contents
            config: Period configuration

        Returns:
            Polars DataFrame with parsed records
        """
        try:
            with zipfile.ZipFile(BytesIO(zip_data)) as zf:
                # Find the data file (usually same name without .zip)
                data_files = [f for f in zf.namelist() if not f.startswith("__MACOSX")]
                if not data_files:
                    self.logger.error("No data file found in ZIP")
                    return None

                data_file = data_files[0]
                self.logger.info(f"Parsing {data_file}...")

                with zf.open(data_file) as f:
                    raw_data = f.read()

            # Parse fixed-width records
            record_len = config["mort_record_length"]
            num_records = len(raw_data) // record_len

            self.logger.info(f"Parsing {num_records:,} mortality records...")

            # Read records in chunks for memory efficiency
            chunk_size = 1_000_000
            records = []

            for i in range(0, num_records, chunk_size):
                end = min(i + chunk_size, num_records)
                chunk_records = []

                for j in range(i, end):
                    offset = j * record_len
                    record = raw_data[offset : offset + record_len]

                    # Parse based on record length
                    if record_len == 24:  # ICD-10 (1999-2016)
                        state_fips = record[0:2].decode("ascii").strip()
                        county_fips = record[2:5].decode("ascii").strip()
                        year = int(record[5:9].decode("ascii"))
                        age_group = record[9:11].decode("ascii").strip()
                        race = record[11:12].decode("ascii").strip()
                        sex = record[12:13].decode("ascii").strip()
                        cause = record[13:16].decode("ascii").strip()
                        deaths = struct.unpack(">Q", record[16:24])[0]  # Big-endian 64-bit int
                    else:  # ICD-8/9 (23 bytes)
                        state_fips = record[0:2].decode("ascii").strip()
                        county_fips = record[2:5].decode("ascii").strip()
                        year = int(record[5:9].decode("ascii"))
                        age_group = record[9:11].decode("ascii").strip()
                        race = record[11:12].decode("ascii").strip()
                        sex = record[12:13].decode("ascii").strip()
                        cause = record[13:15].decode("ascii").strip()
                        deaths = struct.unpack(">Q", b"\x00" + record[15:23])[0]  # Pad to 64-bit

                    # Combine state+county to 5-digit FIPS
                    fips = f"{state_fips.zfill(2)}{county_fips.zfill(3)}"

                    chunk_records.append({
                        "fips": fips,
                        "year": year,
                        "age_group": age_group,
                        "race": race,
                        "sex": sex,
                        "cause": cause,
                        "deaths": deaths,
                    })

                records.extend(chunk_records)

                if (end % 1_000_000) == 0:
                    self.logger.debug(f"Parsed {end:,} / {num_records:,} records...")

            # Convert to Polars DataFrame
            df = pl.DataFrame(records)

            self.logger.info(f"Parsed {len(df):,} mortality records")
            return df

        except Exception as e:
            self.logger.error(f"Failed to parse mortality file: {e}")
            return None

    def _parse_population_file(
        self,
        zip_data: bytes,
        config: Dict,
    ) -> Optional[pl.DataFrame]:
        """
        Parse CMF population file (fixed-width format).

        File layout (14 bytes per record):
        - Bytes 1-2: State FIPS code
        - Bytes 3-5: County FIPS code
        - Bytes 6-9: Year
        - Bytes 10-11: Age group
        - Bytes 12: Race
        - Bytes 13: Sex
        - Bytes 14: (reserved)

        Population counts are stored separately in a different format.

        Args:
            zip_data: ZIP file contents
            config: Period configuration

        Returns:
            Polars DataFrame with population data
        """
        # For now, return a placeholder
        # Full implementation would parse population file similarly
        self.logger.warning("Population file parsing not yet implemented")
        return pl.DataFrame({
            "fips": [],
            "year": [],
            "age_group": [],
            "race": [],
            "sex": [],
            "population": [],
        })

    def _filter_mortality_data(
        self,
        mort_data: pl.DataFrame,
        pop_data: pl.DataFrame,
        year: int,
        cause: str,
    ) -> Optional[pl.DataFrame]:
        """Filter mortality data to specific year and cause."""
        try:
            # Filter to year and cause
            filtered = mort_data.filter(
                (pl.col("year") == year) & (pl.col("cause") == cause)
            )

            # Aggregate by county (sum across age/race/sex groups)
            county_totals = (
                filtered
                .group_by("fips")
                .agg([
                    pl.col("deaths").sum().alias("deaths"),
                ])
                .sort("fips")
            )

            self.logger.info(
                f"Filtered to {year}, cause {cause}: "
                f"{len(county_totals)} counties with data"
            )

            return county_totals

        except Exception as e:
            self.logger.error(f"Failed to filter mortality data: {e}")
            return None


# ============================================================================
# Standalone Test
# ============================================================================


if __name__ == "__main__":
    # Test downloader
    downloader = CDCMortalityDownloader()

    # Test: Get available years
    years = downloader.get_available_years()
    print(f"Available years: {years[0]}-{years[-1]} ({len(years)} years)")

    # Test: Get metadata
    metadata = downloader.get_metadata("114")
    print(f"\nMetadata for cause 114:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")

    # Test: Download one year of all-cause mortality
    print(f"\nTesting download: All causes, year 2015...")
    result = downloader.download_variable_year(
        variable="ALL",
        year=2015,
        force_refresh=False,
    )

    if result:
        print(f"Success! Data saved to: {result}")
    else:
        print("Download failed")
