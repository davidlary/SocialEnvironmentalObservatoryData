"""
Geographic utilities for county-level data processing.

Provides reusable GIS operations with performance optimization:
- FIPS validation
- Coordinate system transformations
- Spatial joins (facilities to counties)
- Zonal statistics (rasters to counties)
- County boundary operations

Design Patterns:
- Singleton: Cache loaded shapefiles
- Strategy: Different aggregation strategies for different data types
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import geopandas as gpd
import numpy as np
import polars as pl
from loguru import logger
from shapely.geometry import Point
from rasterstats import zonal_stats

from utils.constants import (
    CRS_US_ALBERS,
    CRS_WGS84,
    METADATA_DIR,
    TOTAL_US_COUNTIES,
    ZONAL_STATS_DEFAULT,
)


# ============================================================================
# FIPS CODE UTILITIES
# ============================================================================


def validate_fips(fips: str) -> bool:
    """
    Validate FIPS code format.

    Args:
        fips: 5-digit FIPS code string

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_fips("48453")  # Travis County, TX
        True
        >>> validate_fips("99999")  # Invalid
        False
    """
    if not isinstance(fips, str):
        return False

    if len(fips) != 5:
        return False

    if not fips.isdigit():
        return False

    # State FIPS must be valid (01-56, 60, 66, 69, 72, 78)
    state_fips = int(fips[:2])
    valid_states = list(range(1, 57)) + [60, 66, 69, 72, 78]

    return state_fips in valid_states


def split_fips(fips: str) -> Tuple[str, str]:
    """
    Split 5-digit FIPS into state and county components.

    Args:
        fips: 5-digit FIPS code string

    Returns:
        Tuple of (state_fips, county_fips)

    Example:
        >>> split_fips("48453")
        ("48", "453")
    """
    if not validate_fips(fips):
        raise ValueError(f"Invalid FIPS code: {fips}")

    return fips[:2], fips[2:]


def construct_fips(state_fips: Union[str, int], county_fips: Union[str, int]) -> str:
    """
    Construct 5-digit FIPS from components.

    Args:
        state_fips: 2-digit state code (int or string)
        county_fips: 3-digit county code (int or string)

    Returns:
        5-digit FIPS code string with proper zero-padding

    Example:
        >>> construct_fips(48, 453)
        "48453"
        >>> construct_fips(6, 37)  # Los Angeles County
        "06037"
    """
    state_str = str(state_fips).zfill(2)
    county_str = str(county_fips).zfill(3)
    fips = state_str + county_str

    if not validate_fips(fips):
        raise ValueError(f"Constructed invalid FIPS: {fips}")

    return fips


# ============================================================================
# COUNTY BOUNDARY OPERATIONS (Singleton Pattern)
# ============================================================================


class CountyBoundaryManager:
    """
    Singleton manager for county boundaries (cached in memory).

    Loads county shapefile once and caches for reuse.
    """

    _instance = None
    _boundaries = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_boundaries(
        self,
        shapefile_path: Optional[Union[str, Path]] = None,
        crs: str = CRS_WGS84,
    ) -> gpd.GeoDataFrame:
        """
        Load county boundaries (cached).

        Args:
            shapefile_path: Path to county boundaries (default: metadata dir)
            crs: Target CRS (default: WGS84)

        Returns:
            GeoDataFrame with county boundaries
        """
        if self._boundaries is not None:
            logger.debug("Using cached county boundaries")
            return self._boundaries

        if shapefile_path is None:
            shapefile_path = METADATA_DIR / "county_boundaries_2020.gpkg"

        shapefile_path = Path(shapefile_path)

        if not shapefile_path.exists():
            raise FileNotFoundError(
                f"County boundaries not found: {shapefile_path}. "
                f"Run scripts/01_download_metadata.py first."
            )

        logger.info(f"Loading county boundaries from {shapefile_path}")

        try:
            self._boundaries = gpd.read_file(shapefile_path)

            # Ensure GEOID column (FIPS code)
            if "GEOID" not in self._boundaries.columns:
                raise ValueError("County boundaries missing GEOID column")

            # Reproject if needed
            if self._boundaries.crs != crs:
                logger.debug(f"Reprojecting boundaries to {crs}")
                self._boundaries = self._boundaries.to_crs(crs)

            # Validate county count
            if len(self._boundaries) != TOTAL_US_COUNTIES:
                logger.warning(
                    f"Expected {TOTAL_US_COUNTIES} counties, "
                    f"found {len(self._boundaries)}"
                )

            logger.info(f"Loaded {len(self._boundaries)} county boundaries")
            return self._boundaries

        except Exception as e:
            logger.error(f"Error loading county boundaries: {e}")
            raise

    def get_county_boundary(self, fips: str) -> Optional[gpd.GeoDataFrame]:
        """
        Get boundary for specific county.

        Args:
            fips: 5-digit FIPS code

        Returns:
            GeoDataFrame with single county boundary, or None if not found
        """
        if self._boundaries is None:
            self.load_boundaries()

        county = self._boundaries[self._boundaries["GEOID"] == fips]

        if len(county) == 0:
            logger.warning(f"County not found: {fips}")
            return None

        return county


# Singleton instance
_boundary_manager = CountyBoundaryManager()


def get_county_boundaries(
    crs: str = CRS_WGS84,
) -> gpd.GeoDataFrame:
    """
    Get all county boundaries (convenience function).

    Args:
        crs: Target CRS

    Returns:
        GeoDataFrame with all county boundaries
    """
    return _boundary_manager.load_boundaries(crs=crs)


# ============================================================================
# POINT-TO-COUNTY SPATIAL JOIN (for facility data)
# ============================================================================


def join_points_to_counties(
    df: pl.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    id_col: Optional[str] = None,
) -> pl.DataFrame:
    """
    Spatial join point data to counties.

    Used for facility-level data (TRI, Superfund, etc.).

    Args:
        df: Polars DataFrame with latitude/longitude columns
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        id_col: Optional ID column to preserve

    Returns:
        Polars DataFrame with FIPS column added

    Example:
        >>> facilities = pl.DataFrame({
        ...     "facility_id": [1, 2, 3],
        ...     "latitude": [30.267, 34.052, 41.878],
        ...     "longitude": [-97.743, -118.244, -87.630]
        ... })
        >>> joined = join_points_to_counties(facilities)
        >>> joined["FIPS"]  # ["48453", "06037", "17031"]
    """
    logger.info(f"Performing spatial join for {len(df)} points")

    # Convert Polars to pandas for geopandas (temporary)
    df_pd = df.to_pandas()

    # Create geometry
    geometry = [
        Point(xy) for xy in zip(df_pd[lon_col], df_pd[lat_col])
    ]

    gdf_points = gpd.GeoDataFrame(
        df_pd, geometry=geometry, crs=CRS_WGS84
    )

    # Load county boundaries
    counties = get_county_boundaries()

    # Spatial join
    joined = gpd.sjoin(
        gdf_points,
        counties[["GEOID", "geometry"]],
        how="left",
        predicate="within",
    )

    # Convert back to Polars
    result_df = pl.from_pandas(joined.drop(columns=["geometry"]))

    # Rename GEOID to FIPS
    if "GEOID" in result_df.columns:
        result_df = result_df.rename({"GEOID": "FIPS"})

    # Count successful joins
    matched = result_df.filter(pl.col("FIPS").is_not_null()).shape[0]
    logger.info(f"Matched {matched}/{len(df)} points to counties")

    return result_df


def aggregate_points_to_counties(
    df: pl.DataFrame,
    value_col: str,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    agg_func: str = "sum",
) -> pl.DataFrame:
    """
    Aggregate point data to county level.

    Args:
        df: Polars DataFrame with point data
        value_col: Column to aggregate
        lat_col: Latitude column name
        lon_col: Longitude column name
        agg_func: Aggregation function (sum, mean, count)

    Returns:
        Polars DataFrame with FIPS and aggregated value

    Example:
        >>> emissions = pl.DataFrame({
        ...     "facility": ["A", "B", "C"],
        ...     "latitude": [30.267, 30.268, 30.269],
        ...     "longitude": [-97.743, -97.744, -97.745],
        ...     "emissions_tons": [100, 200, 150]
        ... })
        >>> county_totals = aggregate_points_to_counties(
        ...     emissions, "emissions_tons", agg_func="sum"
        ... )
    """
    # First, join points to counties
    df_with_fips = join_points_to_counties(df, lat_col, lon_col)

    # Then aggregate by county
    if agg_func == "sum":
        agg_expr = pl.col(value_col).sum()
    elif agg_func == "mean":
        agg_expr = pl.col(value_col).mean()
    elif agg_func == "count":
        agg_expr = pl.col(value_col).count()
    else:
        raise ValueError(f"Unknown aggregation function: {agg_func}")

    county_summary = (
        df_with_fips
        .filter(pl.col("FIPS").is_not_null())
        .group_by("FIPS")
        .agg([
            agg_expr.alias("value"),
            pl.count().alias("n_facilities")
        ])
    )

    logger.info(f"Aggregated to {len(county_summary)} counties")

    return county_summary


# ============================================================================
# RASTER-TO-COUNTY ZONAL STATISTICS
# ============================================================================


def aggregate_raster_to_counties(
    raster_path: Union[str, Path],
    statistic: str = ZONAL_STATS_DEFAULT,
    nodata_value: Optional[float] = None,
) -> pl.DataFrame:
    """
    Aggregate raster to county-level statistics.

    Used for gridded data (NLCD, ERA5, PRISM, etc.).

    Args:
        raster_path: Path to GeoTIFF raster file
        statistic: Statistic to calculate (mean, sum, median, min, max)
        nodata_value: NoData value to exclude

    Returns:
        Polars DataFrame with FIPS and aggregated value

    Example:
        >>> # Aggregate NLCD land cover to county % impervious
        >>> county_impervious = aggregate_raster_to_counties(
        ...     "nlcd_2021_impervious.tif",
        ...     statistic="mean"
        ... )
    """
    raster_path = Path(raster_path)

    if not raster_path.exists():
        raise FileNotFoundError(f"Raster not found: {raster_path}")

    logger.info(f"Computing zonal statistics: {raster_path}")

    # Load county boundaries
    counties = get_county_boundaries()

    # Compute zonal statistics
    stats = zonal_stats(
        counties,
        str(raster_path),
        stats=[statistic],
        nodata=nodata_value,
        all_touched=False,  # Only include pixels with center in polygon
    )

    # Convert to DataFrame
    results = []
    for idx, county_stats in enumerate(stats):
        fips = counties.iloc[idx]["GEOID"]
        value = county_stats.get(statistic, None)
        results.append({"FIPS": fips, "value": value})

    df = pl.DataFrame(results)

    # Count non-null values
    non_null = df.filter(pl.col("value").is_not_null()).shape[0]
    logger.info(
        f"Computed {statistic} for {non_null}/{len(df)} counties"
    )

    return df


# ============================================================================
# COORDINATE TRANSFORMATIONS
# ============================================================================


def transform_coordinates(
    df: pl.DataFrame,
    from_crs: str = CRS_WGS84,
    to_crs: str = CRS_US_ALBERS,
    lon_col: str = "longitude",
    lat_col: str = "latitude",
) -> pl.DataFrame:
    """
    Transform coordinates to different CRS.

    Args:
        df: Polars DataFrame with coordinates
        from_crs: Source CRS (EPSG code)
        to_crs: Target CRS (EPSG code)
        lon_col: Longitude column name
        lat_col: Latitude column name

    Returns:
        Polars DataFrame with transformed coordinates
    """
    logger.debug(f"Transforming coordinates from {from_crs} to {to_crs}")

    # Convert to GeoDataFrame
    df_pd = df.to_pandas()
    geometry = [Point(xy) for xy in zip(df_pd[lon_col], df_pd[lat_col])]
    gdf = gpd.GeoDataFrame(df_pd, geometry=geometry, crs=from_crs)

    # Transform
    gdf_transformed = gdf.to_crs(to_crs)

    # Extract new coordinates
    gdf_transformed[lon_col] = gdf_transformed.geometry.x
    gdf_transformed[lat_col] = gdf_transformed.geometry.y

    # Convert back to Polars
    result = pl.from_pandas(gdf_transformed.drop(columns=["geometry"]))

    return result


# ============================================================================
# DISTANCE CALCULATIONS
# ============================================================================


def calculate_distances_to_counties(
    points: pl.DataFrame,
    lat_col: str = "latitude",
    lon_col: str = "longitude",
    use_centroids: bool = True,
) -> pl.DataFrame:
    """
    Calculate distance from points to county centroids.

    Useful for proximity analysis (e.g., distance to nearest Superfund site).

    Args:
        points: Polars DataFrame with point locations
        lat_col: Latitude column name
        lon_col: Longitude column name
        use_centroids: If True, use county centroids (faster)

    Returns:
        Polars DataFrame with distances to all counties
    """
    logger.info("Calculating distances to counties")

    # Get county boundaries/centroids
    counties = get_county_boundaries(crs=CRS_US_ALBERS)

    if use_centroids:
        counties["geometry"] = counties.geometry.centroid

    # Convert points to GeoDataFrame (in same CRS)
    points_pd = points.to_pandas()
    points_gdf = gpd.GeoDataFrame(
        points_pd,
        geometry=[Point(xy) for xy in zip(points_pd[lon_col], points_pd[lat_col])],
        crs=CRS_WGS84,
    ).to_crs(CRS_US_ALBERS)

    # Calculate distances (this can be slow for many points)
    distances = []
    for idx, point in points_gdf.iterrows():
        county_distances = counties.geometry.distance(point.geometry)
        min_distance = county_distances.min()
        nearest_county = counties.loc[county_distances.idxmin(), "GEOID"]
        distances.append({
            "point_id": idx,
            "nearest_county_fips": nearest_county,
            "distance_meters": min_distance,
        })

    result = pl.DataFrame(distances)

    logger.info(f"Calculated distances for {len(points)} points")

    return result


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================


def validate_county_coverage(df: pl.DataFrame) -> Dict[str, any]:
    """
    Validate county-level data coverage.

    Args:
        df: Polars DataFrame with FIPS column

    Returns:
        Dictionary with coverage statistics

    Example:
        >>> data = pl.DataFrame({"FIPS": ["48453", "06037"]})
        >>> stats = validate_county_coverage(data)
        >>> stats["pct_coverage"]  # 0.064% (2/3143 counties)
    """
    if "FIPS" not in df.columns:
        raise ValueError("DataFrame must have FIPS column")

    unique_fips = df["FIPS"].n_unique()
    pct_coverage = (unique_fips / TOTAL_US_COUNTIES) * 100

    # Check for invalid FIPS
    invalid_fips = [
        fips for fips in df["FIPS"].unique()
        if not validate_fips(str(fips))
    ]

    stats = {
        "total_counties_us": TOTAL_US_COUNTIES,
        "counties_in_data": unique_fips,
        "pct_coverage": round(pct_coverage, 2),
        "missing_counties": TOTAL_US_COUNTIES - unique_fips,
        "invalid_fips_codes": invalid_fips,
    }

    logger.info(
        f"County coverage: {unique_fips}/{TOTAL_US_COUNTIES} "
        f"({pct_coverage:.1f}%)"
    )

    return stats
