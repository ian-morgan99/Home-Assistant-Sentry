"""
Log Monitor for Home Assistant Sentry

Monitors Home Assistant logs for errors after component updates.
Compares logs between checks to identify new error messages.
Supports both heuristic and AI-powered analysis.
"""
import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from log_obfuscator import LogObfuscator

logger = logging.getLogger(__name__)


class LogMonitor:
    """Monitors Home Assistant logs for errors after updates"""
    
    # Pattern to identify error/warning log lines
    ERROR_PATTERN = re.compile(r'(ERROR|WARNING|CRITICAL|FATAL)', re.IGNORECASE)
    
    # Maximum number of log lines to send to AI for analysis
    MAX_LOGS_FOR_AI_ANALYSIS = 50
    
    # Common error patterns that indicate significant issues
    SIGNIFICANT_ERROR_PATTERNS = [
        r'integration .* could not be set up',
        r'setup of .* is taking',
        r'error setting up',
        r'error during setup',
        r'failed to (load|start|initialize)',
        r'exception in',
        r'unexpected error',
        r'cannot import',
        r'no module named',
        r'dependency.*not found',
        r'version conflict',
        r'deprecated',
        r'breaking change',
    ]
    
    # Log storage files
    PREVIOUS_LOGS_FILE = '/data/previous_logs.json'
    BASELINE_LOGS_FILE = '/data/baseline_logs.json'  # Long-term baseline for comparison
    
    def __init__(self, config, obfuscator: Optional[LogObfuscator] = None):
        """
        Initialize the log monitor
        
        Args:
            config: Configuration object with monitor_logs_after_update and log_check_lookback_hours
            obfuscator: Optional LogObfuscator for anonymizing logs before AI analysis
        """
        self.config = config
        self.obfuscator = obfuscator or LogObfuscator(enabled=config.obfuscate_logs)
        self.lookback_hours = config.log_check_lookback_hours
    
    async def fetch_logs(self, ha_client) -> List[str]:
        """
        Fetch Home Assistant logs from the Supervisor API
        
        Args:
            ha_client: HomeAssistantClient instance
            
        Returns:
            List of log lines
        """
        try:
            url = f"{self.config.supervisor_url}/core/logs"
            logger.debug(f"Fetching logs from: {url}")
            
            async with ha_client.session.get(url) as response:
                if response.status == 200:
                    # Logs are returned as plain text
                    log_text = await response.text()
                    log_lines = log_text.split('\n')
                    logger.info(f"Fetched {len(log_lines)} log lines from Home Assistant")
                    return log_lines
                else:
                    logger.error(f"Failed to fetch logs: {response.status}")
                    if response.status == 401:
                        logger.error("Authentication failed - check SUPERVISOR_TOKEN")
                    return []
        except Exception as e:
            logger.error(f"Error fetching logs: {e}", exc_info=True)
            return []
    
    def filter_recent_errors(self, log_lines: List[str]) -> List[str]:
        """
        Filter log lines to only include errors/warnings from the lookback period
        
        Args:
            log_lines: All log lines
            
        Returns:
            Filtered list of error/warning log lines
        """
        cutoff_time = datetime.now() - timedelta(hours=self.lookback_hours)
        error_lines = []
        
        for line in log_lines:
            # Check if line contains error/warning
            if not self.ERROR_PATTERN.search(line):
                continue
            
            # Try to extract timestamp from log line
            # Common HA log format: YYYY-MM-DD HH:MM:SS.mmm LEVEL ...
            timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
            if timestamp_match:
                try:
                    log_time = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                    if log_time >= cutoff_time:
                        error_lines.append(line)
                except ValueError:
                    # If timestamp parsing fails, include the line anyway (better safe than sorry)
                    error_lines.append(line)
            else:
                # No timestamp found, include the line
                error_lines.append(line)
        
        logger.info(f"Filtered to {len(error_lines)} error/warning lines from last {self.lookback_hours} hours")
        return error_lines
    
    def extract_error_signature(self, log_line: str) -> str:
        """
        Extract a signature from an error log line for comparison
        
        Removes timestamps, instance-specific details, and other variable data
        to enable comparison between runs.
        
        Args:
            log_line: A single log line
            
        Returns:
            Normalized signature string
        """
        # Remove timestamp
        signature = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(\.\d+)?', '', log_line)
        
        # Remove log level (already filtered, but normalize)
        signature = re.sub(r'(ERROR|WARNING|CRITICAL|FATAL|INFO|DEBUG)', '', signature, flags=re.IGNORECASE)
        
        # Remove common variable parts
        signature = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', '<IP>', signature)  # IP addresses
        signature = re.sub(r'\b[0-9a-f]{8,}\b', '<ID>', signature)  # Hex IDs
        # ISO 8601 timestamps with optional fractional seconds and timezone
        # Home Assistant logs may use various timestamp formats, this pattern handles most variations
        signature = re.sub(r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?\b', '<TIMESTAMP>', signature)
        signature = re.sub(r'\(\d+\.\d+s\)', '(<TIME>)', signature)  # Duration
        
        # Normalize whitespace
        signature = ' '.join(signature.split())
        
        return signature.strip()
    
    def compare_logs(self, current_errors: List[str], previous_errors: List[str]) -> Dict:
        """
        Compare current error logs with previous errors
        
        Args:
            current_errors: Error lines from current check
            previous_errors: Error lines from previous check
            
        Returns:
            Dictionary with comparison results:
                - new_errors: List of new error lines
                - resolved_errors: List of resolved error lines
                - persistent_errors: List of errors that persist
        """
        # Create signature sets for comparison
        current_signatures = {self.extract_error_signature(line): line for line in current_errors}
        previous_signatures = {self.extract_error_signature(line): line for line in previous_errors}
        
        # Find new, resolved, and persistent errors
        new_sigs = set(current_signatures.keys()) - set(previous_signatures.keys())
        resolved_sigs = set(previous_signatures.keys()) - set(current_signatures.keys())
        persistent_sigs = set(current_signatures.keys()) & set(previous_signatures.keys())
        
        new_errors = [current_signatures[sig] for sig in new_sigs]
        resolved_errors = [previous_signatures[sig] for sig in resolved_sigs]
        persistent_errors = [current_signatures[sig] for sig in persistent_sigs]
        
        logger.info(f"Log comparison: {len(new_errors)} new, {len(resolved_errors)} resolved, {len(persistent_errors)} persistent")
        
        return {
            'new_errors': new_errors,
            'resolved_errors': resolved_errors,
            'persistent_errors': persistent_errors,
            'total_current': len(current_errors),
            'total_previous': len(previous_errors)
        }
    
    def save_current_logs(self, error_lines: List[str]):
        """
        Save current error logs to disk for next comparison
        
        Also maintains a baseline snapshot for long-term comparison across HA restarts.
        The baseline is only updated when the system appears stable (fewer errors).
        
        Args:
            error_lines: Current error log lines to save
        """
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'errors': error_lines,
                'lookback_hours': self.lookback_hours
            }
            
            os.makedirs(os.path.dirname(self.PREVIOUS_LOGS_FILE), exist_ok=True)
            
            # Always save current logs
            with open(self.PREVIOUS_LOGS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(error_lines)} error lines to {self.PREVIOUS_LOGS_FILE}")
            
            # Update baseline if this appears to be a stable state
            # Baseline is updated when we have fewer than 20 errors or no previous baseline exists
            baseline_should_update = False
            if not os.path.exists(self.BASELINE_LOGS_FILE):
                baseline_should_update = True
                logger.info("Creating initial baseline log snapshot for future comparisons")
            elif len(error_lines) < 20:
                # System appears stable, update baseline
                baseline_should_update = True
                logger.debug(f"Updating baseline log snapshot (stable state with {len(error_lines)} errors)")
            
            if baseline_should_update:
                with open(self.BASELINE_LOGS_FILE, 'w') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Updated baseline log snapshot with {len(error_lines)} errors")
                
        except Exception as e:
            logger.warning(f"Failed to save logs: {e}")
    
    def load_previous_logs(self) -> List[str]:
        """
        Load previous error logs from disk
        
        Tries to load from previous_logs.json first. If that fails or appears
        to be from after a restart (very few or no errors), falls back to
        baseline_logs.json which persists across HA restarts.
        
        Returns:
            List of previous error log lines, or empty list if none exist
        """
        try:
            # Try loading recent previous logs first
            if os.path.exists(self.PREVIOUS_LOGS_FILE):
                with open(self.PREVIOUS_LOGS_FILE, 'r') as f:
                    data = json.load(f)
                
                previous_errors = data.get('errors', [])
                previous_time = data.get('timestamp', 'unknown')
                
                # If previous logs are empty or very sparse, might indicate HA restart cleared logs
                # Fall back to baseline for better comparison
                if len(previous_errors) > 0:
                    logger.info(f"Loaded {len(previous_errors)} previous error lines from {previous_time}")
                    return previous_errors
                else:
                    logger.info("Previous logs appear empty (possible HA restart), trying baseline logs")
            else:
                logger.debug("No previous logs file found")
            
            # Fall back to baseline logs for comparison across restarts
            if os.path.exists(self.BASELINE_LOGS_FILE):
                with open(self.BASELINE_LOGS_FILE, 'r') as f:
                    data = json.load(f)
                
                baseline_errors = data.get('errors', [])
                baseline_time = data.get('timestamp', 'unknown')
                
                if len(baseline_errors) > 0:
                    logger.info(f"Loaded {len(baseline_errors)} baseline error lines from {baseline_time}")
                    logger.info("Using baseline for comparison (helps detect issues across HA restarts)")
                    return baseline_errors
            
            logger.debug("No baseline logs found - this may be the first run")
            return []
            
        except Exception as e:
            logger.warning(f"Failed to load previous logs: {e}")
            return []
    
    def heuristic_analysis(self, comparison: Dict) -> Dict:
        """
        Perform heuristic analysis on log comparison results
        
        Args:
            comparison: Log comparison results from compare_logs()
            
        Returns:
            Analysis dictionary with:
                - severity: 'none', 'low', 'medium', 'high', 'critical'
                - has_significant_errors: boolean
                - significant_errors: list of significant error lines
                - summary: text summary
                - recommendations: list of recommendation strings
        """
        new_errors = comparison['new_errors']
        resolved_errors = comparison['resolved_errors']
        
        # Check for significant error patterns
        significant_errors = []
        for error_line in new_errors:
            for pattern in self.SIGNIFICANT_ERROR_PATTERNS:
                if re.search(pattern, error_line, re.IGNORECASE):
                    significant_errors.append(error_line)
                    break
        
        # Determine severity
        if len(significant_errors) > 0:
            if len(significant_errors) >= 5:
                severity = 'critical'
            elif len(significant_errors) >= 3:
                severity = 'high'
            else:
                severity = 'medium'
        elif len(new_errors) > 10:
            severity = 'medium'
        elif len(new_errors) > 0:
            severity = 'low'
        else:
            severity = 'none'
        
        # Build summary
        summary_parts = []
        if len(new_errors) == 0 and len(resolved_errors) == 0:
            summary_parts.append("No changes in error logs since last check.")
        else:
            if len(new_errors) > 0:
                summary_parts.append(f"{len(new_errors)} new error/warning messages detected.")
            if len(resolved_errors) > 0:
                summary_parts.append(f"{len(resolved_errors)} previous errors have been resolved.")
            if len(significant_errors) > 0:
                summary_parts.append(f"{len(significant_errors)} errors may require attention.")
        
        summary = ' '.join(summary_parts)
        
        # Build recommendations
        recommendations = []
        if severity in ['critical', 'high']:
            recommendations.append("Review the new error messages immediately.")
            recommendations.append("Check if any integrations or add-ons are failing to load.")
        elif severity == 'medium':
            recommendations.append("Review the new error messages when convenient.")
        
        if len(significant_errors) > 0:
            recommendations.append("Consider reporting issues to component maintainers if errors persist.")
        
        if len(resolved_errors) > 0:
            recommendations.append("Good news: Some previous errors have been resolved.")
        
        return {
            'severity': severity,
            'has_significant_errors': len(significant_errors) > 0,
            'significant_errors': significant_errors[:10],  # Limit to 10 for display
            'summary': summary,
            'recommendations': recommendations,
            'new_error_count': len(new_errors),
            'resolved_error_count': len(resolved_errors)
        }
    
    async def ai_analysis(self, comparison: Dict, ai_client) -> Dict:
        """
        Perform AI-powered analysis on log comparison results
        
        Args:
            comparison: Log comparison results from compare_logs()
            ai_client: AIClient instance for analysis
            
        Returns:
            Analysis dictionary similar to heuristic_analysis() but with AI insights
        """
        try:
            new_errors = comparison['new_errors']
            resolved_errors = comparison['resolved_errors']
            
            if len(new_errors) == 0 and len(resolved_errors) == 0:
                return {
                    'severity': 'none',
                    'has_significant_errors': False,
                    'significant_errors': [],
                    'summary': 'No changes in error logs since last check.',
                    'recommendations': [],
                    'new_error_count': 0,
                    'resolved_error_count': 0,
                    'ai_powered': True
                }
            
            # Anonymize logs before sending to AI (slice first for performance)
            anonymized_new = [self.obfuscator.obfuscate(line) for line in new_errors[:self.MAX_LOGS_FOR_AI_ANALYSIS]]
            anonymized_resolved = [self.obfuscator.obfuscate(line) for line in resolved_errors[:self.MAX_LOGS_FOR_AI_ANALYSIS]]
            
            # Build prompt for AI
            prompt = self._build_ai_prompt(anonymized_new, anonymized_resolved)
            
            # Call AI client
            logger.debug("Requesting AI analysis of log changes")
            response = await ai_client._call_ai(prompt, system_prompt=self._get_system_prompt())
            
            # Parse AI response
            analysis = self._parse_ai_response(response, len(new_errors), len(resolved_errors))
            analysis['ai_powered'] = True
            
            return analysis
            
        except Exception as e:
            logger.warning(f"AI analysis failed, falling back to heuristics: {e}")
            # Fallback to heuristic analysis
            result = self.heuristic_analysis(comparison)
            result['ai_powered'] = False
            return result
    
    def _build_ai_prompt(self, new_errors: List[str], resolved_errors: List[str]) -> str:
        """Build prompt for AI analysis"""
        prompt = "Analyze the following Home Assistant log changes:\n\n"
        
        if new_errors:
            prompt += f"NEW ERRORS/WARNINGS ({len(new_errors)}):\n"
            for i, error in enumerate(new_errors[:20], 1):  # Limit to 20 for context window
                prompt += f"{i}. {error}\n"
            if len(new_errors) > 20:
                prompt += f"... and {len(new_errors) - 20} more\n"
            prompt += "\n"
        
        if resolved_errors:
            prompt += f"RESOLVED ERRORS ({len(resolved_errors)}):\n"
            for i, error in enumerate(resolved_errors[:10], 1):  # Limit to 10
                prompt += f"{i}. {error}\n"
            if len(resolved_errors) > 10:
                prompt += f"... and {len(resolved_errors) - 10} more\n"
            prompt += "\n"
        
        prompt += """Please analyze these log changes and provide:
1. A severity assessment (none/low/medium/high/critical)
2. Identification of any significant errors that require immediate attention
3. A brief summary of the changes
4. Specific recommendations for the user

Format your response as JSON with these fields:
{
  "severity": "none|low|medium|high|critical",
  "significant_errors": ["error1", "error2", ...],
  "summary": "brief summary",
  "recommendations": ["recommendation1", "recommendation2", ...]
}"""
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        return """You are a Home Assistant expert analyzing system logs after component updates.
Your role is to identify errors that may impact system functionality and advise users on appropriate actions.
Focus on integration setup failures, breaking changes, and critical errors that need immediate attention.
Be concise but clear in your recommendations."""
    
    def _parse_ai_response(self, response: str, new_count: int, resolved_count: int) -> Dict:
        """Parse AI response into analysis dictionary"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                return {
                    'severity': data.get('severity', 'low'),
                    'has_significant_errors': len(data.get('significant_errors', [])) > 0,
                    'significant_errors': data.get('significant_errors', [])[:10],
                    'summary': data.get('summary', ''),
                    'recommendations': data.get('recommendations', []),
                    'new_error_count': new_count,
                    'resolved_error_count': resolved_count
                }
            else:
                # AI didn't return JSON, parse as text
                return {
                    'severity': 'medium' if new_count > 0 else 'none',
                    'has_significant_errors': new_count > 0,
                    'significant_errors': [],
                    'summary': response[:500],  # First 500 chars
                    'recommendations': [],
                    'new_error_count': new_count,
                    'resolved_error_count': resolved_count
                }
        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return {
                'severity': 'medium' if new_count > 0 else 'none',
                'has_significant_errors': new_count > 0,
                'significant_errors': [],
                'summary': f"{new_count} new errors detected, {resolved_count} resolved.",
                'recommendations': ['Review the error logs manually.'],
                'new_error_count': new_count,
                'resolved_error_count': resolved_count
            }
    
    async def check_logs(self, ha_client, ai_client=None) -> Optional[Dict]:
        """
        Main method to check logs for errors after updates
        
        This method compares current logs against a baseline to detect new errors.
        The baseline persists across Home Assistant restarts, solving the issue where
        HA clears its logs on restart (which often happens after updates).
        
        Args:
            ha_client: HomeAssistantClient instance
            ai_client: Optional AIClient instance for AI-powered analysis
            
        Returns:
            Analysis dictionary or None if monitoring is disabled
        """
        if not self.config.monitor_logs_after_update:
            logger.debug("Log monitoring is disabled")
            return None
        
        logger.info("=" * 60)
        logger.info("LOG MONITORING CHECK")
        logger.info("=" * 60)
        logger.info("Comparing current logs against baseline to detect new errors")
        logger.info("Note: Baseline persists across HA restarts for accurate comparison")
        
        # Fetch current logs
        log_lines = await self.fetch_logs(ha_client)
        if not log_lines:
            logger.warning("No logs fetched - skipping log check")
            return None
        
        # Filter to recent errors
        current_errors = self.filter_recent_errors(log_lines)
        
        # Load previous errors (will use baseline if needed)
        previous_errors = self.load_previous_logs()
        
        # Enhanced debug logging for maximal log level
        logger.debug("=" * 60)
        logger.debug("LOG COMPARISON DETAILS")
        logger.debug("=" * 60)
        
        # Calculate time ranges for comparison
        current_time = datetime.now()
        lookback_start = current_time - timedelta(hours=self.lookback_hours)
        
        logger.debug(f"Current check time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.debug(f"Lookback period: {self.lookback_hours} hours")
        logger.debug(f"Comparing logs from: {lookback_start.strftime('%Y-%m-%d %H:%M:%S')} to {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.debug(f"Current errors found: {len(current_errors)}")
        logger.debug(f"Previous/baseline errors loaded: {len(previous_errors)}")
        
        # Log whether we can determine changes
        can_determine_changes = len(previous_errors) > 0
        if can_determine_changes:
            logger.debug("Previous log data available - can determine changes")
        else:
            logger.info("=" * 60)
            logger.info("ESTABLISHING BASELINE")
            logger.info("=" * 60)
            logger.info("No previous log data available - this may be first run")
            logger.info("Creating baseline snapshot for future comparisons")
            logger.info("Future checks will compare against this baseline to detect new errors")
            logger.info("=" * 60)
        
        # Log sample of current errors for debugging (maximal level only)
        if current_errors and logger.isEnabledFor(logging.DEBUG):
            logger.debug("Sample of current error entries (up to 5):")
            for i, error in enumerate(current_errors[:5], 1):
                # Truncate long lines for readability
                preview = error[:150] + "..." if len(error) > 150 else error
                logger.debug(f"  {i}. {preview}")
        
        # Log sample of previous errors for debugging (maximal level only)
        if previous_errors and logger.isEnabledFor(logging.DEBUG):
            logger.debug("Sample of previous/baseline error entries (up to 5):")
            for i, error in enumerate(previous_errors[:5], 1):
                # Truncate long lines for readability
                preview = error[:150] + "..." if len(error) > 150 else error
                logger.debug(f"  {i}. {preview}")
        
        logger.debug("=" * 60)
        
        # Compare logs
        comparison = self.compare_logs(current_errors, previous_errors)
        
        # Log comparison results for debugging
        logger.debug(f"Comparison results:")
        logger.debug(f"  New errors: {len(comparison['new_errors'])}")
        logger.debug(f"  Resolved errors: {len(comparison['resolved_errors'])}")
        logger.debug(f"  Persistent errors: {len(comparison['persistent_errors'])}")
        
        # Analyze results
        if ai_client and self.config.ai_enabled:
            logger.info("Performing AI-powered log analysis")
            analysis = await self.ai_analysis(comparison, ai_client)
        else:
            logger.info("Performing heuristic log analysis")
            analysis = self.heuristic_analysis(comparison)
        
        # Add check timestamp to analysis
        analysis['check_time'] = datetime.now(tz=timezone.utc)
        
        # Add flag to indicate if we can determine changes (for notification logic)
        analysis['can_determine_changes'] = can_determine_changes
        
        # Save current logs for next comparison
        self.save_current_logs(current_errors)
        logger.debug(f"Saved {len(current_errors)} current error entries for next comparison")
        
        logger.info(f"Log analysis complete: severity={analysis['severity']}, new={analysis['new_error_count']}, resolved={analysis['resolved_error_count']}")
        logger.info("=" * 60)
        
        return analysis
