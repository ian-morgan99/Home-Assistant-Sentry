"""
Dependency Graph Builder - Feature 1
Builds a dependency graph from Home Assistant integrations without executing code
Uses static inspection only (manifest.json parsing)
"""
import json
import logging
import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import SpecifierSet

logger = logging.getLogger(__name__)


class DependencyGraphBuilder:
    """Builds dependency graphs from integration manifests"""
    
    # Known high-risk libraries to highlight
    HIGH_RISK_LIBRARIES = {
        'aiohttp', 'cryptography', 'numpy', 'pyjwt', 
        'sqlalchemy', 'protobuf', 'requests', 'urllib3'
    }
    
    # Common paths for Home Assistant integrations
    # Multiple potential paths to handle different HA installation types
    CORE_INTEGRATION_PATHS = [
        '/usr/src/homeassistant/homeassistant/components',  # HA OS/Container (most common)
        '/config/custom_components',  # Custom components (HACS)
        '/usr/local/lib/python*/site-packages/homeassistant/components',  # Python site-packages (glob pattern)
        '/homeassistant/homeassistant/components',  # Core installation
    ]
    
    # Display limit for log messages
    MAX_PATHS_TO_DISPLAY = 5
    
    def __init__(self):
        """Initialize the dependency graph builder"""
        self.integrations = {}
        self.dependency_map = {}  # Maps dependency name to list of integrations using it
        self.graph = {}
        
    def build_graph_from_paths(self, paths: List[str] = None) -> Dict:
        """
        Build dependency graph by scanning integration paths
        
        Args:
            paths: List of paths to scan for integrations. If None, uses defaults.
            
        Returns:
            Dict containing the dependency graph and analysis
        """
        if paths is None:
            paths = self.CORE_INTEGRATION_PATHS
        
        # Expand glob patterns in paths
        expanded_paths = []
        unmatched_patterns = []
        for path in paths:
            if '*' in path:
                # Expand glob pattern
                matches = glob.glob(path)
                if matches:
                    expanded_paths.extend(matches)
                else:
                    # Track patterns that didn't match anything
                    unmatched_patterns.append(path)
            else:
                expanded_paths.append(path)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in expanded_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        
        paths = unique_paths
            
        logger.info("=" * 70)
        logger.info("BUILDING DEPENDENCY GRAPH")
        logger.info("=" * 70)
        logger.info(f"Checking {len(paths)} potential integration path(s)...")
        
        # Track which paths exist and which don't
        existing_paths = []
        empty_paths = []  # Paths that exist but contain no integrations
        non_existent_paths = []  # Paths that don't exist
        
        # Scan all paths for integrations
        for path in paths:
            if os.path.exists(path):
                # Count manifests before scanning
                manifest_count = self._count_manifests(path)
                if manifest_count > 0:
                    existing_paths.append(path)
                    logger.info(f"✓ Found path: {path}")
                    logger.info(f"  ({manifest_count} integration manifests detected)")
                    self._scan_integration_path(path)
                else:
                    empty_paths.append(path)
                    logger.debug(f"  Path exists but contains no integrations: {path}")
            else:
                non_existent_paths.append(path)
                logger.debug(f"✗ Path does not exist: {path}")
        
        # Log summary of path scanning
        if (empty_paths or non_existent_paths or unmatched_patterns) and not existing_paths:
            logger.warning("=" * 70)
            logger.warning("⚠️  NO INTEGRATION PATHS FOUND!")
            logger.warning("=" * 70)
            total_checked = len(paths) + len(unmatched_patterns)
            logger.warning(f"Checked {total_checked} path(s)/pattern(s), none contain integrations:")
            
            # Log non-existent paths
            if non_existent_paths:
                logger.warning("")
                logger.warning("  Paths that don't exist:")
                for path in non_existent_paths[:self.MAX_PATHS_TO_DISPLAY]:
                    logger.warning(f"    ✗ {path}")
                if len(non_existent_paths) > self.MAX_PATHS_TO_DISPLAY:
                    logger.warning(f"    ... and {len(non_existent_paths) - self.MAX_PATHS_TO_DISPLAY} more")
            
            # Log empty paths
            if empty_paths:
                logger.warning("")
                logger.warning("  Paths that exist but are empty:")
                for path in empty_paths[:self.MAX_PATHS_TO_DISPLAY]:
                    logger.warning(f"    ○ {path}")
                if len(empty_paths) > self.MAX_PATHS_TO_DISPLAY:
                    logger.warning(f"    ... and {len(empty_paths) - self.MAX_PATHS_TO_DISPLAY} more")
            
            # Log unmatched glob patterns
            if unmatched_patterns:
                logger.warning("")
                logger.warning("  Glob patterns that didn't match anything:")
                for pattern in unmatched_patterns[:self.MAX_PATHS_TO_DISPLAY]:
                    logger.warning(f"    ~ {pattern}")
                if len(unmatched_patterns) > self.MAX_PATHS_TO_DISPLAY:
                    logger.warning(f"    ... and {len(unmatched_patterns) - self.MAX_PATHS_TO_DISPLAY} more")
            logger.warning("")
            logger.warning("This means the dependency graph will be EMPTY and the WebUI")
            logger.warning("will show 'No integrations found' or stay on 'Loading...'")
            logger.warning("")
            logger.warning("IMPORTANT:")
            logger.warning("  The add-on runs in a separate container and needs explicit")
            logger.warning("  permission to access Home Assistant's integration directories.")
            logger.warning("")
            logger.warning("SOLUTION:")
            logger.warning("  The add-on should have access via the 'map' configuration,")
            logger.warning("  but if paths are not found:")
            logger.warning("  1. Restart the add-on to apply the latest configuration")
            logger.warning("  2. If still not working, set 'custom_integration_paths' manually:")
            logger.warning("     - Go to Settings → Add-ons → Home Assistant Sentry → Configuration")
            logger.warning("     - Add custom_integration_paths (see logs for suggestions)")
            logger.warning("     - Restart the add-on")
            logger.warning("")
            logger.warning("NOTE:")
            logger.warning("  Core/built-in integrations cannot be scanned (they're in the HA")
            logger.warning("  container). Only custom integrations (HACS) can be analyzed.")
            logger.warning("")
            
            # Try to find alternative paths and suggest them
            logger.warning("Searching for alternative paths...")
            self._suggest_alternative_paths(non_existent_paths)
            logger.warning("=" * 70)
        elif existing_paths:
            logger.info(f"✓ Successfully found {len(existing_paths)} path(s) with integrations")
            if empty_paths or non_existent_paths:
                skipped_count = len(empty_paths) + len(non_existent_paths)
                logger.debug(f"  (Skipped {skipped_count} paths that don't exist or are empty)")
        
        # Build the dependency map
        self._build_dependency_map()
        
        # Generate the graph structure
        graph_data = self._generate_graph_structure()
        
        # Log final summary
        integration_count = len(self.integrations)
        dependency_count = len(self.dependency_map)
        
        if integration_count == 0:
            logger.warning("=" * 70)
            logger.warning("⚠️  DEPENDENCY GRAPH IS EMPTY!")
            logger.warning("=" * 70)
            logger.warning("The graph was built but contains 0 integrations.")
            logger.warning("This will cause the WebUI to show 'No integrations found'")
            logger.warning("")
            logger.warning("Possible causes:")
            logger.warning("  1. Integration paths are incorrect or inaccessible")
            logger.warning("  2. No integrations are installed (unlikely)")
            logger.warning("  3. Permission denied to read integration directories")
            logger.warning("")
            logger.warning("Check the path scanning logs above for details.")
            logger.warning("=" * 70)
        else:
            logger.info("=" * 70)
            logger.info("✅ DEPENDENCY GRAPH BUILD COMPLETE")
            logger.info("=" * 70)
            logger.info(f"  Total integrations: {integration_count}")
            logger.info(f"  Unique dependencies: {dependency_count}")
            # Show sample of what was found
            sample_domains = list(self.integrations.keys())[:self.MAX_PATHS_TO_DISPLAY]
            logger.info(f"  Sample integrations: {', '.join(sample_domains)}")
            if integration_count > self.MAX_PATHS_TO_DISPLAY:
                logger.info(f"  ... and {integration_count - self.MAX_PATHS_TO_DISPLAY} more")
            logger.info("=" * 70)
        
        return graph_data
    
    def _scan_integration_path(self, base_path: str):
        """
        Scan a path for integration directories and parse their manifests
        
        Args:
            base_path: Path to scan for integrations
        """
        try:
            path = Path(base_path)
            if not path.exists():
                return
                
            # Each subdirectory is potentially an integration
            for integration_dir in path.iterdir():
                if not integration_dir.is_dir():
                    continue
                    
                manifest_path = integration_dir / 'manifest.json'
                if manifest_path.exists():
                    self._parse_manifest(manifest_path, integration_dir.name)
                    
        except Exception as e:
            logger.warning(f"Error scanning path {base_path}: {e}")
    
    def _suggest_alternative_paths(self, missing_paths: List[str]):
        """
        Suggest alternative paths when default paths are missing
        
        Args:
            missing_paths: List of paths that don't exist
        """
        # Common alternative locations to check
        alternative_checks = [
            '/config',
            '/homeassistant',
            '/usr/share/hassio/homeassistant',
            '/usr/src',
            '/usr/local',
            '/data',
        ]
        
        found_alternatives = []
        
        for base_path in alternative_checks:
            if os.path.exists(base_path):
                try:
                    # List subdirectories to help identify integration paths
                    subdirs = [d for d in os.listdir(base_path) 
                              if os.path.isdir(os.path.join(base_path, d))]
                    
                    # Look for directories that might contain integrations
                    for subdir in subdirs:
                        full_path = os.path.join(base_path, subdir)
                        
                        # Check if it looks like an integration directory
                        # For 'homeassistant' directories, prefer the components subdirectory
                        if subdir == 'homeassistant':
                            ha_components = os.path.join(full_path, 'components')
                            if os.path.exists(ha_components):
                                manifest_count = self._count_manifests(ha_components)
                                if manifest_count > 0:
                                    found_alternatives.append(f"{ha_components} ({manifest_count} integrations)")
                            # Only add the parent if components subdirectory doesn't exist
                            elif self._count_manifests(full_path) > 0:
                                manifest_count = self._count_manifests(full_path)
                                found_alternatives.append(f"{full_path} ({manifest_count} integrations)")
                        elif subdir in ['custom_components', 'components']:
                            manifest_count = self._count_manifests(full_path)
                            if manifest_count > 0:
                                found_alternatives.append(f"{full_path} ({manifest_count} integrations)")
                                    
                except (PermissionError, OSError) as e:
                    logger.debug(f"Cannot access {base_path}: {e}")
                    
        if found_alternatives:
            logger.warning("✓ FOUND ALTERNATIVE INTEGRATION PATHS:")
            for alt_path in found_alternatives:
                logger.warning(f"  → {alt_path}")
            logger.warning("")
            logger.warning("TO USE THESE PATHS:")
            logger.warning("  1. Go to Settings → Add-ons → Home Assistant Sentry → Configuration")
            logger.warning("  2. Add 'custom_integration_paths' with these values:")
            logger.warning("     custom_integration_paths:")
            for alt_path in found_alternatives:
                # Extract just the path (remove the count)
                path_only = alt_path.split(' (')[0]
                logger.warning(f"       - {path_only}")
            logger.warning("  3. Save and restart the add-on")
        else:
            logger.warning("✗ No alternative integration paths found in common locations")
            logger.warning("  The add-on may be running in an unusual environment")
            logger.warning("  or Home Assistant may not be installed yet.")
    
    def _count_manifests(self, path: str) -> int:
        """
        Count manifest.json files in subdirectories of a path
        
        Args:
            path: Path to check
            
        Returns:
            Number of manifest.json files found
        """
        try:
            count = 0
            path_obj = Path(path)
            if path_obj.exists():
                for item in path_obj.iterdir():
                    if item.is_dir():
                        manifest = item / 'manifest.json'
                        if manifest.exists():
                            count += 1
            return count
        except Exception:
            return 0
    
    def _parse_manifest(self, manifest_path: Path, integration_name: str):
        """
        Parse a manifest.json file and extract dependency information
        
        Args:
            manifest_path: Path to manifest.json
            integration_name: Name of the integration
        """
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Extract relevant fields
            requirements = manifest.get('requirements', [])
            homeassistant = manifest.get('homeassistant')
            version = manifest.get('version')
            domain = manifest.get('domain', integration_name)
            name = manifest.get('name', integration_name)
            
            # Parse requirements into structured format
            parsed_requirements = self._parse_requirements(requirements)
            
            # Store integration data
            self.integrations[domain] = {
                'name': name,
                'domain': domain,
                'version': version,
                'homeassistant': homeassistant,
                'requirements': parsed_requirements,
                'raw_requirements': requirements,
                'manifest_path': str(manifest_path)
            }
            
            logger.debug(f"Parsed manifest for {name}: {len(requirements)} requirements")
            
        except json.JSONDecodeError as e:
            logger.warning(f"Malformed manifest.json at {manifest_path}: {e}")
            # Gracefully handle - store with error flag
            self.integrations[integration_name] = {
                'name': integration_name,
                'domain': integration_name,
                'error': 'malformed_json',
                'manifest_path': str(manifest_path)
            }
        except Exception as e:
            logger.warning(f"Error parsing manifest at {manifest_path}: {e}")
            self.integrations[integration_name] = {
                'name': integration_name,
                'domain': integration_name,
                'error': str(e),
                'manifest_path': str(manifest_path)
            }
    
    def _parse_requirements(self, requirements: List[str]) -> List[Dict]:
        """
        Parse requirement strings into structured format
        
        Args:
            requirements: List of requirement strings (e.g., "aiohttp>=3.9.0")
            
        Returns:
            List of dicts with package name and version specifiers
        """
        parsed = []
        
        for req_string in requirements:
            try:
                req = Requirement(req_string)
                parsed.append({
                    'package': req.name.lower(),
                    'specifier': str(req.specifier) if req.specifier else 'any',
                    'raw': req_string,
                    'high_risk': req.name.lower() in self.HIGH_RISK_LIBRARIES
                })
            except InvalidRequirement as e:
                logger.debug(f"Invalid requirement format: {req_string}: {e}")
                # Try simple parsing as fallback
                match = re.match(r'^([a-zA-Z0-9_-]+)', req_string)
                if match:
                    package = match.group(1).lower()
                    parsed.append({
                        'package': package,
                        'specifier': 'unknown',
                        'raw': req_string,
                        'high_risk': package in self.HIGH_RISK_LIBRARIES,
                        'parse_error': str(e)
                    })
                    
        return parsed
    
    def _build_dependency_map(self):
        """Build a map of dependencies to integrations that use them"""
        self.dependency_map = {}
        
        for domain, integration in self.integrations.items():
            if 'error' in integration:
                continue
                
            for req in integration.get('requirements', []):
                package = req['package']
                if package not in self.dependency_map:
                    self.dependency_map[package] = []
                    
                self.dependency_map[package].append({
                    'integration': integration['name'],
                    'domain': domain,
                    'specifier': req['specifier'],
                    'high_risk': req.get('high_risk', False)
                })
    
    def _generate_graph_structure(self) -> Dict:
        """
        Generate the final graph structure with both machine-readable and human-readable formats
        
        Returns:
            Dict with 'integrations', 'dependencies', 'summary', and 'json' keys
        """
        # Machine-readable: full data structure
        machine_readable = {
            'integrations': self.integrations,
            'dependency_map': self.dependency_map,
            'statistics': {
                'total_integrations': len(self.integrations),
                'total_dependencies': len(self.dependency_map),
                'integrations_with_errors': len([i for i in self.integrations.values() if 'error' in i]),
                'high_risk_dependencies': len([d for d in self.dependency_map.keys() if d in self.HIGH_RISK_LIBRARIES])
            }
        }
        
        # Human-readable: formatted text
        human_readable = self._generate_human_readable_summary()
        
        return {
            'machine_readable': machine_readable,
            'human_readable': human_readable,
            'integrations': self.integrations,
            'dependency_map': self.dependency_map
        }
    
    def _generate_human_readable_summary(self) -> str:
        """Generate a human-readable summary of the dependency graph"""
        lines = []
        lines.append("=" * 60)
        lines.append("DEPENDENCY GRAPH SUMMARY")
        lines.append("=" * 60)
        lines.append("")
        
        # Statistics
        total_integrations = len(self.integrations)
        total_deps = len(self.dependency_map)
        errors = len([i for i in self.integrations.values() if 'error' in i])
        
        lines.append(f"Total Integrations: {total_integrations}")
        lines.append(f"Unique Dependencies: {total_deps}")
        if errors > 0:
            lines.append(f"Integrations with Parse Errors: {errors}")
        lines.append("")
        
        # High-risk dependencies
        high_risk = {pkg: users for pkg, users in self.dependency_map.items() 
                    if pkg in self.HIGH_RISK_LIBRARIES}
        
        if high_risk:
            lines.append("HIGH-RISK DEPENDENCIES:")
            lines.append("-" * 60)
            for pkg, users in sorted(high_risk.items(), key=lambda x: len(x[1]), reverse=True):
                lines.append(f"  {pkg}: used by {len(users)} integration(s)")
                for user in users[:3]:  # Show first 3
                    lines.append(f"    └─ {user['integration']} ({user['specifier']})")
                if len(users) > 3:
                    lines.append(f"    └─ ... and {len(users) - 3} more")
            lines.append("")
        
        # Top dependencies by usage
        top_deps = sorted(self.dependency_map.items(), 
                         key=lambda x: len(x[1]), reverse=True)[:10]
        
        if top_deps:
            lines.append("TOP 10 MOST-USED DEPENDENCIES:")
            lines.append("-" * 60)
            for pkg, users in top_deps:
                risk_indicator = " ⚠️ HIGH RISK" if pkg in self.HIGH_RISK_LIBRARIES else ""
                lines.append(f"  {pkg}: {len(users)} integration(s){risk_indicator}")
            lines.append("")
        
        # Sample integration tree (show first 5)
        lines.append("SAMPLE INTEGRATION DEPENDENCIES:")
        lines.append("-" * 60)
        sample_count = 0
        for domain, integration in self.integrations.items():
            if 'error' in integration:
                continue
            if sample_count >= 5:
                break
                
            requirements = integration.get('requirements', [])
            if requirements:
                lines.append(f"{integration['name']}:")
                for req in requirements:
                    risk = " ⚠️" if req.get('high_risk') else ""
                    lines.append(f"  ├─ {req['package']} {req['specifier']}{risk}")
                lines.append("")
                sample_count += 1
        
        if sample_count < len(self.integrations):
            lines.append(f"... and {len(self.integrations) - sample_count} more integrations")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def get_shared_dependencies(self) -> List[Dict]:
        """
        Get dependencies that are shared by multiple integrations
        
        Returns:
            List of dicts with dependency info and conflict details
        """
        shared = []
        
        for package, users in self.dependency_map.items():
            if len(users) > 1:
                # Check for version conflicts
                specifiers = [u['specifier'] for u in users if u['specifier'] != 'any']
                has_conflict = len(set(specifiers)) > 1
                
                shared.append({
                    'package': package,
                    'user_count': len(users),
                    'users': users,
                    'high_risk': package in self.HIGH_RISK_LIBRARIES,
                    'has_version_conflict': has_conflict,
                    'specifiers': list(set(specifiers))
                })
        
        # Sort by user count (most shared first)
        shared.sort(key=lambda x: x['user_count'], reverse=True)
        
        return shared
    
    def detect_version_conflicts(self) -> List[Dict]:
        """
        Detect potential version conflicts in shared dependencies
        
        Returns:
            List of conflicts with details
        """
        conflicts = []
        
        for package, users in self.dependency_map.items():
            if len(users) <= 1:
                continue
            
            # Group by specifier
            specifier_groups = {}
            for user in users:
                spec = user['specifier']
                if spec not in specifier_groups:
                    specifier_groups[spec] = []
                specifier_groups[spec].append(user)
            
            # If more than one unique specifier, potential conflict
            if len(specifier_groups) > 1:
                conflicts.append({
                    'package': package,
                    'high_risk': package in self.HIGH_RISK_LIBRARIES,
                    'conflict_type': 'version_constraint_mismatch',
                    'specifier_groups': specifier_groups,
                    'affected_integrations': [u['integration'] for u in users]
                })
        
        return conflicts
