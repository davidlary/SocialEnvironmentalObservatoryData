"""
Map Generator for county-level choropleth maps.

Creates publication-quality maps with:
- Quantile-based color classification
- Proper legends and colorbars
- Title with variable name, year, unit
- Geographic projection
- Missing data handling

Every TSV file gets a corresponding map showing the spatial distribution.

Design Patterns:
- Template Method: Standard map creation workflow
- Strategy: Different color schemes for different data types
- Factory: Create appropriate map type based on data
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colorbar import ColorbarBase
from matplotlib.cm import ScalarMappable
import numpy as np
import polars as pl
from loguru import logger

from core.metadata_manager import get_county_boundaries
from utils.constants import (
    COLORMAPS,
    CRS_US_ALBERS,
    DEFAULT_QUANTILES,
    MAP_DPI,
    MAP_FIGSIZE,
    MAP_FORMAT,
    MAP_MISSING_COLOR,
    PROCESSED_DIR,
)
from utils.file_utils import ensure_directory, read_tsv


# ============================================================================
# MAP GENERATOR
# ============================================================================


class MapGenerator:
    """
    Generate choropleth maps from TSV files.

    Maps are saved alongside TSV files with same name but .png extension.
    """

    def __init__(self):
        """Initialize map generator."""
        self.county_boundaries = None
        logger.debug("Map generator initialized")

    def _load_county_boundaries(self) -> gpd.GeoDataFrame:
        """
        Load county boundaries (cached).

        Returns:
            GeoDataFrame with county boundaries in US Albers projection
        """
        if self.county_boundaries is None:
            logger.info("Loading county boundaries for mapping")
            self.county_boundaries = get_county_boundaries()

            # Project to US Albers Equal Area for better visualization
            if self.county_boundaries.crs != CRS_US_ALBERS:
                logger.debug(f"Reprojecting to {CRS_US_ALBERS}")
                self.county_boundaries = self.county_boundaries.to_crs(CRS_US_ALBERS)

            # Convert GEOID to zero-padded string for merging with FIPS
            # (do this AFTER CRS transform to ensure it sticks)
            self.county_boundaries['GEOID'] = (
                self.county_boundaries['GEOID']
                .astype(str)
                .str.zfill(5)
            )

        return self.county_boundaries

    def create_map(
        self,
        tsv_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        variable_name: Optional[str] = None,
        title: Optional[str] = None,
        cmap: str = COLORMAPS["sequential"],
        n_bins: int = DEFAULT_QUANTILES,
        figsize: Tuple[int, int] = MAP_FIGSIZE,
        dpi: int = MAP_DPI,
    ) -> Path:
        """
        Create choropleth map from TSV file.

        Args:
            tsv_path: Path to TSV file
            output_path: Optional output path (default: same dir as TSV, .png)
            variable_name: Variable name for title
            title: Custom title (overrides auto-generated)
            cmap: Matplotlib colormap name
            n_bins: Number of color bins (quantiles)
            figsize: Figure size (width, height) in inches
            dpi: Resolution in dots per inch

        Returns:
            Path to created map

        Example:
            >>> generator = MapGenerator()
            >>> map_path = generator.create_map(
            ...     "data/processed/.../2020_PM25_Annual_Mean.tsv"
            ... )
        """
        tsv_path = Path(tsv_path)

        if not tsv_path.exists():
            raise FileNotFoundError(f"TSV file not found: {tsv_path}")

        logger.info(f"Creating map: {tsv_path.name}")

        # Determine output path
        if output_path is None:
            output_path = tsv_path.with_suffix(f".{MAP_FORMAT}")
        else:
            output_path = Path(output_path)

        ensure_directory(output_path.parent)

        # Load TSV data
        data = read_tsv(tsv_path)

        # Extract metadata from TSV
        year = data["Year"][0] if "Year" in data.columns else "Unknown"
        unit = data["Unit"][0] if "Unit" in data.columns else ""

        # If variable name not provided, try to extract from filename
        if variable_name is None:
            # Filename format: {year}_{variable}.tsv
            filename = tsv_path.stem
            if "_" in filename:
                variable_name = "_".join(filename.split("_")[1:])
            else:
                variable_name = "Variable"

        # Load county boundaries
        counties = self._load_county_boundaries()

        # Merge data with geometries
        # Convert Polars to pandas for geopandas merge
        # Ensure FIPS is string (polars may read it as int64)
        data_with_fips = data.with_columns([
            pl.col("FIPS").cast(pl.Utf8).str.zfill(5)
        ])
        data_pd = data_with_fips.select(["FIPS", "Value"]).to_pandas()

        # Merge on GEOID (already converted to string in _load_county_boundaries)
        counties_with_data = counties.merge(
            data_pd,
            left_on="GEOID",
            right_on="FIPS",
            how="left",
        )

        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        # Calculate quantile breaks
        values = counties_with_data["Value"].dropna()

        if len(values) == 0:
            logger.warning("No data to map - all values are null")
            plt.close()
            return output_path

        # Calculate quantile bins
        bins = np.quantile(values, np.linspace(0, 1, n_bins + 1))

        # Handle case where all values are identical
        if len(np.unique(bins)) == 1:
            logger.warning("All values identical - using single color")
            bins = [bins[0] - 1, bins[0], bins[0] + 1]

        # Create normalization
        norm = mcolors.BoundaryNorm(bins, plt.get_cmap(cmap).N)

        # Plot counties
        counties_with_data.plot(
            column="Value",
            ax=ax,
            cmap=cmap,
            norm=norm,
            edgecolor="white",
            linewidth=0.1,
            legend=False,
            missing_kwds={"color": MAP_MISSING_COLOR, "label": "No data"},
        )

        # Remove axes
        ax.set_axis_off()

        # Create title
        if title is None:
            title = f"{variable_name} ({year})"
            if unit:
                title += f"\nUnit: {unit}"

        ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

        # Add colorbar
        sm = ScalarMappable(norm=norm, cmap=cmap)
        sm.set_array([])

        cbar = fig.colorbar(
            sm,
            ax=ax,
            orientation="horizontal",
            pad=0.02,
            shrink=0.6,
            aspect=30,
        )

        # Format colorbar labels
        cbar.set_label(unit if unit else "Value", fontsize=10)

        # Add data statistics as text
        stats_text = (
            f"Counties: {len(values):,}\n"
            f"Min: {values.min():.2f}\n"
            f"Max: {values.max():.2f}\n"
            f"Mean: {values.mean():.2f}"
        )

        ax.text(
            0.02,
            0.02,
            stats_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="bottom",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
        )

        # Tight layout
        plt.tight_layout()

        # Save figure
        plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
        plt.close()

        logger.info(f"✅ Created map: {output_path.name}")

        return output_path

    def create_maps_for_variable(
        self,
        category: str,
        variable: str,
        **map_kwargs,
    ) -> list[Path]:
        """
        Create maps for all years of a variable.

        Args:
            category: Data category
            variable: Variable name
            **map_kwargs: Additional arguments for create_map()

        Returns:
            List of created map paths

        Example:
            >>> generator = MapGenerator()
            >>> maps = generator.create_maps_for_variable(
            ...     "01_AIR_ATMOSPHERE",
            ...     "PM25_Annual_Mean"
            ... )
            >>> print(f"Created {len(maps)} maps")
        """
        variable_dir = PROCESSED_DIR / category / variable

        if not variable_dir.exists():
            logger.warning(f"Variable directory not found: {variable_dir}")
            return []

        # Find all TSV files
        tsv_files = sorted(variable_dir.glob("*.tsv"))

        if len(tsv_files) == 0:
            logger.warning(f"No TSV files found in {variable_dir}")
            return []

        logger.info(f"Creating maps for {len(tsv_files)} TSV files")

        map_paths = []

        for tsv_path in tsv_files:
            try:
                map_path = self.create_map(
                    tsv_path,
                    variable_name=variable,
                    **map_kwargs,
                )
                map_paths.append(map_path)

            except Exception as e:
                logger.error(f"Error creating map for {tsv_path.name}: {e}")
                # Continue with other files

        logger.info(
            f"✅ Created {len(map_paths)}/{len(tsv_files)} maps for {variable}"
        )

        return map_paths

    def batch_create_maps(
        self,
        category: str,
        **map_kwargs,
    ) -> Dict[str, list[Path]]:
        """
        Create maps for all variables in a category.

        Args:
            category: Data category
            **map_kwargs: Additional arguments for create_map()

        Returns:
            Dictionary mapping variable names to list of map paths

        Example:
            >>> generator = MapGenerator()
            >>> results = generator.batch_create_maps("01_AIR_ATMOSPHERE")
            >>> for var, maps in results.items():
            ...     print(f"{var}: {len(maps)} maps")
        """
        category_dir = PROCESSED_DIR / category

        if not category_dir.exists():
            logger.warning(f"Category directory not found: {category_dir}")
            return {}

        # Find all variable directories
        variable_dirs = [d for d in category_dir.iterdir() if d.is_dir()]

        logger.info(
            f"Creating maps for {len(variable_dirs)} variables in {category}"
        )

        results = {}

        for var_dir in variable_dirs:
            variable_name = var_dir.name

            try:
                map_paths = self.create_maps_for_variable(
                    category,
                    variable_name,
                    **map_kwargs,
                )
                results[variable_name] = map_paths

            except Exception as e:
                logger.error(f"Error creating maps for {variable_name}: {e}")
                results[variable_name] = []

        total_maps = sum(len(paths) for paths in results.values())
        logger.info(f"✅ Created {total_maps} total maps for {category}")

        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_map_generator = None


def get_map_generator() -> MapGenerator:
    """Get map generator (singleton)."""
    global _map_generator
    if _map_generator is None:
        _map_generator = MapGenerator()
    return _map_generator


def create_map(tsv_path: Union[str, Path], **kwargs) -> Path:
    """Create map (convenience function)."""
    generator = get_map_generator()
    return generator.create_map(tsv_path, **kwargs)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MapGenerator",
    "get_map_generator",
    "create_map",
]
