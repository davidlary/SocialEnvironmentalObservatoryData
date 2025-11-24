#!/usr/bin/env python3
"""
Script 02: Build Source Registry
=================================

Parse markdown documentation files from SocialEnvironmentalObservatoryDataList repository
to build comprehensive source registry and variable catalog.

Per IMPLEMENTATION_PLAN.md lines 399-413:
1. Parse all documentation files in SocialEnvironmentalObservatoryDataList/
2. Extract source metadata (name, agency, category, access method, etc.)
3. Generate config/sources_registry.json with ~200 source entries
4. Generate config/variable_catalog.json with ~43,000 variable entries
5. Validate outputs

Author: Context-Preserving Framework v4.7.1
Created: 2025-11-24
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import sys

# Setup paths directly
PROJECT_ROOT = Path(__file__).parent.parent
DATA_LIST_REPO = PROJECT_ROOT.parent / "SocialEnvironmentalObservatoryDataList"

# Simple logging setup
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "logs/main.log")
    ]
)
logger = logging.getLogger("source_registry_builder")


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class SourceMetadata:
    """Metadata for a single data source"""
    source_id: str
    name: str
    official_name: str
    agency: str
    category: str
    status: str
    priority: int
    geographic_coverage: Dict = field(default_factory=dict)
    temporal_coverage: Dict = field(default_factory=dict)
    access_method: Dict = field(default_factory=dict)
    documentation: Dict = field(default_factory=dict)
    implementation: Dict = field(default_factory=dict)
    variable_count: int = 0


@dataclass
class VariableMetadata:
    """Metadata for a single variable"""
    variable_id: str
    name: str
    code: Optional[str]
    description: str
    unit: str
    source_id: str
    category: str
    temporal_coverage: Dict = field(default_factory=dict)
    data_type: str = "continuous"
    notes: str = ""


# ============================================================================
# MARKDOWN PARSER
# ============================================================================

class MarkdownParser:
    """Parse structured markdown files to extract source metadata"""

    def __init__(self, file_path: Path, category: str):
        self.file_path = file_path
        self.category = category
        self.content = file_path.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')

    def extract_header_metadata(self) -> Dict:
        """Extract file-level metadata from header"""
        metadata = {
            'title': '',
            'last_updated': '',
            'geographic_coverage': '',
            'status': ''
        }

        for i, line in enumerate(self.lines[:30]):  # Check first 30 lines
            if line.startswith('# '):
                metadata['title'] = line[2:].strip()
            elif '**Last Updated**:' in line:
                metadata['last_updated'] = line.split('**Last Updated**:')[-1].strip()
            elif '**Geographic Coverage**:' in line:
                metadata['geographic_coverage'] = line.split('**Geographic Coverage**:')[-1].strip()
            elif '**Status**:' in line:
                metadata['status'] = line.split('**Status**:')[-1].strip()

        return metadata

    def find_source_sections(self) -> List[Tuple[str, int, int]]:
        """
        Find all source sections in document
        Returns: List of (source_name, start_line, end_line)
        """
        sources = []
        source_pattern = re.compile(r'^### Source \d+: (.+)$')

        i = 0
        while i < len(self.lines):
            match = source_pattern.match(self.lines[i])
            if match:
                source_name = match.group(1).strip()
                start_line = i

                # Find end of this source section (next ### or end of file)
                end_line = len(self.lines)
                for j in range(i + 1, len(self.lines)):
                    if self.lines[j].startswith('### '):
                        end_line = j
                        break

                sources.append((source_name, start_line, end_line))
                i = end_line
            else:
                i += 1

        return sources

    def parse_field(self, lines: List[str], field_name: str) -> Optional[str]:
        """Extract value of a field like **Official Name**: value"""
        pattern = re.compile(f'\\*\\*{re.escape(field_name)}\\*\\*:(.+)$')
        for line in lines:
            match = pattern.search(line)
            if match:
                return match.group(1).strip()
        return None

    def parse_source_section(self, source_name: str, start_idx: int, end_idx: int) -> Optional[SourceMetadata]:
        """Parse individual source section"""
        section_lines = self.lines[start_idx:end_idx]

        # Extract basic fields
        official_name = self.parse_field(section_lines, 'Official Name') or source_name
        agency = self.parse_field(section_lines, 'Agency') or 'Unknown'
        status_line = self.parse_field(section_lines, 'Status') or 'Unknown'

        # Parse status
        if '✅' in status_line or 'operational' in status_line.lower():
            status = 'operational'
        elif 'planned' in status_line.lower() or 'ready' in status_line.lower():
            status = 'planned'
        elif '⚠️' in status_line or 'blocked' in status_line.lower():
            status = 'blocked'
        elif 'restricted' in status_line.lower():
            status = 'restricted'
        else:
            status = 'unknown'

        # Generate source ID
        source_id = self.generate_source_id(source_name)

        # Parse geographic coverage
        geographic_coverage = self.parse_geographic_coverage(section_lines)

        # Parse temporal coverage
        temporal_coverage = self.parse_temporal_coverage(section_lines)

        # Parse access method
        access_method = self.parse_access_method(section_lines)

        # Create source metadata
        source = SourceMetadata(
            source_id=source_id,
            name=source_name,
            official_name=official_name,
            agency=agency,
            category=self.category,
            status=status,
            priority=5,  # Will be assigned later
            geographic_coverage=geographic_coverage,
            temporal_coverage=temporal_coverage,
            access_method=access_method,
            documentation={
                'file_path': str(self.file_path.relative_to(DATA_LIST_REPO)),
                'source_section': f'Source: {source_name}',
                'notes': ''
            },
            implementation={
                'downloader_class': None,
                'implemented': False,
                'script': 'scripts/03_download_source.py',
                'test_status': 'not_tested'
            }
        )

        return source

    def generate_source_id(self, source_name: str) -> str:
        """Generate unique source ID from category and name"""
        # Clean source name
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', source_name)
        clean_name = re.sub(r'\s+', '_', clean_name).upper()

        # Combine category and name
        category_code = self.category.split('_')[0]  # Get "01" from "01_AIR_ATMOSPHERE"
        source_id = f"{category_code}_{clean_name[:30]}"  # Limit length

        return source_id

    def parse_geographic_coverage(self, lines: List[str]) -> Dict:
        """Parse geographic coverage section"""
        coverage = {
            'level': 'unknown',
            'county_native': False,
            'requires_aggregation': False,
            'coverage_description': ''
        }

        for line in lines:
            if '**Geographic**:' in line or '- **Geographic**:' in line:
                desc = line.split('**Geographic**:')[-1].strip()
                coverage['coverage_description'] = desc

                # Infer level
                if 'county' in desc.lower() or 'counties' in desc.lower():
                    coverage['level'] = 'county'
                    coverage['county_native'] = True
                elif 'state' in desc.lower():
                    coverage['level'] = 'state'
                elif 'national' in desc.lower():
                    coverage['level'] = 'national'

                # Check if requires aggregation
                if 'aggregat' in desc.lower() or 'raster' in desc.lower() or 'grid' in desc.lower():
                    coverage['requires_aggregation'] = True
                    coverage['county_native'] = False

        return coverage

    def parse_temporal_coverage(self, lines: List[str]) -> Dict:
        """Parse temporal coverage section"""
        coverage = {
            'start_year': None,
            'end_year': None,
            'frequency': 'unknown',
            'update_schedule': '',
            'last_updated': ''
        }

        for line in lines:
            if '**Years**:' in line or '- **Years**:' in line:
                years_text = line.split('**Years**:')[-1].strip()
                # Try to extract year range
                year_match = re.search(r'(\d{4})[^\d]+(\d{4}|present)', years_text, re.IGNORECASE)
                if year_match:
                    coverage['start_year'] = int(year_match.group(1))
                    end_year_str = year_match.group(2)
                    coverage['end_year'] = 2025 if end_year_str.lower() == 'present' else int(end_year_str)

            elif '**Frequency**:' in line or '- **Frequency**:' in line:
                freq_text = line.split('**Frequency**:')[-1].strip().lower()
                if 'annual' in freq_text:
                    coverage['frequency'] = 'annual'
                elif 'month' in freq_text:
                    coverage['frequency'] = 'monthly'
                elif 'daily' in freq_text or 'day' in freq_text:
                    coverage['frequency'] = 'daily'
                elif 'hour' in freq_text:
                    coverage['frequency'] = 'hourly'
                elif 'triennial' in freq_text or '3 year' in freq_text:
                    coverage['frequency'] = 'triennial'

            elif '**Update Schedule**:' in line or '- **Update Schedule**:' in line:
                coverage['update_schedule'] = line.split('**Update Schedule**:')[-1].strip()

        return coverage

    def parse_access_method(self, lines: List[str]) -> Dict:
        """Parse data access method section"""
        method = {
            'type': 'unknown',
            'url': '',
            'api_endpoint': '',
            'authentication': 'unknown',
            'format': ''
        }

        # Look for access method indicators
        for line in lines:
            line_lower = line.lower()

            # Type
            if 'api' in line_lower and 'url' in line_lower:
                method['type'] = 'api'
            elif 'bulk download' in line_lower or 'bulk csv' in line_lower:
                method['type'] = 'bulk_download'
            elif 'raster' in line_lower or 'geotiff' in line_lower:
                method['type'] = 'raster'
            elif 'manual' in line_lower or 'data request' in line_lower:
                method['type'] = 'manual'

            # URL
            if '**URL**:' in line or '**Download URL**:' in line or '**API URL**:' in line:
                url_match = re.search(r'https?://[^\s\)]+', line)
                if url_match:
                    method['url'] = url_match.group(0)

            # Authentication
            if 'api key' in line_lower or 'registration' in line_lower:
                method['authentication'] = 'api_key'
            elif 'no authentication' in line_lower or 'public' in line_lower:
                method['authentication'] = 'none'

            # Format
            if 'csv' in line_lower:
                method['format'] = 'csv'
            elif 'json' in line_lower:
                method['format'] = 'json'
            elif 'netcdf' in line_lower:
                method['format'] = 'netcdf'
            elif 'geotiff' in line_lower:
                method['format'] = 'geotiff'

        return method


# ============================================================================
# SOURCE REGISTRY BUILDER
# ============================================================================

class SourceRegistryBuilder:
    """Build comprehensive source registry from markdown files"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.sources: List[SourceMetadata] = []
        self.variables: List[VariableMetadata] = []
        self.parser_class = MarkdownParser
        self.source_id_counter: Dict[str, int] = {}  # Track ID usage for deduplication

    def discover_markdown_files(self) -> List[Tuple[Path, str]]:
        """
        Find all markdown files in repository
        Returns: List of (file_path, category)
        """
        md_files = []

        # Skip these files
        skip_files = {'README.md', 'MASTER_INDEX.md', 'PROJECT_COMPLETION_SUMMARY.md', 'CLAUDE.md'}

        # Walk through category directories
        for item in sorted(self.repo_path.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                category = item.name

                # Find markdown files in this category
                for md_file in item.glob('*.md'):
                    if md_file.name not in skip_files:
                        md_files.append((md_file, category))

        return md_files

    def process_file(self, file_path: Path, category: str):
        """Process single markdown file"""
        try:
            logger.info(f"Processing: {file_path.relative_to(self.repo_path)}")

            parser = self.parser_class(file_path, category)

            # Find source sections
            source_sections = parser.find_source_sections()

            if not source_sections:
                logger.warning(f"No source sections found in {file_path.name}")
                return

            # Parse each source
            for source_name, start_idx, end_idx in source_sections:
                source = parser.parse_source_section(source_name, start_idx, end_idx)
                if source:
                    # Deduplicate source ID if needed
                    base_id = source.source_id
                    if base_id in self.source_id_counter:
                        self.source_id_counter[base_id] += 1
                        source.source_id = f"{base_id}_{self.source_id_counter[base_id]}"
                        logger.debug(f"  Deduplicated ID: {source.source_id}")
                    else:
                        self.source_id_counter[base_id] = 0

                    self.sources.append(source)
                    logger.debug(f"  Extracted: {source.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    def assign_priorities(self):
        """Assign priority based on implementation status and importance"""
        for source in self.sources:
            # Priority 1: Already implemented
            if source.source_id in ['01_EPA_AQS', '15_IPUMS_NHGIS']:
                source.priority = 1
                source.implementation['implemented'] = True

                if source.source_id == '01_EPA_AQS':
                    source.implementation['downloader_class'] = 'EPAAQSDownloader'
                    source.implementation['test_status'] = 'passed'
                elif source.source_id == '15_IPUMS_NHGIS':
                    source.implementation['downloader_class'] = 'NHGISDownloader'
                    source.implementation['test_status'] = 'passed'

            # Priority 2: Operational, county-native, API access
            elif (source.status == 'operational' and
                  source.geographic_coverage.get('county_native') and
                  source.access_method.get('type') in ['api', 'bulk_download']):
                source.priority = 2

            # Priority 3: Operational but requires aggregation or complex access
            elif source.status == 'operational':
                source.priority = 3

            # Priority 4: Planned sources
            elif source.status == 'planned':
                source.priority = 4

            # Priority 5: Blocked, restricted, or unknown
            else:
                source.priority = 5

    def generate_source_registry(self) -> Dict:
        """Generate sources_registry.json structure"""
        sources_list = [asdict(s) for s in self.sources]

        # Sort by priority, then by name
        sources_list.sort(key=lambda x: (x['priority'], x['name']))

        registry = {
            'sources': sources_list,
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'total_sources': len(sources_list),
                'script_version': '2.0',
                'companion_repo_path': str(self.repo_path.relative_to(PROJECT_ROOT.parent)),
                'source_counts_by_priority': {
                    str(i): len([s for s in self.sources if s.priority == i])
                    for i in range(1, 6)
                },
                'source_counts_by_status': {
                    status: len([s for s in self.sources if s.status == status])
                    for status in ['operational', 'planned', 'blocked', 'restricted', 'unknown']
                },
                'source_counts_by_category': {}
            }
        }

        # Count by category
        for source in self.sources:
            cat = source.category
            if cat not in registry['metadata']['source_counts_by_category']:
                registry['metadata']['source_counts_by_category'][cat] = 0
            registry['metadata']['source_counts_by_category'][cat] += 1

        return registry

    def generate_variable_catalog(self) -> Dict:
        """Generate variable_catalog.json structure (placeholder for now)"""
        variables_list = [asdict(v) for v in self.variables]

        catalog = {
            'variables': variables_list,
            'metadata': {
                'generated_date': datetime.now().isoformat(),
                'total_variables': len(variables_list),
                'script_version': '2.0',
                'notes': 'Variable extraction not yet implemented - placeholder file'
            }
        }

        return catalog

    def validate_output(self) -> bool:
        """Validate generated data"""
        logger.info("Validating generated data...")

        # Check minimum sources
        if len(self.sources) < 10:
            logger.error(f"Too few sources extracted: {len(self.sources)} (expected >10)")
            return False

        # Check for unique source IDs
        source_ids = [s.source_id for s in self.sources]
        if len(source_ids) != len(set(source_ids)):
            logger.error("Duplicate source IDs found")
            duplicates = [sid for sid in source_ids if source_ids.count(sid) > 1]
            logger.error(f"Duplicates: {set(duplicates)}")
            return False

        # Check required fields
        for source in self.sources:
            if not source.name or not source.agency or not source.category:
                logger.error(f"Missing required fields for source: {source.source_id}")
                return False

        logger.info(f"✅ Validation passed: {len(self.sources)} sources, {len(self.variables)} variables")
        return True

    def save_json(self, data: Dict, output_path: Path):
        """Save JSON with pretty formatting"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("Script 02: Build Source Registry")
    logger.info("=" * 80)
    logger.info(f"Companion repo: {DATA_LIST_REPO}")
    logger.info(f"Output: {PROJECT_ROOT / 'config'}")
    logger.info("")

    # Check companion repo exists
    if not DATA_LIST_REPO.exists():
        logger.error(f"Companion repository not found: {DATA_LIST_REPO}")
        logger.error("Please ensure SocialEnvironmentalObservatoryDataList is in the correct location")
        return 1

    # Initialize builder
    builder = SourceRegistryBuilder(DATA_LIST_REPO)

    # Discover files
    logger.info("Discovering markdown files...")
    md_files = builder.discover_markdown_files()
    logger.info(f"Found {len(md_files)} markdown files across {len(set(c for _, c in md_files))} categories")
    logger.info("")

    # Process each file
    logger.info("Parsing markdown files...")
    for md_file, category in md_files:
        builder.process_file(md_file, category)
    logger.info("")

    # Assign priorities
    logger.info("Assigning source priorities...")
    builder.assign_priorities()
    logger.info("")

    # Generate outputs
    logger.info("Generating output files...")
    source_registry = builder.generate_source_registry()
    variable_catalog = builder.generate_variable_catalog()
    logger.info("")

    # Display summary
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total sources extracted: {len(builder.sources)}")
    logger.info(f"Total variables extracted: {len(builder.variables)} (variable extraction not yet implemented)")
    logger.info("")
    logger.info("Sources by priority:")
    for priority in range(1, 6):
        count = len([s for s in builder.sources if s.priority == priority])
        logger.info(f"  Priority {priority}: {count} sources")
    logger.info("")
    logger.info("Sources by status:")
    for status in ['operational', 'planned', 'blocked', 'restricted', 'unknown']:
        count = len([s for s in builder.sources if s.status == status])
        logger.info(f"  {status.capitalize()}: {count} sources")
    logger.info("")

    # Validate
    if not builder.validate_output():
        logger.error("❌ Validation failed - outputs not saved")
        return 1

    # Save
    builder.save_json(source_registry, PROJECT_ROOT / "config/sources_registry.json")
    builder.save_json(variable_catalog, PROJECT_ROOT / "config/variable_catalog.json")
    logger.info("")
    logger.info("=" * 80)
    logger.info("✅ Source registry generation complete")
    logger.info("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
