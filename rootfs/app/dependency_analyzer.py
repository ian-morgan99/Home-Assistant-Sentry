"""
Deep Dependency Analysis without AI
Analyzes update conflicts using version parsing and heuristic rules
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from packaging import version

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Performs deep dependency analysis without AI"""
    
    # Known problematic combinations
    CONFLICT_PATTERNS = {
        'mariadb': {
            'major_version_change': True,
            'affected_addons': ['homeassistant', 'influxdb', 'grafana'],
            'warning': 'Database schema changes may require migration'
        },
        'postgresql': {
            'major_version_change': True,
            'affected_addons': ['homeassistant', 'grafana', 'pgadmin'],
            'warning': 'PostgreSQL major upgrades require data migration'
        },
        'mosquitto': {
            'major_version_change': True,
            'affected_addons': ['zigbee2mqtt', 'zwave', 'node-red'],
            'warning': 'MQTT broker changes may affect IoT devices'
        },
        'node-red': {
            'major_version_change': True,
            'affected_addons': [],
            'warning': 'Node-RED major updates may break custom flows'
        }
    }
    
    # Core integrations that often conflict
    CORE_INTEGRATIONS = [
        'homeassistant', 'hacs', 'esphome', 'zigbee2mqtt', 'zwavejs'
    ]
    
    def __init__(self):
        """Initialize the analyzer"""
        pass
    
    def analyze_updates(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """
        Perform deep dependency analysis on updates
        
        Returns:
            Dict with keys: safe, confidence, issues, recommendations, summary
        """
        issues = []
        recommendations = []
        total_updates = len(addon_updates) + len(hacs_updates)
        
        # 1. Check update volume
        volume_issues = self._check_update_volume(total_updates)
        issues.extend(volume_issues['issues'])
        recommendations.extend(volume_issues['recommendations'])
        
        # 2. Analyze add-on version changes
        addon_issues = self._analyze_addon_updates(addon_updates)
        issues.extend(addon_issues['issues'])
        recommendations.extend(addon_issues['recommendations'])
        
        # 3. Check for simultaneous critical updates
        simultaneous_issues = self._check_simultaneous_critical_updates(addon_updates)
        issues.extend(simultaneous_issues['issues'])
        recommendations.extend(simultaneous_issues['recommendations'])
        
        # 4. Analyze HACS updates for known conflicts
        hacs_issues = self._analyze_hacs_updates(hacs_updates)
        issues.extend(hacs_issues['issues'])
        recommendations.extend(hacs_issues['recommendations'])
        
        # 5. Check for breaking changes based on version jumps
        breaking_issues = self._check_breaking_changes(addon_updates, hacs_updates)
        issues.extend(breaking_issues['issues'])
        recommendations.extend(breaking_issues['recommendations'])
        
        # Determine overall safety
        critical_count = len([i for i in issues if i['severity'] == 'critical'])
        high_count = len([i for i in issues if i['severity'] == 'high'])
        medium_count = len([i for i in issues if i['severity'] == 'medium'])
        
        # Calculate confidence based on analysis depth
        confidence = self._calculate_confidence(issues, total_updates)
        
        # Determine if safe to update
        safe = critical_count == 0 and high_count == 0
        
        # Generate summary
        summary = self._generate_summary(total_updates, issues, safe)
        
        # Add general recommendations if none exist
        if not recommendations:
            recommendations.append('No specific concerns detected. Updates appear safe to install.')
            recommendations.append('Always backup your system before major updates.')
        
        return {
            'safe': safe,
            'confidence': confidence,
            'issues': issues,
            'recommendations': list(set(recommendations)),  # Remove duplicates
            'summary': summary,
            'ai_analysis': False
        }
    
    def _check_update_volume(self, total_updates: int) -> Dict:
        """Check if too many updates at once"""
        issues = []
        recommendations = []
        
        if total_updates > 15:
            issues.append({
                'severity': 'high',
                'component': 'update_volume',
                'description': f'Very large number of updates ({total_updates}) available',
                'impact': 'High risk of multiple breaking changes and difficult troubleshooting'
            })
            recommendations.append('Install updates in smaller batches (5-10 at a time)')
            recommendations.append('Test system functionality between batches')
        elif total_updates > 10:
            issues.append({
                'severity': 'medium',
                'component': 'update_volume',
                'description': f'Large number of updates ({total_updates}) available',
                'impact': 'Installing many updates at once may complicate troubleshooting'
            })
            recommendations.append('Consider installing updates in smaller batches')
        
        return {'issues': issues, 'recommendations': recommendations}
    
    def _analyze_addon_updates(self, addon_updates: List[Dict]) -> Dict:
        """Analyze add-on updates for conflicts"""
        issues = []
        recommendations = []
        
        for addon in addon_updates:
            addon_slug = addon.get('slug', '').lower()
            current_ver = addon.get('current_version', '')
            latest_ver = addon.get('latest_version', '')
            
            # Check if this is a known critical addon
            for pattern_key, pattern_info in self.CONFLICT_PATTERNS.items():
                if pattern_key in addon_slug:
                    # Check for major version change
                    if pattern_info.get('major_version_change'):
                        is_major_change = self._is_major_version_change(current_ver, latest_ver)
                        
                        if is_major_change:
                            issues.append({
                                'severity': 'high',
                                'component': addon['name'],
                                'description': f"Major version update: {current_ver} → {latest_ver}",
                                'impact': pattern_info['warning']
                            })
                            recommendations.append(f"Backup before updating {addon['name']}")
                            recommendations.append(f"Review {addon['name']} changelog for breaking changes")
                            recommendations.append(f"Plan for potential downtime with {addon['name']}")
                            
                            # Check for affected add-ons
                            if pattern_info.get('affected_addons'):
                                affected = ', '.join(pattern_info['affected_addons'])
                                recommendations.append(
                                    f"Check compatibility with: {affected}"
                                )
                        else:
                            # Minor update to critical service
                            issues.append({
                                'severity': 'medium',
                                'component': addon['name'],
                                'description': f"Core service update: {current_ver} → {latest_ver}",
                                'impact': 'May require dependent service restarts'
                            })
                            recommendations.append(f"Monitor {addon['name']} after update")
        
        return {'issues': issues, 'recommendations': recommendations}
    
    def _check_simultaneous_critical_updates(self, addon_updates: List[Dict]) -> Dict:
        """Check if multiple critical services are updating at once"""
        issues = []
        recommendations = []
        
        critical_updates = []
        for addon in addon_updates:
            addon_slug = addon.get('slug', '').lower()
            for pattern_key in self.CONFLICT_PATTERNS.keys():
                if pattern_key in addon_slug:
                    critical_updates.append(addon['name'])
                    break
        
        if len(critical_updates) >= 2:
            issues.append({
                'severity': 'high',
                'component': 'multiple_critical_updates',
                'description': f"Multiple critical services updating: {', '.join(critical_updates)}",
                'impact': 'Simultaneous updates increase risk of cascading failures'
            })
            recommendations.append('Update critical services one at a time')
            recommendations.append('Verify each service is working before updating the next')
        
        return {'issues': issues, 'recommendations': recommendations}
    
    def _analyze_hacs_updates(self, hacs_updates: List[Dict]) -> Dict:
        """Analyze HACS integration updates"""
        issues = []
        recommendations = []
        
        # HACS integrations share the Home Assistant Python environment
        # Multiple updates increase risk of dependency conflicts
        if len(hacs_updates) > 5:
            issues.append({
                'severity': 'medium',
                'component': 'hacs_updates',
                'description': f'{len(hacs_updates)} HACS integrations have updates',
                'impact': 'Multiple custom integrations updating may have dependency conflicts'
            })
            recommendations.append('Update HACS integrations one at a time')
            recommendations.append('Check Home Assistant logs for Python dependency warnings')
        
        # Check for major version updates in HACS
        for hacs in hacs_updates:
            current_ver = hacs.get('current_version', '')
            latest_ver = hacs.get('latest_version', '')
            
            if self._is_major_version_change(current_ver, latest_ver):
                issues.append({
                    'severity': 'medium',
                    'component': hacs['name'],
                    'description': f"Major HACS update: {current_ver} → {latest_ver}",
                    'impact': 'Breaking changes may affect automations or dashboards'
                })
                recommendations.append(f"Review {hacs['name']} release notes before updating")
        
        return {'issues': issues, 'recommendations': recommendations}
    
    def _check_breaking_changes(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """Check for potential breaking changes based on version patterns"""
        issues = []
        recommendations = []
        
        all_updates = [
            {'type': 'addon', **addon} for addon in addon_updates
        ] + [
            {'type': 'hacs', **hacs} for hacs in hacs_updates
        ]
        
        breaking_count = 0
        for update in all_updates:
            current = update.get('current_version', '')
            latest = update.get('latest_version', '')
            
            # Check for pre-release versions (alpha, beta, rc)
            if self._is_prerelease(latest):
                issues.append({
                    'severity': 'high',
                    'component': update['name'],
                    'description': f"Pre-release version: {latest}",
                    'impact': 'Beta/RC versions may be unstable'
                })
                recommendations.append(f"Wait for stable release of {update['name']}")
                breaking_count += 1
            
            # Check for version jumps (multiple major versions)
            jump_size = self._get_version_jump_size(current, latest)
            if jump_size >= 2:
                issues.append({
                    'severity': 'medium',
                    'component': update['name'],
                    'description': f"Large version jump: {current} → {latest}",
                    'impact': 'Skipping versions may miss important migration steps'
                })
                recommendations.append(f"Check if {update['name']} requires incremental updates")
                breaking_count += 1
        
        return {'issues': issues, 'recommendations': recommendations}
    
    def _is_major_version_change(self, current: str, latest: str) -> bool:
        """Check if version change is a major version bump"""
        try:
            current_parsed = version.parse(current)
            latest_parsed = version.parse(latest)
            
            # Extract major version numbers
            if hasattr(current_parsed, 'major') and hasattr(latest_parsed, 'major'):
                return latest_parsed.major > current_parsed.major
            
            # Fallback to simple comparison
            current_major = int(current.split('.')[0]) if '.' in current else 0
            latest_major = int(latest.split('.')[0]) if '.' in latest else 0
            return latest_major > current_major
        except Exception as e:
            logger.debug(f"Version comparison failed: {e}")
            return False
    
    def _is_prerelease(self, version_str: str) -> bool:
        """Check if version is a pre-release"""
        prerelease_patterns = ['alpha', 'beta', 'rc', 'dev', 'pre']
        version_lower = version_str.lower()
        return any(pattern in version_lower for pattern in prerelease_patterns)
    
    def _get_version_jump_size(self, current: str, latest: str) -> int:
        """Calculate how many major versions are being jumped"""
        try:
            current_parsed = version.parse(current)
            latest_parsed = version.parse(latest)
            
            if hasattr(current_parsed, 'major') and hasattr(latest_parsed, 'major'):
                return latest_parsed.major - current_parsed.major
            
            # Fallback
            current_major = int(current.split('.')[0]) if '.' in current else 0
            latest_major = int(latest.split('.')[0]) if '.' in latest else 0
            return latest_major - current_major
        except Exception:
            return 0
    
    def _calculate_confidence(self, issues: List[Dict], total_updates: int) -> float:
        """Calculate confidence score based on analysis depth"""
        # Base confidence for heuristic analysis
        base_confidence = 0.65
        
        # Increase confidence if we found specific issues
        if len(issues) > 0:
            base_confidence += 0.05
        
        # Decrease confidence for large update sets (harder to analyze)
        if total_updates > 10:
            base_confidence -= 0.05
        
        # Cap between 0.5 and 0.75 (never as confident as AI)
        return max(0.5, min(0.75, base_confidence))
    
    def _generate_summary(self, total_updates: int, issues: List[Dict], safe: bool) -> str:
        """Generate analysis summary"""
        critical = len([i for i in issues if i['severity'] == 'critical'])
        high = len([i for i in issues if i['severity'] == 'high'])
        medium = len([i for i in issues if i['severity'] == 'medium'])
        
        summary = f"Deep analysis: {total_updates} updates available. "
        
        if safe:
            if medium > 0:
                summary += f"Safe to proceed with caution. {medium} medium-priority items to review."
            else:
                summary += "Safe to proceed."
        else:
            summary += f"Review required: {critical} critical, {high} high-priority issues detected."
        
        return summary
