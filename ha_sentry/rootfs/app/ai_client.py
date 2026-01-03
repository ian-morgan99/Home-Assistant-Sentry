"""
AI Client for analyzing update conflicts
Supports OpenAI-compatible endpoints (OpenAI, LMStudio, OpenWebUI, Ollama)
"""
import logging
import json
from typing import Dict, List, Optional
from dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)


class AIClient:
    """Client for AI-powered conflict analysis"""
    
    # High-risk libraries that require special attention in updates
    HIGH_RISK_LIBRARIES = {
        'aiohttp', 'cryptography', 'numpy', 'pyjwt', 
        'sqlalchemy', 'protobuf', 'requests', 'urllib3'
    }
    
    # Context formatting constants
    MAX_RELEASE_SUMMARY_LENGTH = 200  # Maximum characters for release summary
    MAX_DEPENDENCIES_SHOWN = 10  # Maximum number of dependencies to show per update
    MAX_HIGH_RISK_DEPS_SHOWN = 5  # Maximum high-risk dependencies to show for system updates
    MAX_KEY_DEPS_SHOWN = 5  # Maximum key dependencies to show in context
    MAX_CRITICAL_DEPS_PREVIEW = 3  # Maximum critical dependencies to preview in system updates
    
    def __init__(self, config, dependency_graph=None):
        """Initialize the AI client
        
        Args:
            config: Configuration object
            dependency_graph: Optional dependency graph data from DependencyGraphBuilder
        """
        self.config = config
        self.client = None
        self.dependency_graph = dependency_graph
        self.dependency_analyzer = DependencyAnalyzer(dependency_graph=dependency_graph)
        
        if config.ai_enabled:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI-compatible client"""
        try:
            logger.debug(f"Initializing AI client for provider: {self.config.ai_provider}")
            from openai import OpenAI
            import httpx
            
            # Configure timeout to prevent hanging on network issues
            # Connect timeout: 10 seconds to establish connection
            # Read timeout: 120 seconds for AI response generation
            # Write timeout: 30 seconds for sending request
            timeout = httpx.Timeout(
                connect=10.0,  # Connection establishment
                read=120.0,    # Reading response (AI may take time to generate)
                write=30.0,    # Writing request
                pool=10.0      # Acquiring connection from pool
            )
            
            # Configure based on provider
            if self.config.ai_provider == 'ollama':
                # Ollama typically runs on localhost:11434
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                logger.debug(f"Configuring Ollama client with base_url: {base_url}")
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="ollama",  # Ollama doesn't require a real key
                    timeout=timeout
                )
            elif self.config.ai_provider == 'lmstudio':
                # LMStudio typically runs on localhost:1234
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                logger.debug(f"Configuring LMStudio client with base_url: {base_url}")
                self.client = OpenAI(
                    base_url=base_url,
                    api_key="lm-studio",  # LMStudio doesn't require a real key
                    timeout=timeout
                )
            elif self.config.ai_provider == 'openwebui':
                # OpenWebUI with compatible endpoint
                base_url = self.config.ai_endpoint
                if not base_url.endswith('/v1'):
                    base_url = f"{base_url}/v1"
                logger.debug(f"Configuring OpenWebUI client with base_url: {base_url}")
                self.client = OpenAI(
                    base_url=base_url,
                    api_key=self.config.api_key or "not-needed",
                    timeout=timeout
                )
            else:  # openai or default
                # Standard OpenAI API
                logger.debug(f"Configuring OpenAI client with endpoint: {self.config.ai_endpoint}")
                self.client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.ai_endpoint if self.config.ai_endpoint != 'http://localhost:11434' else None,
                    timeout=timeout
                )
            
            logger.info(f"AI client initialized: {self.config.ai_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
            logger.error(f"AI Provider: {self.config.ai_provider}")
            logger.error(f"AI Endpoint: {self.config.ai_endpoint}")
            logger.error(f"AI Model: {self.config.ai_model}")
            logger.info("AI analysis will be disabled. The add-on will continue using fallback dependency analysis.")
            logger.info("To resolve this issue, please check:")
            logger.info("  1. Your AI provider is running and accessible at the configured endpoint")
            logger.info("  2. The endpoint URL is correct (e.g., http://localhost:1234 for LMStudio)")
            logger.info("  3. The model name is correctly configured")
            logger.debug("Full error details:", exc_info=True)
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
            logger.debug("AI not enabled or client not available, using fallback analysis")
            return self._fallback_analysis(addon_updates, hacs_updates)
        
        try:
            # Prepare the context for AI analysis
            logger.debug("Preparing context for AI analysis")
            context = self._prepare_analysis_context(addon_updates, hacs_updates)
            logger.debug(f"Context prepared, size: {len(context)} characters")
            
            # Call AI for analysis
            logger.info(f"Sending analysis request to AI ({self.config.ai_provider} - {self.config.ai_model})")
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
            logger.debug(f"AI response: {ai_response[:200]}...")
            
            # Parse the structured response
            return self._parse_ai_response(ai_response, addon_updates, hacs_updates)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}", exc_info=True)
            logger.info("Falling back to dependency analysis")
            return self._fallback_analysis(addon_updates, hacs_updates)
    
    async def _call_ai(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generic method to call AI with a prompt
        
        Args:
            prompt: User prompt to send to AI
            system_prompt: Optional system prompt (uses default if not provided)
            
        Returns:
            AI response as string
        """
        if not self.client:
            raise Exception("AI client not initialized")
        
        if system_prompt is None:
            system_prompt = self._get_system_prompt()
        
        response = self.client.chat.completions.create(
            model=self.config.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
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
    
    def _get_dependency_info_for_update(self, update: Dict) -> Dict:
        """
        Extract dependency information for an update from the dependency graph.
        
        Args:
            update: Update information dict (e.g. from add-on or HACS metadata).
            
        Returns:
            Dict with dependency information. The structure depends on the update type:
            
            - For system updates (`type` in `["core", "supervisor", "os"]`):
              
              {
                  "type": "system",
                  "high_risk_dependencies": [
                      {
                          "package": str,     # Python package name
                          "user_count": int,  # Number of integrations using this package
                          "high_risk": bool   # Always True for packages in HIGH_RISK_LIBRARIES
                      },
                      ...
                  ],
                  "impact_radius": int       # Total number of integrations in the system
              }
            
            - For add-on / integration updates:
              
              {
                  "type": "integration",
                  "requirements": List[Dict],     # Integration requirements from dependency graph,
                                                  # truncated to MAX_DEPENDENCIES_SHOWN
                  "high_risk_count": int,         # Number of requirements marked as high risk
                  "shared_dependency_impact": int # Number of other integrations sharing dependencies
              }
            
            If no dependency graph is available or the update cannot be matched to an
            integration, an empty dict is returned.
        """
        if not self.dependency_graph:
            return {}
        
        # Try to match update to integration in dependency graph
        # For core/supervisor/os updates, look for system-level dependencies
        update_type = update.get('type', 'addon')
        integrations = self.dependency_graph.get('integrations', {})
        dependency_map = self.dependency_graph.get('dependency_map', {})
        
        # For system updates (core, supervisor, os), analyze high-risk shared dependencies
        if update_type in ['core', 'supervisor', 'os']:
            high_risk_deps = []
            for pkg, users in dependency_map.items():
                if pkg in self.HIGH_RISK_LIBRARIES:
                    high_risk_deps.append({
                        'package': pkg,
                        'user_count': len(users),
                        'high_risk': True
                    })
            return {
                'type': 'system',
                'high_risk_dependencies': high_risk_deps[:self.MAX_HIGH_RISK_DEPS_SHOWN],
                'impact_radius': len(integrations)
            }
        
        # For add-ons and integrations, try to find matching integration
        update_name = update.get('name', '').lower()
        slug = update.get('slug', '').lower()
        
        # Try to find matching integration by domain/name
        matching_integration = None
        for domain, integration_data in integrations.items():
            # Use exact matching to avoid false positives
            if (domain.lower() == slug or 
                domain.lower() == update_name or
                integration_data.get('name', '').lower() == update_name):
                matching_integration = integration_data
                break
        
        if matching_integration:
            requirements = matching_integration.get('requirements', [])
            # Count high-risk dependencies efficiently
            high_risk_count = sum(1 for req in requirements if req.get('high_risk'))
            
            # Calculate impact: how many other integrations use this integration's dependencies
            impacted = set()
            for req in requirements:
                pkg = req.get('package')
                if pkg and pkg in dependency_map:
                    impacted.update(u['integration'] for u in dependency_map[pkg])
            
            return {
                'type': 'integration',
                'requirements': requirements[:self.MAX_DEPENDENCIES_SHOWN],
                'high_risk_count': high_risk_count,
                'shared_dependency_impact': len(impacted)
            }
        
        return {}
    
    def _prepare_analysis_context(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> str:
        """Prepare context for AI analysis with dependency information"""
        context = "# Update Analysis Request\n\n"
        
        # Add dependency graph summary if available
        if self.dependency_graph:
            stats = self.dependency_graph.get('machine_readable', {}).get('statistics', {})
            if stats:
                context += "## System Context:\n"
                context += f"- Total Integrations: {stats.get('total_integrations', 0)}\n"
                context += f"- Unique Dependencies: {stats.get('total_dependencies', 0)}\n"
                context += f"- High-Risk Dependencies: {stats.get('high_risk_dependencies', 0)}\n"
                context += "\n"
        
        if addon_updates:
            context += "## Add-on/System Updates Available:\n"
            for addon in addon_updates:
                # Handle both formats: with slug (from get_addon_updates) and without slug (from get_all_updates)
                addon_identifier = ""
                if addon.get('slug'):
                    addon_identifier = f" ({addon['slug']})"
                elif addon.get('entity_id'):
                    addon_identifier = f" ({addon['entity_id']})"
                
                # Determine update criticality
                update_type = addon.get('type', 'addon')
                criticality = ""
                if update_type in ['core', 'supervisor', 'os']:
                    criticality = " [CRITICAL SYSTEM UPDATE]"
                
                context += f"- **{addon['name']}**{addon_identifier}{criticality}\n"
                context += f"  - Current: {addon['current_version']} → Latest: {addon['latest_version']}\n"
                context += f"  - Type: {update_type}\n"
                
                # Add repository and release info
                if addon.get('repository'):
                    context += f"  - Repository: {addon['repository']}\n"
                if addon.get('release_url'):
                    context += f"  - Release Notes: {addon['release_url']}\n"
                if addon.get('release_summary'):
                    full_summary = addon['release_summary']
                    if len(full_summary) > self.MAX_RELEASE_SUMMARY_LENGTH:
                        summary = full_summary[:self.MAX_RELEASE_SUMMARY_LENGTH] + "..."
                    else:
                        summary = full_summary
                    context += f"  - Summary: {summary}\n"
                if addon.get('description'):
                    context += f"  - Description: {addon['description']}\n"
                
                # Add dependency information if available
                dep_info = self._get_dependency_info_for_update(addon)
                if dep_info:
                    if dep_info.get('type') == 'system':
                        high_risk = dep_info.get('high_risk_dependencies', [])
                        if high_risk:
                            context += f"  - Impact: System-wide ({dep_info.get('impact_radius', 0)} integrations)\n"
                            context += "  - Critical Dependencies:\n"
                            for dep in high_risk[:self.MAX_CRITICAL_DEPS_PREVIEW]:
                                context += f"    • {dep['package']} (used by {dep['user_count']} integrations) ⚠️\n"
                    elif dep_info.get('type') == 'integration':
                        if dep_info.get('high_risk_count', 0) > 0:
                            context += f"  - High-Risk Dependencies: {dep_info['high_risk_count']}\n"
                        if dep_info.get('shared_dependency_impact', 0) > 0:
                            context += f"  - Shared Dependency Impact: {dep_info['shared_dependency_impact']} integrations\n"
                        requirements = dep_info.get('requirements', [])
                        if requirements:
                            context += "  - Key Dependencies:\n"
                            for req in requirements[:self.MAX_KEY_DEPS_SHOWN]:
                                risk_marker = " ⚠️" if req.get('high_risk') else ""
                                context += f"    • {req['package']} {req['specifier']}{risk_marker}\n"
                
                context += "\n"
        
        if hacs_updates:
            context += "## HACS/Integration Updates Available:\n"
            for hacs in hacs_updates:
                context += f"- **{hacs['name']}**\n"
                context += f"  - Current: {hacs['current_version']} → Latest: {hacs['latest_version']}\n"
                
                if hacs.get('repository'):
                    context += f"  - Repository: {hacs['repository']}\n"
                if hacs.get('release_url'):
                    context += f"  - Release Notes: {hacs['release_url']}\n"
                if hacs.get('release_summary'):
                    full_summary = hacs['release_summary']
                    if len(full_summary) > self.MAX_RELEASE_SUMMARY_LENGTH:
                        summary = full_summary[:self.MAX_RELEASE_SUMMARY_LENGTH] + "..."
                    else:
                        summary = full_summary
                    context += f"  - Summary: {summary}\n"
                
                # Add dependency information
                dep_info = self._get_dependency_info_for_update(hacs)
                if dep_info and dep_info.get('type') == 'integration':
                    if dep_info.get('high_risk_count', 0) > 0:
                        context += f"  - High-Risk Dependencies: {dep_info['high_risk_count']}\n"
                    requirements = dep_info.get('requirements', [])
                    if requirements:
                        context += "  - Dependencies:\n"
                        for req in requirements[:self.MAX_KEY_DEPS_SHOWN]:
                            risk_marker = " ⚠️" if req.get('high_risk') else ""
                            context += f"    • {req['package']} {req['specifier']}{risk_marker}\n"
                
                context += "\n"
        
        if not addon_updates and not hacs_updates:
            context += "No updates available.\n"
        
        context += "\nPlease analyze these updates for potential conflicts, compatibility issues, and provide safety recommendations."
        context += "\nFocus on:"
        context += "\n- Breaking changes in high-risk dependencies (⚠️)"
        context += "\n- Compatibility between shared dependencies"
        context += "\n- Impact radius of system-wide updates"
        context += "\n- Recommended installation order"
        
        return context
    
    def _parse_ai_response(self, ai_response: str, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """Parse AI response into structured format"""
        try:
            logger.debug("Parsing AI response")
            # Try to extract JSON from the response
            # The AI might wrap JSON in code blocks
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = ai_response[json_start:json_end]
                result = json.loads(json_str)
                
                logger.debug(f"Successfully parsed JSON response: safe={result.get('safe')}, confidence={result.get('confidence')}")
                
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
                logger.warning("No JSON found in AI response, parsing as text")
                return {
                    'safe': 'safe' in ai_response.lower() and 'not safe' not in ai_response.lower(),
                    'confidence': 0.6,
                    'issues': [],
                    'recommendations': [ai_response],
                    'summary': ai_response[:200],
                    'ai_analysis': True
                }
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}", exc_info=True)
            return self._fallback_analysis(addon_updates, hacs_updates)
    
    def _fallback_analysis(self, addon_updates: List[Dict], hacs_updates: List[Dict]) -> Dict:
        """
        Fallback analysis when AI is not available
        Uses deep dependency analysis without AI
        """
        logger.info("Using deep dependency analysis (non-AI)")
        return self.dependency_analyzer.analyze_updates(addon_updates, hacs_updates)
