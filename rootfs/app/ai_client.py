"""
AI Client for analyzing update conflicts
Supports OpenAI-compatible endpoints (OpenAI, LMStudio, OpenWebUI, Ollama)
"""
import logging
import json
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class AIClient:
    """Client for AI-powered conflict analysis"""
    
    def __init__(self, config):
        """Initialize the AI client"""
        self.config = config
        self.client = None
        
        if config.ai_enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client"""
        try:
            # Configure based on provider
            if self.config.ai_provider == 'ollama':
                # Ollama typically runs on localhost:11434
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="ollama"  # Ollama doesn't require a real key
                )
            elif self.config.ai_provider == 'lmstudio':
                # LMStudio typically runs on localhost:1234
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="lm-studio"  # LMStudio doesn't require a real key
                )
            elif self.config.ai_provider == 'openwebui':
                # OpenWebUI with compatible endpoint
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                self.client = OpenAI(
                    base_url=base_url,
                    api_key=self.config.api_key or "not-needed"
                )
            else:  # openai or default
                # Standard OpenAI API
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.ai_endpoint if self.config.ai_endpoint != 'http://localhost:11434' else None
                )
            
            logger.info(f"AI client initialized: {self.config.ai_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            self.client = None
    
    async def analyze_updates(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """
        Analyze updates for potential conflicts and issues
        
        Returns:
            Dict with keys:
                - safe: bool - Whether updates are safe to install
                - confidence: float - Confidence score (0-1)
                - issues: List[Dict] - List of identified issues
                - recommendations: List[str] - List of recommendations
                - summary: str - Overall summary
        """
        if not self.config.ai_enabled or not self.client:
            return self._fallback_analysis(addon_updates, hacs_updates)
        
        try:
            # Prepare the context for AI analysis
            context = self._prepare_analysis_context(addon_updates, hacs_updates)
            
            # Call AI for analysis
            response = self.client.chat.completions.create(
                model=self.config.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            logger.info(f"AI analysis completed: {len(ai_response)} chars")
            
            # Parse the structured response
            return self._parse_ai_response(ai_response, addon_updates, hacs_updates)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(addon_updates, hacs_updates)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI analysis"""
        return """You are an expert Home Assistant system administrator specializing in add-on and integration compatibility analysis.

Your task is to analyze updates for Home Assistant add-ons and HACS integrations to identify:
1. Potential dependency conflicts between updates
2. Breaking changes that could affect system stability
3. Integration compatibility issues
4. Security concerns
5. Installation order recommendations

Provide your analysis in the following JSON format:
{
  "safe": true/false,
  "confidence": 0.0-1.0,
  "issues": [
    {
      "severity": "critical/high/medium/low",
      "component": "component name",
      "description": "detailed description",
      "impact": "potential impact"
    }
  ],
  "recommendations": [
    "recommendation 1",
    "recommendation 2"
  ],
  "summary": "Overall summary of the analysis"
}

Be thorough but concise. Focus on actionable insights."""
    
    def _prepare_analysis_context(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> str:
        """Prepare context for AI analysis"""
        context = "# Update Analysis Request\n\n"
        
        if addon_updates:
            context += "## Add-on Updates Available:\n"
            for addon in addon_updates:
                context += f"- **{addon['name']}** ({addon['slug']})\n"
                context += f"  - Current: {addon['current_version']}\n"
                context += f"  - Latest: {addon['latest_version']}\n"
                context += f"  - Repository: {addon.get('repository', 'N/A')}\n"
                if addon.get('description'):
                    context += f"  - Description: {addon['description']}\n"
                context += "\n"
        
        if hacs_updates:
            context += "## HACS Integration Updates Available:\n"
            for hacs in hacs_updates:
                context += f"- **{hacs['name']}**\n"
                context += f"  - Current: {hacs['current_version']}\n"
                context += f"  - Latest: {hacs['latest_version']}\n"
                context += f"  - Repository: {hacs.get('repository', 'N/A')}\n"
                context += "\n"
        
        if not addon_updates and not hacs_updates:
            context += "No updates available.\n"
        
        context += "\nPlease analyze these updates for potential conflicts, compatibility issues, and provide safety recommendations."
        
        return context
    
    def _parse_ai_response(self, ai_response: str, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from the response
            # The AI might wrap JSON in code blocks
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
                
                # Validate and normalize the response
                return {
                    'safe': result.get('safe', True),
                    'confidence': float(result.get('confidence', 0.7)),
                    'issues': result.get('issues', []),
                    'recommendations': result.get('recommendations', []),
                    'summary': result.get('summary', 'Analysis completed'),
                    'ai_analysis': True
                }
            else:
                # If no JSON found, create a structured response from the text
                return {
                    'safe': 'safe' in ai_response.lower() and 'not safe' not in ai_response.lower(),
                    'confidence': 0.6,
                    'issues': [],
                    'recommendations': [ai_response],
                    'summary': ai_response[:200],
                    'ai_analysis': True
                }
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._fallback_analysis(addon_updates, hacs_updates)
    
    def _fallback_analysis(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """Fallback analysis when AI is not available"""
        total_updates = len(addon_updates) + len(hacs_updates)
        
        issues = []
        recommendations = []
        
        # Basic heuristic checks
        if total_updates > 10:
            issues.append({
                'severity': 'medium',
                'component': 'update_volume',
                'description': f'Large number of updates ({total_updates}) available',
                'impact': 'Installing many updates at once may complicate troubleshooting if issues arise'
            })
            recommendations.append('Consider installing updates in smaller batches')
        
        # Check for core integrations
        critical_addons = ['mosquitto', 'mariadb', 'influxdb', 'postgresql']
        for addon in addon_updates:
            if any(critical in addon['slug'].lower() for critical in critical_addons):
                issues.append({
                    'severity': 'high',
                    'component': addon['name'],
                    'description': f"Core service {addon['name']} has an update",
                    'impact': 'Updates to database/broker services may require dependent service restarts'
                })
                recommendations.append(f"Backup before updating {addon['name']}")
                recommendations.append(f"Plan for potential downtime when updating {addon['name']}")
        
        # Determine safety
        critical_issues = [i for i in issues if i['severity'] in ('critical', 'high')]
        safe = len(critical_issues) == 0
        
        return {
            'safe': safe,
            'confidence': 0.6,
            'issues': issues,
            'recommendations': recommendations if recommendations else ['No specific recommendations. Updates appear safe to install.'],
            'summary': f'Basic analysis: {total_updates} updates available. {"Safe to proceed" if safe else "Review critical issues before updating"}.',
            'ai_analysis': False
        }
