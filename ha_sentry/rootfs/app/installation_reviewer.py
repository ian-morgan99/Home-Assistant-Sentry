"""
Installation Reviewer - Analyzes Home Assistant installation and provides improvement recommendations

This module provides AI-powered and heuristic analysis of a Home Assistant installation,
suggesting optimizations, best practices, and potential improvements.

SAFETY PRINCIPLES:
- Read-only analysis only - never modifies any configuration
- Privacy-preserving - no sensitive data collected or sent to AI
- Advisory only - provides recommendations, user decides what to implement
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class InstallationReviewer:
    """Analyzes Home Assistant installation and provides improvement recommendations"""
    
    def __init__(self, config, ai_client=None, dependency_graph=None):
        """
        Initialize the installation reviewer
        
        Args:
            config: Configuration object
            ai_client: Optional AI client for enhanced analysis
            dependency_graph: Optional dependency graph for integration analysis
        """
        self.config = config
        self.ai_client = ai_client
        self.dependency_graph = dependency_graph
    
    async def review_installation(self, installation_summary: Dict) -> Dict:
        """
        Review the Home Assistant installation and provide recommendations
        
        Args:
            installation_summary: Summary of the installation from ha_client.get_installation_summary()
        
        Returns:
            Dict with review results:
            - recommendations: List of improvement suggestions
            - insights: List of interesting observations
            - warnings: List of potential issues
            - summary: Overall summary of the review
            - categories: Recommendations grouped by category
        """
        logger.info("Starting installation review...")
        logger.debug(f"Installation summary: {installation_summary}")
        
        # Use AI if available, otherwise use heuristic analysis
        if self.config.ai_enabled and self.ai_client and self.ai_client.client:
            logger.info("Using AI-powered installation review")
            try:
                return await self._ai_review(installation_summary)
            except Exception as e:
                logger.error(f"AI review failed: {e}", exc_info=True)
                logger.info("Falling back to heuristic analysis")
                return self._heuristic_review(installation_summary)
        else:
            logger.info("Using heuristic installation review")
            return self._heuristic_review(installation_summary)
    
    async def _ai_review(self, installation_summary: Dict) -> Dict:
        """
        Use AI to review the installation and provide recommendations
        
        Args:
            installation_summary: Summary of the installation
        
        Returns:
            Dict with AI-generated recommendations
        """
        logger.debug("Preparing context for AI review")
        
        # Build context for AI
        context = self._build_ai_context(installation_summary)
        
        # Get system prompt for installation review
        system_prompt = self._get_ai_system_prompt()
        
        # Call AI with timeout protection
        logger.info(f"Sending installation review request to AI ({self.config.ai_provider} - {self.config.ai_model})")
        
        def _sync_ai_call():
            logger.debug("Starting synchronous AI API call for installation review")
            try:
                result = self.ai_client.client.chat.completions.create(
                    model=self.config.ai_model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": context
                        }
                    ],
                    temperature=0.7,  # Higher temperature for more creative suggestions
                    max_tokens=3000  # More tokens for comprehensive recommendations
                )
                logger.debug("Synchronous AI API call completed successfully")
                return result
            except Exception as e:
                logger.error(f"Synchronous AI API call failed: {e}")
                raise
        
        # Run in thread pool with async timeout
        try:
            logger.debug("Executing AI call with asyncio.to_thread and 160s timeout")
            response = await asyncio.wait_for(
                asyncio.to_thread(_sync_ai_call),
                timeout=160.0
            )
            logger.debug("AI call completed within timeout")
        except asyncio.TimeoutError:
            logger.error("AI installation review timed out after 160 seconds")
            logger.error(f"AI Provider: {self.config.ai_provider}")
            logger.error(f"AI Endpoint: {self.config.ai_endpoint}")
            logger.error(f"AI Model: {self.config.ai_model}")
            raise
        
        # Parse AI response
        ai_response = response.choices[0].message.content
        logger.info(f"AI review completed: {len(ai_response)} chars")
        logger.debug(f"AI response: {ai_response[:200]}...")
        
        # Parse the structured response
        return self._parse_ai_review_response(ai_response, installation_summary)
    
    def _build_ai_context(self, installation_summary: Dict) -> str:
        """Build context string for AI analysis"""
        context = "# Home Assistant Installation Review Request\n\n"
        
        # Add summary statistics
        context += "## Installation Statistics:\n"
        context += f"- Total Entities: {installation_summary.get('entity_count', 0)}\n"
        context += f"- Devices: {installation_summary.get('device_count', 0)}\n"
        context += f"- Integrations: {installation_summary.get('integration_count', 0)}\n"
        context += f"- Automations: {installation_summary.get('automation_count', 0)}\n"
        context += f"- Scripts: {installation_summary.get('script_count', 0)}\n"
        context += f"- Helpers: {installation_summary.get('helper_count', 0)}\n"
        context += f"- Dashboards: {installation_summary.get('dashboard_count', 0)}\n"
        context += "\n"
        
        # Add entity domain breakdown
        entity_domains = installation_summary.get('entity_domains', {})
        if entity_domains:
            context += "## Entity Breakdown by Domain:\n"
            # Sort by count, descending
            sorted_domains = sorted(entity_domains.items(), key=lambda x: x[1], reverse=True)
            for domain, count in sorted_domains[:20]:  # Top 20 domains
                context += f"- {domain}: {count}\n"
            context += "\n"
        
        # Add device information
        manufacturers = installation_summary.get('manufacturers', {})
        if manufacturers:
            context += "## Device Manufacturers:\n"
            sorted_manufacturers = sorted(manufacturers.items(), key=lambda x: x[1], reverse=True)
            for manufacturer, count in sorted_manufacturers[:15]:  # Top 15 manufacturers
                context += f"- {manufacturer}: {count} devices\n"
            context += "\n"
        
        # Add integration list
        integrations = installation_summary.get('integrations', [])
        if integrations:
            context += f"## Active Integrations ({len(integrations)}):\n"
            for integration in sorted(integrations)[:50]:  # Limit to 50 for context size
                context += f"- {integration}\n"
            if len(integrations) > 50:
                context += f"- ... and {len(integrations) - 50} more\n"
            context += "\n"
        
        # Add dependency graph insights if available
        if self.dependency_graph:
            stats = self.dependency_graph.get('machine_readable', {}).get('statistics', {})
            if stats:
                context += "## Dependency Analysis:\n"
                context += f"- Total Integration Dependencies: {stats.get('total_integrations', 0)}\n"
                context += f"- Unique Python Packages: {stats.get('total_dependencies', 0)}\n"
                context += f"- High-Risk Dependencies: {stats.get('high_risk_dependencies', 0)}\n"
                context += "\n"
        
        context += """
Please analyze this Home Assistant installation and provide:
1. **Recommendations**: Specific improvements to optimize the setup
2. **Insights**: Interesting patterns or observations about the installation
3. **Warnings**: Potential issues or areas of concern
4. **Best Practices**: Suggestions for following Home Assistant best practices

Focus on:
- Integration usage patterns and optimization
- Entity organization and naming
- Automation and script efficiency
- Device integration best practices
- Security and maintenance recommendations
- Performance optimization opportunities

Provide actionable, specific recommendations that the user can implement.
"""
        
        return context
    
    def _get_ai_system_prompt(self) -> str:
        """Get system prompt for AI installation review"""
        return """You are an expert Home Assistant consultant specializing in installation optimization and best practices.

Your task is to review a Home Assistant installation and provide valuable, actionable recommendations for improvement.

Provide your analysis in the following JSON format:
{
  "recommendations": [
    {
      "category": "integration|automation|performance|security|organization|maintenance",
      "priority": "high|medium|low",
      "title": "Brief title",
      "description": "Detailed recommendation",
      "rationale": "Why this matters"
    }
  ],
  "insights": [
    "Interesting observation 1",
    "Interesting observation 2"
  ],
  "warnings": [
    {
      "severity": "high|medium|low",
      "description": "Potential issue description"
    }
  ],
  "summary": "Overall summary of the installation review"
}

Be specific, practical, and focus on improvements that will genuinely benefit the user.
Avoid generic advice - tailor recommendations to the actual installation data provided."""
    
    def _parse_ai_review_response(self, ai_response: str, installation_summary: Dict) -> Dict:
        """Parse AI review response into structured format"""
        try:
            logger.debug("Parsing AI review response")
            # Try to extract JSON from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate and normalize the response
                review = {
                    'recommendations': result.get('recommendations', []),
                    'insights': result.get('insights', []),
                    'warnings': result.get('warnings', []),
                    'summary': result.get('summary', 'Review completed'),
                    'ai_powered': True,
                    'timestamp': datetime.now().isoformat(),
                    'scope': installation_summary.get('scope', 'full')
                }
                
                # Group recommendations by category
                categories = {}
                for rec in review['recommendations']:
                    category = rec.get('category', 'general')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(rec)
                review['categories'] = categories
                
                logger.debug(f"Successfully parsed AI review: {len(review['recommendations'])} recommendations")
                return review
            else:
                # If no JSON found, create a structured response from the text
                logger.warning("No JSON found in AI review response, parsing as text")
                return {
                    'recommendations': [
                        {
                            'category': 'general',
                            'priority': 'medium',
                            'title': 'AI Review',
                            'description': ai_response[:500],
                            'rationale': 'AI-generated review'
                        }
                    ],
                    'insights': [],
                    'warnings': [],
                    'summary': ai_response[:200],
                    'ai_powered': True,
                    'timestamp': datetime.now().isoformat(),
                    'categories': {'general': []},
                    'scope': installation_summary.get('scope', 'full')
                }
        except Exception as e:
            logger.error(f"Failed to parse AI review response: {e}", exc_info=True)
            return self._heuristic_review(installation_summary)
    
    def _heuristic_review(self, installation_summary: Dict) -> Dict:
        """
        Perform heuristic-based installation review without AI
        
        Analyzes installation using rule-based logic and best practices
        """
        logger.info("Performing heuristic installation review")
        
        recommendations = []
        insights = []
        warnings = []
        
        # Analyze entity counts
        entity_count = installation_summary.get('entity_count', 0)
        device_count = installation_summary.get('device_count', 0)
        integration_count = installation_summary.get('integration_count', 0)
        automation_count = installation_summary.get('automation_count', 0)
        
        # Check for large installations
        if entity_count > 1000:
            insights.append(f"Large installation with {entity_count} entities - consider using performance optimization techniques")
            recommendations.append({
                'category': 'performance',
                'priority': 'medium',
                'title': 'Performance Optimization for Large Installation',
                'description': 'With over 1000 entities, consider enabling recorder filtering to improve database performance',
                'rationale': 'Large entity counts can slow down the recorder and history components'
            })
        
        # Check for automation complexity
        if automation_count > 50:
            recommendations.append({
                'category': 'organization',
                'priority': 'low',
                'title': 'Organize Automations',
                'description': f'You have {automation_count} automations. Consider organizing them into packages or using automation blueprints',
                'rationale': 'Organized automations are easier to maintain and troubleshoot'
            })
        elif automation_count < 5 and entity_count > 50:
            insights.append(f"Low automation count ({automation_count}) relative to entities ({entity_count}) - automation opportunities may exist")
        
        # Analyze entity domains
        entity_domains = installation_summary.get('entity_domains', {})
        if entity_domains:
            sensor_count = entity_domains.get('sensor', 0)
            if sensor_count > 500:
                recommendations.append({
                    'category': 'performance',
                    'priority': 'high',
                    'title': 'Recorder Optimization for Sensors',
                    'description': f'You have {sensor_count} sensors. Configure recorder to exclude sensors that don\'t need history',
                    'rationale': 'Recording all sensor data can significantly impact database size and performance'
                })
            
            # Check for helper usage
            helper_count = installation_summary.get('helper_count', 0)
            if helper_count == 0 and automation_count > 10:
                recommendations.append({
                    'category': 'automation',
                    'priority': 'low',
                    'title': 'Consider Using Input Helpers',
                    'description': 'Input helpers (input_boolean, input_number, etc.) can make automations more flexible and easier to manage',
                    'rationale': 'Helpers allow for runtime configuration without editing automations'
                })
        
        # Analyze device diversity
        manufacturers = installation_summary.get('manufacturers', {})
        if len(manufacturers) > 10:
            insights.append(f"Diverse device ecosystem with {len(manufacturers)} different manufacturers")
        
        # Check for dependency graph availability
        if self.dependency_graph:
            stats = self.dependency_graph.get('machine_readable', {}).get('statistics', {})
            high_risk_count = stats.get('high_risk_dependencies', 0)
            if high_risk_count > 5:
                warnings.append({
                    'severity': 'medium',
                    'description': f'{high_risk_count} high-risk Python dependencies detected - keep integrations updated'
                })
        
        # Check for dashboard usage
        dashboard_count = installation_summary.get('dashboard_count', 0)
        if dashboard_count == 0 and entity_count > 20:
            recommendations.append({
                'category': 'organization',
                'priority': 'low',
                'title': 'Create Custom Dashboards',
                'description': 'Consider creating custom dashboards to organize your entities effectively',
                'rationale': 'Custom dashboards provide better organization and user experience than the default view'
            })
        
        # General best practices
        recommendations.append({
            'category': 'maintenance',
            'priority': 'medium',
            'title': 'Regular Backup Schedule',
            'description': 'Ensure you have automated backups configured for your Home Assistant installation',
            'rationale': 'Regular backups protect against data loss and make recovery easier'
        })
        
        recommendations.append({
            'category': 'security',
            'priority': 'high',
            'title': 'Keep System Updated',
            'description': 'Regularly update Home Assistant Core, Supervisor, OS, and all integrations',
            'rationale': 'Updates include security patches and bug fixes that protect your installation'
        })
        
        # Build summary
        summary = f"Installation review complete. Analyzed {entity_count} entities across {integration_count} integrations and {device_count} devices."
        if len(recommendations) > 0:
            summary += f" Found {len(recommendations)} recommendations for improvement."
        
        # Group recommendations by category
        categories = {}
        for rec in recommendations:
            category = rec.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(rec)
        
        return {
            'recommendations': recommendations,
            'insights': insights,
            'warnings': warnings,
            'summary': summary,
            'ai_powered': False,
            'timestamp': datetime.now().isoformat(),
            'scope': installation_summary.get('scope', 'full'),
            'categories': categories
        }
