"""
Web Server for Dependency Tree Visualization
Provides a web interface to visualize component dependencies and impact analysis
"""
import json
import logging
import html
from aiohttp import web
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DependencyTreeWebServer:
    """Web server for dependency tree visualization"""
    
    # Core Home Assistant domains
    CORE_DOMAINS = {'homeassistant', 'hassio', 'supervisor'}
    
    # Type order for sorting (lower number = higher priority)
    # Note: 'addon' is reserved for future use when add-on data is included
    TYPE_SORT_ORDER = {'core': 0, 'addon': 1, 'hacs': 2, 'integration': 3}
    UNKNOWN_TYPE_SORT_ORDER = 999  # Fallback for unknown types
    
    # Type labels for display
    TYPE_LABELS = {
        'core': 'Core',
        'addon': 'Add-on',  # Reserved for future use
        'hacs': 'HACS Integration',
        'integration': 'Integration'
    }
    
    def __init__(self, dependency_graph_builder, config_manager, port=8099, sentry_service=None):
        """
        Initialize the web server
        
        Args:
            dependency_graph_builder: DependencyGraphBuilder instance
            config_manager: ConfigManager instance
            port: Port to run the server on
            sentry_service: Optional reference to SentryService for status checking
        """
        self.dependency_graph_builder = dependency_graph_builder
        self.config = config_manager
        self.port = port
        self.sentry_service = sentry_service  # Reference to get build status
        self.app = None
        self.runner = None
        self.site = None
        
    async def start(self):
        """Start the web server"""
        try:
            if not self.config.enable_web_ui:
                logger.info("Web UI disabled in configuration")
                return
            
            # Validate dependency graph is available
            if not self.dependency_graph_builder:
                logger.error("Cannot start web server: Dependency graph builder is not available")
                logger.error("This usually means:")
                logger.error("  1. 'enable_dependency_graph' is disabled in configuration")
                logger.error("  2. Dependency graph building failed during initialization")
                logger.error("To fix: Set 'enable_dependency_graph: true' in add-on configuration")
                logger.error("Note: Web UI requires dependency graph to be enabled")
                return
                
            logger.info(f"Starting dependency tree web server on port {self.port}")
            logger.info(f"  Binding to: 0.0.0.0:{self.port}")
            logger.info(f"  Web UI configuration: enable_web_ui={self.config.enable_web_ui}")
            
            self.app = web.Application(middlewares=[self.error_middleware])
            self._setup_routes()
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            logger.info(f"✅ Dependency tree visualization started successfully")
            logger.info(f"   Available at http://localhost:{self.port}")
            logger.info(f"   Or via Home Assistant ingress: /api/hassio_ingress/ha_sentry")
            logger.info(f"   Also accessible from the 'Sentry' panel in your Home Assistant sidebar")
            logger.info(f"   Total integrations: {len(self.dependency_graph_builder.integrations)}")
        except Exception as e:
            logger.error(f"❌ Failed to start web server: {e}", exc_info=True)
            logger.error("Web UI will not be available")
            logger.error("Common causes:")
            logger.error(f"  1. Port {self.port} is already in use")
            logger.error("  2. Permission denied binding to the port")
            logger.error("  3. Network configuration issue")
            logger.error("Check the error details above for more information")
        
    async def stop(self):
        """Stop the web server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web server stopped")
    
    @web.middleware
    async def error_middleware(self, request, handler):
        """Global error handler middleware to catch unhandled exceptions"""
        try:
            response = await handler(request)
            return response
        except web.HTTPException as e:
            # HTTP exceptions are intentional, re-raise them
            raise
        except Exception as e:
            # Log the error with full traceback
            logger.error(f"Unhandled exception in request handler: {e}", exc_info=True)
            logger.error(f"  Request path: {request.path}")
            logger.error(f"  Request method: {request.method}")
            try:
                logger.error(f"  Request URL: {request.url}")
            except (AttributeError, ValueError) as url_error:
                # URL property may fail when accessed through Home Assistant ingress proxy
                # or in test environments with malformed requests
                # AttributeError: Missing URL components
                # ValueError: Invalid host/port format (e.g., 'homeassistant.local:8123')
                # This is expected when using HA ingress and can be safely ignored
                logger.debug(f"Request URL not available (expected when using HA ingress): {url_error}")
            
            # Sanitize error message for production - avoid leaking sensitive information
            # For HTML responses (web UI), include details since it's typically accessed by admin users
            # For API responses, use generic message
            if request.path.startswith('/api/'):
                # API endpoints: return generic error to avoid information disclosure
                return web.json_response({
                    'error': 'Internal server error',
                    'message': 'An unexpected error occurred. Please check the add-on logs for details.',
                    'path': request.path
                }, status=500)
            else:
                # HTML pages: show details for admin troubleshooting
                error_html = self._generate_error_html(str(e), "Internal Server Error")
                return web.Response(text=error_html, content_type='text/html', status=500)
        
    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self._handle_index)
        self.app.router.add_get('/api/status', self._handle_status)
        self.app.router.add_get('/api/components', self._handle_get_components)
        self.app.router.add_get('/api/dependency-tree/{component}', self._handle_dependency_tree)
        self.app.router.add_get('/api/where-used/{component}', self._handle_where_used)
        self.app.router.add_get('/api/change-impact', self._handle_change_impact)
        self.app.router.add_get('/api/graph-data', self._handle_graph_data)
    
    def _generate_error_html(self, error_message: str, title: str = "Error") -> str:
        """
        Generate a user-friendly error HTML page
        
        Args:
            error_message: The error message to display (will be HTML-escaped)
            title: The page title
        
        Returns:
            str: HTML error page
        """
        # Escape the error message to prevent XSS
        escaped_message = html.escape(error_message)
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>{html.escape(title)} - Home Assistant Sentry</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }}
        .error {{ background: white; padding: 30px; border-radius: 8px; max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #d32f2f; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; word-wrap: break-word; }}
    </style>
</head>
<body>
    <div class="error">
        <h1>❌ {html.escape(title)}</h1>
        <p>The Home Assistant Sentry web interface encountered an error:</p>
        <pre>{escaped_message}</pre>
        <p><strong>Please check the add-on logs for more details.</strong></p>
        <p>Common causes:</p>
        <ul>
            <li>Dependency graph is not enabled in configuration</li>
            <li>Web UI configuration issue</li>
            <li>Add-on initialization error</li>
        </ul>
        <p><a href="/">Retry</a></p>
    </div>
</body>
</html>"""
    
    def _determine_component_type(self, domain: str, integration: Dict) -> str:
        """
        Determine the type of a component based on its domain and manifest
        
        Args:
            domain: Integration domain
            integration: Integration manifest data
        
        Returns:
            str: Component type ('core', 'hacs', 'integration').
                Note: 'addon' is reserved for future use and is not currently returned.
        """
        # Check manifest path to determine if it's a custom component (HACS)
        manifest_path = integration.get('manifest_path', '')
        
        # HACS integrations are installed in custom_components
        if 'custom_components' in manifest_path:
            return 'hacs'
        
        # Check if it's a core Home Assistant component
        if domain in self.CORE_DOMAINS:
            return 'core'
        
        # Default to built-in integration
        return 'integration'
    
    def _get_type_label(self, component_type: str) -> str:
        """
        Get a user-friendly label for a component type
        
        Args:
            component_type: The component type code
        
        Returns:
            str: Formatted label for display
        """
        return self.TYPE_LABELS.get(component_type, 'Unknown')
        
    async def _handle_index(self, request):
        """Serve the main HTML page"""
        try:
            # Log access for debugging
            logger.debug(f"Web UI accessed from: {request.remote}")
            logger.debug(f"Request path: {request.path}")
            try:
                logger.debug(f"Request URL: {request.url}")
            except (AttributeError, ValueError):
                # URL property may fail when accessed through Home Assistant ingress proxy
                # This is expected and can be safely ignored - the path and remote are sufficient
                pass
            
            html = self._generate_html()
            return web.Response(text=html, content_type='text/html')
        except Exception as e:
            logger.error(f"Error serving index page: {e}", exc_info=True)
            # Return error page using shared template
            error_html = self._generate_error_html(str(e), "Error Loading Web UI")
            return web.Response(text=error_html, content_type='text/html', status=500)
    
    async def _handle_status(self, request):
        """Get the status of the dependency graph building process"""
        try:
            if not self.dependency_graph_builder:
                return web.json_response({
                    'status': 'unavailable',
                    'message': 'Dependency graph builder not initialized',
                    'components_count': 0,
                    'ready': False
                })
            
            components_count = len(self.dependency_graph_builder.integrations)
            
            # Get build status from sentry service if available
            build_status = 'unknown'
            build_error = None
            if self.sentry_service:
                build_status = getattr(self.sentry_service, '_graph_build_status', 'unknown')
                build_error = getattr(self.sentry_service, '_graph_build_error', None)
            
            # Determine overall status
            if build_status == 'disabled':
                status = 'unavailable'
                message = 'Dependency graph is disabled in configuration'
                is_ready = False
            elif build_status == 'failed':
                status = 'error'
                message = f'Dependency graph build failed: {build_error or "Unknown error"}'
                is_ready = False
            elif build_status == 'building':
                status = 'building'
                message = f'Building dependency graph... ({components_count} components loaded so far)'
                is_ready = False
            elif components_count > 0:
                status = 'ready'
                message = f'{components_count} components loaded'
                is_ready = True
            else:
                # No components but status is not explicitly failed
                status = 'building'
                message = 'Dependency graph is building... (this may take up to 60 seconds)'
                is_ready = False
            
            return web.json_response({
                'status': status,
                'build_status': build_status,
                'message': message,
                'components_count': components_count,
                'ready': is_ready,
                'error': build_error
            })
        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            return web.json_response({
                'status': 'error',
                'message': str(e),
                'components_count': 0,
                'ready': False
            }, status=500)
        
    async def _handle_get_components(self, request):
        """Get list of all components"""
        try:
            if not self.dependency_graph_builder:
                logger.error("API request failed: Dependency graph not available")
                logger.error("The dependency graph is required for web UI functionality")
                logger.error("Please enable 'enable_dependency_graph: true' in add-on configuration")
                return web.json_response({
                    'error': 'Dependency graph not available',
                    'message': 'The dependency graph is required for web UI functionality. Please enable "enable_dependency_graph: true" in your add-on configuration and restart.',
                    'fix': 'Go to Settings → Add-ons → Home Assistant Sentry → Configuration tab, enable "enable_dependency_graph", and restart the add-on.'
                }, status=503)
                
            components = []
            for domain, integration in self.dependency_graph_builder.integrations.items():
                if 'error' not in integration:
                    # Determine component type based on domain and manifest
                    component_type = self._determine_component_type(domain, integration)
                    
                    components.append({
                        'domain': domain,
                        'name': integration.get('name', domain),
                        'version': integration.get('version'),
                        'dependency_count': len(integration.get('requirements', [])),
                        'type': component_type,
                        'type_label': self._get_type_label(component_type)
                    })
            
            # Sort by type (using sort order), then by name
            components.sort(key=lambda x: (self.TYPE_SORT_ORDER.get(x['type'], self.UNKNOWN_TYPE_SORT_ORDER), x['name'].lower()))
            
            return web.json_response({
                'components': components,
                'total': len(components)
            })
        except Exception as e:
            logger.error(f"Error getting components: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
            
    async def _handle_dependency_tree(self, request):
        """Get dependency tree for a specific component (what it depends on)"""
        try:
            component = request.match_info['component']
            
            if not self.dependency_graph_builder:
                logger.warning(f"API request for dependency tree of '{component}' failed: Dependency graph not available")
                return web.json_response({
                    'error': 'Dependency graph not available',
                    'message': 'The dependency graph is required for web UI functionality. Please enable "enable_dependency_graph: true" in your add-on configuration and restart.'
                }, status=503)
                
            integrations = self.dependency_graph_builder.integrations
            
            if component not in integrations:
                return web.json_response({'error': 'Component not found'}, status=404)
                
            integration = integrations[component]
            
            if 'error' in integration:
                return web.json_response({
                    'error': 'Component has parsing errors',
                    'details': integration.get('error')
                }, status=400)
            
            # Build tree structure
            tree = {
                'component': component,
                'name': integration.get('name', component),
                'version': integration.get('version'),
                'dependencies': []
            }
            
            # Add direct dependencies
            for req in integration.get('requirements', []):
                dep_node = {
                    'package': req['package'],
                    'specifier': req['specifier'],
                    'high_risk': req.get('high_risk', False),
                    'shared': len(self.dependency_graph_builder.dependency_map.get(req['package'], [])) > 1,
                    'shared_count': len(self.dependency_graph_builder.dependency_map.get(req['package'], []))
                }
                tree['dependencies'].append(dep_node)
            
            return web.json_response(tree)
            
        except Exception as e:
            logger.error(f"Error getting dependency tree: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
            
    async def _handle_where_used(self, request):
        """Get 'where used' tree for a component or dependency (what depends on it)"""
        try:
            item = request.match_info['component']
            
            if not self.dependency_graph_builder:
                logger.warning(f"API request for where-used of '{item}' failed: Dependency graph not available")
                return web.json_response({
                    'error': 'Dependency graph not available',
                    'message': 'The dependency graph is required for web UI functionality. Please enable "enable_dependency_graph: true" in your add-on configuration and restart.'
                }, status=503)
            
            dependency_map = self.dependency_graph_builder.dependency_map
            integrations = self.dependency_graph_builder.integrations
            
            # Check if this is a package dependency
            if item in dependency_map:
                tree = {
                    'type': 'package',
                    'package': item,
                    'used_by': dependency_map[item],
                    'user_count': len(dependency_map[item]),
                    'high_risk': item in self.dependency_graph_builder.HIGH_RISK_LIBRARIES
                }
                return web.json_response(tree)
            
            # Check if this is an integration
            if item in integrations:
                # For integrations, we can show which other integrations might import it
                # For now, we'll show "no direct dependents" as integrations don't typically
                # depend on each other in the manifest
                tree = {
                    'type': 'integration',
                    'component': item,
                    'name': integrations[item].get('name', item),
                    'used_by': [],
                    'note': 'Integration dependencies are tracked at the package level'
                }
                return web.json_response(tree)
            
            return web.json_response({'error': 'Item not found'}, status=404)
            
        except Exception as e:
            logger.error(f"Error getting where-used tree: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
            
    async def _handle_change_impact(self, request):
        """Get impact analysis for changed components"""
        try:
            # Get components from query parameter (comma-separated)
            components_param = request.query.get('components', '')
            if not components_param:
                return web.json_response({'error': 'No components specified'}, status=400)
            
            components = [c.strip() for c in components_param.split(',')]
            
            if not self.dependency_graph_builder:
                logger.warning(f"API request for change impact failed: Dependency graph not available")
                return web.json_response({
                    'error': 'Dependency graph not available',
                    'message': 'The dependency graph is required for web UI functionality. Please enable "enable_dependency_graph: true" in your add-on configuration and restart.'
                }, status=503)
            
            integrations = self.dependency_graph_builder.integrations
            dependency_map = self.dependency_graph_builder.dependency_map
            
            impact = {
                'changed_components': components,
                'affected_packages': [],
                'affected_integrations': set(),
                'high_risk_changes': []
            }
            
            # For each changed component, find what packages it provides/affects
            for component in components:
                if component not in integrations:
                    continue
                    
                integration = integrations[component]
                if 'error' in integration:
                    continue
                
                # Check dependencies of this component
                for req in integration.get('requirements', []):
                    package = req['package']
                    
                    # Find all integrations that depend on this package
                    if package in dependency_map:
                        users = dependency_map[package]
                        
                        for user in users:
                            # Don't include the changed component itself
                            if user['domain'] != component:
                                impact['affected_integrations'].add(user['integration'])
                        
                        package_info = {
                            'package': package,
                            'specifier': req['specifier'],
                            'high_risk': req.get('high_risk', False),
                            'affected_count': len(users) - 1,  # Exclude the component itself
                            'affected_integrations': [u['integration'] for u in users if u['domain'] != component]
                        }
                        
                        impact['affected_packages'].append(package_info)
                        
                        if req.get('high_risk'):
                            impact['high_risk_changes'].append({
                                'component': component,
                                'package': package,
                                'affected_count': len(users) - 1
                            })
            
            # Convert set to list for JSON serialization
            impact['affected_integrations'] = list(impact['affected_integrations'])
            impact['total_affected'] = len(impact['affected_integrations'])
            
            return web.json_response(impact)
            
        except Exception as e:
            logger.error(f"Error getting change impact: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
            
    async def _handle_graph_data(self, request):
        """Get complete graph data for visualization"""
        try:
            if not self.dependency_graph_builder:
                logger.warning("API request for graph data failed: Dependency graph not available")
                return web.json_response({
                    'error': 'Dependency graph not available',
                    'message': 'The dependency graph is required for web UI functionality. Please enable "enable_dependency_graph: true" in your add-on configuration and restart.'
                }, status=503)
            
            # Return the machine-readable format
            graph_data = {
                'integrations': self.dependency_graph_builder.integrations,
                'dependency_map': self.dependency_graph_builder.dependency_map,
                'statistics': {
                    'total_integrations': len(self.dependency_graph_builder.integrations),
                    'total_dependencies': len(self.dependency_graph_builder.dependency_map),
                    'high_risk_count': len([
                        d for d in self.dependency_graph_builder.dependency_map.keys()
                        if d in self.dependency_graph_builder.HIGH_RISK_LIBRARIES
                    ])
                }
            }
            
            return web.json_response(graph_data)
            
        except Exception as e:
            logger.error(f"Error getting graph data: {e}", exc_info=True)
            return web.json_response({'error': str(e)}, status=500)
    
    def _generate_html(self):
        """Generate the HTML interface for dependency visualization"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Assistant Sentry - Dependency Tree Visualization</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        
        h1 {
            color: #58a6ff;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #8b949e;
            font-size: 14px;
        }
        
        .controls {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }
        
        .control-row {
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .control-group {
            flex: 1;
            min-width: 250px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #8b949e;
            font-size: 13px;
            font-weight: 600;
        }
        
        select, input {
            width: 100%;
            padding: 8px 12px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #c9d1d9;
            font-size: 14px;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #58a6ff;
        }
        
        button {
            padding: 8px 16px;
            background: #238636;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        
        button:hover {
            background: #2ea043;
        }
        
        button:active {
            background: #1a7f37;
        }
        
        .mode-selector {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .mode-btn {
            flex: 1;
            padding: 10px;
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            cursor: pointer;
            border-radius: 6px;
            transition: all 0.2s;
        }
        
        .mode-btn:hover {
            background: #30363d;
        }
        
        .mode-btn.active {
            background: #1f6feb;
            border-color: #1f6feb;
            color: white;
        }
        
        .visualization {
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #30363d;
            min-height: 500px;
        }
        
        .tree-view {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.8;
        }
        
        .tree-node {
            margin-left: 20px;
            padding: 4px 0;
        }
        
        .tree-node.root {
            margin-left: 0;
            font-weight: bold;
            color: #58a6ff;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .tree-node.dependency {
            color: #79c0ff;
        }
        
        .tree-node.high-risk {
            color: #f85149;
        }
        
        .tree-node.shared {
            color: #d29922;
        }
        
        .badge {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
        }
        
        .badge.high-risk {
            background: #da3633;
            color: white;
        }
        
        .badge.shared {
            background: #9e6a03;
            color: white;
        }
        
        .badge.info {
            background: #1f6feb;
            color: white;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #30363d;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: bold;
            color: #58a6ff;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 13px;
            color: #8b949e;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }
        
        .error {
            background: #da3633;
            color: white;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }
        
        .empty {
            text-align: center;
            padding: 60px 20px;
            color: #8b949e;
        }
        
        .empty-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        .diagnostic-panel {
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            display: none;
        }
        
        .diagnostic-panel.visible {
            display: block;
        }
        
        .diagnostic-panel h3 {
            color: #f85149;
            margin-bottom: 10px;
            font-size: 16px;
        }
        
        .diagnostic-log {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 4px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #8b949e;
        }
        
        .diagnostic-log .log-entry {
            margin-bottom: 5px;
            padding: 3px 0;
            border-bottom: 1px solid #161b22;
        }
        
        .diagnostic-log .log-entry:last-child {
            border-bottom: none;
        }
        
        .diagnostic-log .log-error {
            color: #f85149;
        }
        
        .diagnostic-log .log-warning {
            color: #d29922;
        }
        
        .diagnostic-log .log-info {
            color: #58a6ff;
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #30363d;
            border-top: 3px solid #58a6ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .status-indicator {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .status-indicator.loading {
            background: #1f6feb;
            color: white;
        }
        
        .status-indicator.error {
            background: #da3633;
            color: white;
        }
        
        .status-indicator.success {
            background: #238636;
            color: white;
        }
        
        .impact-summary {
            background: #21262d;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 15px;
        }
        
        .impact-item {
            padding: 8px 0;
            border-bottom: 1px solid #30363d;
        }
        
        .impact-item:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ Home Assistant Sentry</h1>
            <p class="subtitle">Dependency Tree Visualization & Impact Analysis</p>
            <span id="status-indicator" class="status-indicator loading">
                <span class="loading-spinner"></span> Initializing...
            </span>
        </header>
        
        <noscript>
            <div class="error" style="margin-bottom: 20px;">
                <h3>⚠️ JavaScript Required</h3>
                <p>The Home Assistant Sentry Web UI requires JavaScript to function.</p>
                <p>Please enable JavaScript in your browser and refresh the page.</p>
            </div>
        </noscript>
        
        <div id="diagnostic-panel" class="diagnostic-panel">
            <h3>🔍 Diagnostic Information</h3>
            <div id="diagnostic-log" class="diagnostic-log">
                <!-- Diagnostic logs will appear here -->
            </div>
            <button onclick="toggleDiagnostics()" style="margin-top: 10px;">Hide Diagnostics</button>
        </div>
        
        <div class="stats" id="stats">
            <div class="stat-card">
                <div class="stat-value" id="stat-integrations">-</div>
                <div class="stat-label">Integrations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-dependencies">-</div>
                <div class="stat-label">Dependencies</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-highrisk">-</div>
                <div class="stat-label">High-Risk Packages</div>
            </div>
        </div>
        
        <div class="controls">
            <div class="control-row">
                <div class="control-group">
                    <label>View Mode</label>
                    <div class="mode-selector">
                        <button class="mode-btn active" data-mode="dependency">
                            📦 Dependencies
                        </button>
                        <button class="mode-btn" data-mode="whereused">
                            🔍 Where Used
                        </button>
                        <button class="mode-btn" data-mode="impact">
                            ⚡ Change Impact
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="control-row">
                <div class="control-group">
                    <label for="component-select">Select Component</label>
                    <select id="component-select">
                        <option value="">Loading components...</option>
                    </select>
                </div>
                <div class="control-group" id="impact-input-group" style="display: none;">
                    <label for="impact-components">Changed Components (comma-separated)</label>
                    <input type="text" id="impact-components" placeholder="e.g., homeassistant, hacs">
                </div>
                <div class="control-group" style="flex: 0 0 auto;">
                    <label>&nbsp;</label>
                    <button id="visualize-btn" onclick="visualize()">Visualize</button>
                </div>
            </div>
        </div>
        
        <div class="visualization" id="visualization">
            <div class="empty">
                <div class="empty-icon">📊</div>
                <p>Select a component and view mode to visualize dependencies</p>
            </div>
        </div>
    </div>
    
    <script>
        let currentMode = 'dependency';
        let components = [];
        let componentLoadIntervalId = null;  // Track interval to prevent memory leaks
        let componentLoadAttempts = 0;  // Track retry attempts
        const MAX_COMPONENT_LOAD_RETRIES = 30;  // Maximum 30 retries (60 seconds total)
        
        // Constants for component loading timeout
        const COMPONENT_LOAD_TIMEOUT_MS = 5000;  // 5 seconds max wait
        const COMPONENT_LOAD_INTERVAL_MS = 100;   // Check every 100ms
        const MAX_COMPONENT_LOAD_ATTEMPTS = Math.floor(COMPONENT_LOAD_TIMEOUT_MS / COMPONENT_LOAD_INTERVAL_MS);
        
        // Global initialization timeout (failsafe)
        const GLOBAL_INIT_TIMEOUT_MS = 15000;  // 15 seconds total timeout
        let globalInitTimeoutId = null;
        let initializationComplete = false;
        
        // Diagnostic logging
        const diagnosticLogs = [];
        
        function addDiagnosticLog(message, level = 'info') {
            const timestamp = new Date().toISOString().substring(11, 23);
            const logEntry = { timestamp, message, level };
            diagnosticLogs.push(logEntry);
            
            // Also log to console
            const consoleMethod = level === 'error' ? 'error' : level === 'warning' ? 'warn' : 'log';
            console[consoleMethod](`[${timestamp}] ${message}`);
            
            // Update diagnostic panel if visible
            updateDiagnosticPanel();
        }
        
        function updateDiagnosticPanel() {
            const panel = document.getElementById('diagnostic-log');
            if (!panel) return;
            
            const html = diagnosticLogs.slice(-20).map(log => {
                const levelClass = `log-${log.level}`;
                return `<div class="log-entry ${levelClass}">[${log.timestamp}] ${escapeHtml(log.message)}</div>`;
            }).join('');
            
            panel.innerHTML = html || '<div class="log-entry">No diagnostic logs yet</div>';
        }
        
        function showDiagnosticPanel() {
            const panel = document.getElementById('diagnostic-panel');
            if (panel) {
                panel.classList.add('visible');
                updateDiagnosticPanel();
            }
        }
        
        function toggleDiagnostics() {
            const panel = document.getElementById('diagnostic-panel');
            if (panel) {
                panel.classList.toggle('visible');
            }
        }
        
        function updateStatusIndicator(status, message) {
            const indicator = document.getElementById('status-indicator');
            if (!indicator) return;
            
            // Remove all status classes
            indicator.classList.remove('loading', 'error', 'success');
            
            // Add new status class
            indicator.classList.add(status);
            
            // Update message
            if (status === 'loading') {
                indicator.innerHTML = `<span class="loading-spinner"></span> ${escapeHtml(message)}`;
            } else if (status === 'error') {
                indicator.innerHTML = `❌ ${escapeHtml(message)}`;
            } else if (status === 'success') {
                indicator.innerHTML = `✅ ${escapeHtml(message)}`;
            }
        }
        
        function handleGlobalInitTimeout() {
            if (!initializationComplete) {
                addDiagnosticLog('Global initialization timeout reached (15s)', 'error');
                updateStatusIndicator('error', 'Initialization timeout');
                showDiagnosticPanel();
                
                const select = document.getElementById('component-select');
                select.innerHTML = '<option value="">Initialization timeout</option>';
                
                showError('The Web UI failed to initialize within 15 seconds.\\n\\n' +
                         'This usually indicates:\\n' +
                         '1. The dependency graph is still building (check add-on logs)\\n' +
                         '2. The add-on is not responding\\n' +
                         '3. Network/proxy issues preventing API access\\n\\n' +
                         'Check the diagnostic panel and add-on logs for details.\\n' +
                         'Try refreshing the page or restarting the add-on.');
            }
        }
        
        // NOTE: All API fetch() calls use relative URLs with './' prefix (e.g., './api/components')
        // This ensures the URLs resolve correctly both when accessed directly at the server root
        // and when accessed through Home Assistant's ingress proxy at /api/hassio_ingress/ha_sentry/
        
        /**
         * Escape HTML entities to prevent XSS attacks
         * @param {string} text - Text to escape
         * @returns {string} - HTML-safe text
         */
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        /**
         * Wait for components to load with timeout, then execute callback
         * @param {function} callback - Function to call when components are loaded
         * @param {function} errorCallback - Function to call on timeout or error
         */
        function waitForComponents(callback, errorCallback) {
            // Clear any existing interval to prevent memory leaks
            if (componentLoadIntervalId !== null) {
                clearInterval(componentLoadIntervalId);
                componentLoadIntervalId = null;
            }
            
            let attempts = 0;
            componentLoadIntervalId = setInterval(() => {
                attempts++;
                if (components.length > 0) {
                    clearInterval(componentLoadIntervalId);
                    componentLoadIntervalId = null;
                    callback();
                } else if (attempts >= MAX_COMPONENT_LOAD_ATTEMPTS) {
                    clearInterval(componentLoadIntervalId);
                    componentLoadIntervalId = null;
                    if (errorCallback) {
                        errorCallback();
                    }
                }
            }, COMPONENT_LOAD_INTERVAL_MS);
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            addDiagnosticLog('DOM Content Loaded', 'info');
            addDiagnosticLog('Current URL: ' + window.location.href, 'info');
            addDiagnosticLog('User Agent: ' + navigator.userAgent.substring(0, 100), 'info');
            
            updateStatusIndicator('loading', 'Loading components...');
            
            // Set global timeout failsafe
            globalInitTimeoutId = setTimeout(handleGlobalInitTimeout, GLOBAL_INIT_TIMEOUT_MS);
            
            // Start loading
            try {
                loadComponents();
                loadStats();
                setupModeButtons();
                handleUrlFragment();  // Handle URL fragment for deep linking
            } catch (error) {
                addDiagnosticLog('Error during initialization: ' + error.message, 'error');
                updateStatusIndicator('error', 'Initialization failed');
                showDiagnosticPanel();
                showError('Failed to initialize Web UI: ' + error.message);
            }
            
            // Log current URL for debugging
            console.log('Web UI loaded');
            console.log('  URL:', window.location.href);
            console.log('  Path:', window.location.pathname);
            console.log('  Hash:', window.location.hash);
        });
        
        function handleUrlFragment() {
            // Check if there's a hash in the URL (e.g., #whereused:component or #impact:comp1,comp2)
            const hash = window.location.hash.substring(1);  // Remove the #
            if (!hash) return;
            
            const [mode, value] = hash.split(':');
            
            if (mode === 'whereused' && value) {
                // Set mode to where-used
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                const whereUsedBtn = document.querySelector('.mode-btn[data-mode="whereused"]');
                if (whereUsedBtn) {
                    whereUsedBtn.classList.add('active');
                    currentMode = 'whereused';
                }
                
                // Wait for components to load, then select and visualize
                waitForComponents(
                    () => {
                        const select = document.getElementById('component-select');
                        select.value = value;
                        if (select.value === value) {  // Verify the option exists
                            visualize();
                        } else {
                            // Component not found in list, show error
                            // Escape component name to prevent XSS
                            const escapedValue = escapeHtml(value);
                            console.warn(`Component '${escapedValue}' not found in component list`);
                            showError(`Component '${escapedValue}' not found. It may not be a tracked integration.`);
                        }
                    },
                    () => {
                        showError('Timeout waiting for components to load');
                    }
                );
            } else if (mode === 'impact' && value) {
                // Set mode to impact
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                const impactBtn = document.querySelector('.mode-btn[data-mode="impact"]');
                if (impactBtn) {
                    impactBtn.classList.add('active');
                    currentMode = 'impact';
                }
                
                // Show impact input
                const impactInput = document.getElementById('impact-input-group');
                const componentSelect = document.getElementById('component-select').closest('.control-group');
                impactInput.style.display = 'block';
                componentSelect.style.display = 'none';
                
                // Set the components value
                document.getElementById('impact-components').value = value;
                
                // Wait for components to load, then trigger visualization
                waitForComponents(
                    () => {
                        visualize();
                    },
                    () => {
                        showError('Timeout waiting for components to load');
                    }
                );
            } else if (mode === 'dependency' && value) {
                // Set mode to dependency (default mode)
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                const dependencyBtn = document.querySelector('.mode-btn[data-mode="dependency"]');
                if (dependencyBtn) {
                    dependencyBtn.classList.add('active');
                    currentMode = 'dependency';
                }
                
                // Wait for components to load, then select and visualize
                waitForComponents(
                    () => {
                        const select = document.getElementById('component-select');
                        select.value = value;
                        if (select.value === value) {  // Verify the option exists
                            visualize();
                        } else {
                            // Component not found in list, show error
                            const escapedValue = escapeHtml(value);
                            showError(`Component '${escapedValue}' not found. It may not be a tracked integration.`);
                        }
                    },
                    () => {
                        showError('Timeout waiting for components to load');
                    }
                );
            }
        }
        
        function setupModeButtons() {
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    currentMode = btn.dataset.mode;
                    
                    // Show/hide impact input
                    const impactInput = document.getElementById('impact-input-group');
                    const componentSelect = document.getElementById('component-select').closest('.control-group');
                    
                    if (currentMode === 'impact') {
                        impactInput.style.display = 'block';
                        componentSelect.style.display = 'none';
                    } else {
                        impactInput.style.display = 'none';
                        componentSelect.style.display = 'block';
                    }
                });
            });
        }
        
        async function loadComponents() {
            addDiagnosticLog('Starting component loading', 'info');
            
            try {
                // First check the status to see if the graph is still building
                let statusResponse;
                try {
                    addDiagnosticLog('Fetching status from ./api/status', 'info');
                    statusResponse = await fetch('./api/status', {
                        credentials: 'same-origin'
                    });
                    
                    if (statusResponse.ok) {
                        const statusData = await statusResponse.json();
                        addDiagnosticLog('Status check result: ' + JSON.stringify(statusData), 'info');
                        console.log('Status check:', statusData);
                        
                        // If status indicates error or unavailable, show error immediately
                        if (statusData.status === 'error' || statusData.status === 'unavailable') {
                            addDiagnosticLog('Service unavailable: ' + statusData.message, 'error');
                            updateStatusIndicator('error', 'Service unavailable');
                            const select = document.getElementById('component-select');
                            select.innerHTML = '<option value="">Service unavailable</option>';
                            showConfigError({
                                error: 'Dependency graph not available',
                                message: statusData.message || 'The dependency graph service is not available.',
                                fix: 'Check add-on logs for errors, or enable "enable_dependency_graph: true" in configuration.'
                            });
                            showDiagnosticPanel();
                            return;
                        }
                    } else {
                        addDiagnosticLog('Status check failed: HTTP ' + statusResponse.status, 'warning');
                    }
                } catch (statusError) {
                    // Status check failed, continue with component loading anyway
                    addDiagnosticLog('Status check exception: ' + statusError.message, 'warning');
                    console.warn('Status check failed:', statusError);
                }
                
                addDiagnosticLog('Fetching components from ./api/components', 'info');
                const response = await fetch('./api/components', {
                    credentials: 'same-origin'
                });
                
                addDiagnosticLog('Components fetch response: HTTP ' + response.status, 'info');
                
                if (response.status === 503) {
                    // Service unavailable - show detailed configuration error
                    addDiagnosticLog('Service unavailable (503)', 'error');
                    updateStatusIndicator('error', 'Service unavailable');
                    showDiagnosticPanel();
                    try {
                        const data = await response.json();
                        showConfigError(data);
                    } catch (e) {
                        showConfigError({ error: 'Service unavailable', message: 'The dependency graph service is not available.' });
                    }
                    return;
                }
                
                if (!response.ok) {
                    addDiagnosticLog(`HTTP error: ${response.status} ${response.statusText}`, 'error');
                    updateStatusIndicator('error', 'Failed to load');
                    showDiagnosticPanel();
                    showError(`Failed to load components: HTTP ${response.status} ${response.statusText}`);
                    return;
                }
                
                const data = await response.json();
                addDiagnosticLog('Components data received, count: ' + (data.components ? data.components.length : 'unknown'), 'info');
                
                if (data.error) {
                    addDiagnosticLog('API returned error: ' + data.error, 'error');
                    updateStatusIndicator('error', 'API error');
                    showDiagnosticPanel();
                    showError(data.error);
                    return;
                }
                
                components = data.components;
                const select = document.getElementById('component-select');
                
                if (components.length === 0) {
                    // Components still loading - retry after a delay with max retry limit
                    componentLoadAttempts++;
                    
                    if (componentLoadAttempts < MAX_COMPONENT_LOAD_RETRIES) {
                        // Still loading, retry after 2 seconds
                        const elapsed = componentLoadAttempts * 2;
                        const remaining = (MAX_COMPONENT_LOAD_RETRIES - componentLoadAttempts) * 2;
                        addDiagnosticLog(`Components empty, retry ${componentLoadAttempts}/${MAX_COMPONENT_LOAD_RETRIES} (elapsed: ${elapsed}s)`, 'warning');
                        console.log(`Components still loading, retry ${componentLoadAttempts}/${MAX_COMPONENT_LOAD_RETRIES} in 2 seconds... (elapsed: ${elapsed}s, max wait: ${remaining}s more)`);
                        select.innerHTML = `<option value="">Loading components (${elapsed}s elapsed, building dependency graph)...</option>`;
                        updateStatusIndicator('loading', `Loading... (${elapsed}s)`);
                        setTimeout(loadComponents, 2000);
                        return;
                    }
                    
                    // After max retries, show error message
                    const waitTime = MAX_COMPONENT_LOAD_RETRIES * 2;  // Calculate actual wait time
                    addDiagnosticLog(`No components after ${waitTime}s, giving up`, 'error');
                    updateStatusIndicator('error', 'No components found');
                    showDiagnosticPanel();
                    select.innerHTML = '<option value="">No integrations found</option>';
                    
                    // Show detailed error with troubleshooting steps
                    const viz = document.getElementById('visualization');
                    viz.innerHTML = `
                        <div class="error">
                            <h3 style="margin-bottom: 15px;">⚠️ No Integrations Found</h3>
                            <p style="margin-bottom: 15px;">
                                The dependency graph was built but found <strong>0 integrations</strong> after waiting ${waitTime} seconds.
                            </p>
                            
                            <p style="margin-bottom: 10px;"><strong>This usually means:</strong></p>
                            <ol style="margin-left: 20px; margin-bottom: 15px;">
                                <li style="margin-bottom: 8px;">
                                    <strong>Integration paths are incorrect or inaccessible</strong><br>
                                    <span style="font-size: 0.9em; color: #ffb3b3;">
                                        The add-on can't find your Home Assistant integrations.
                                    </span>
                                </li>
                                <li style="margin-bottom: 8px;">
                                    <strong>The dependency graph build failed</strong><br>
                                    <span style="font-size: 0.9em; color: #ffb3b3;">
                                        Check the add-on logs for error messages during graph building.
                                    </span>
                                </li>
                            </ol>
                            
                            <p style="margin-bottom: 10px;"><strong>How to fix:</strong></p>
                            <ol style="margin-left: 20px; margin-bottom: 15px;">
                                <li style="margin-bottom: 8px;">
                                    Check the <strong>add-on logs</strong> for details:
                                    <ul style="margin-left: 20px; margin-top: 5px;">
                                        <li>Go to Settings → Add-ons → Home Assistant Sentry</li>
                                        <li>Click the "Log" tab</li>
                                        <li>Look for messages starting with "BUILDING DEPENDENCY GRAPH"</li>
                                        <li>Look for "FOUND ALTERNATIVE INTEGRATION PATHS" suggestions</li>
                                    </ul>
                                </li>
                                <li style="margin-bottom: 8px;">
                                    If logs show path errors, <strong>configure custom paths</strong>:
                                    <ul style="margin-left: 20px; margin-top: 5px;">
                                        <li>Go to Configuration tab</li>
                                        <li>Add the paths shown in the logs to 'custom_integration_paths'</li>
                                        <li>Save and restart the add-on</li>
                                    </ul>
                                </li>
                                <li style="margin-bottom: 8px;">
                                    Try <strong>refreshing this page</strong> after checking the logs
                                </li>
                            </ol>
                            
                            <p style="font-size: 0.9em; color: #ffb3b3; margin-top: 15px;">
                                💡 <strong>Tip:</strong> The add-on automatically scans common paths and suggests alternatives in the logs.
                            </p>
                            
                            <button onclick="window.location.reload()" style="margin-top: 15px; margin-right: 10px;">
                                🔄 Refresh Page
                            </button>
                            <button onclick="toggleDiagnostics()" style="margin-top: 15px;">
                                📋 Hide Diagnostic Logs
                            </button>
                        </div>`;
                    return;
                }
                
                // Successfully loaded components, reset retry counter
                componentLoadAttempts = 0;
                initializationComplete = true;
                
                // Clear global timeout
                if (globalInitTimeoutId) {
                    clearTimeout(globalInitTimeoutId);
                    globalInitTimeoutId = null;
                }
                
                select.innerHTML = '<option value="">-- Select a component --</option>';
                
                components.forEach(comp => {
                    const option = document.createElement('option');
                    option.value = comp.domain;
                    // Show type label and name, with dependency count
                    option.textContent = `[${comp.type_label}] ${comp.name} (${comp.dependency_count} deps)`;
                    select.appendChild(option);
                });
                
                // Log success for debugging
                addDiagnosticLog(`Successfully loaded ${components.length} components`, 'info');
                updateStatusIndicator('success', `${components.length} components loaded`);
                console.log(`Loaded ${components.length} components successfully`);
            } catch (error) {
                addDiagnosticLog('Component loading exception: ' + error.message, 'error');
                addDiagnosticLog('Error stack: ' + (error.stack || 'no stack trace'), 'error');
                updateStatusIndicator('error', 'Load failed');
                showDiagnosticPanel();
                showError('Failed to load components: ' + error.message);
                console.error('Component loading error:', error);
            }
        }
        
        async function loadStats() {
            try {
                addDiagnosticLog('Loading statistics', 'info');
                const response = await fetch('./api/graph-data', {
                    credentials: 'same-origin'
                });
                
                if (response.status === 503) {
                    addDiagnosticLog('Stats unavailable (503)', 'warning');
                    return; // Don't show stats if service unavailable
                }
                
                if (!response.ok) {
                    addDiagnosticLog(`Failed to load stats: HTTP ${response.status}`, 'warning');
                    console.error(`Failed to load stats: HTTP ${response.status} ${response.statusText}`);
                    return;
                }
                
                const data = await response.json();
                
                if (data.error) {
                    addDiagnosticLog('Stats API error: ' + data.error, 'warning');
                    return;
                }
                
                document.getElementById('stat-integrations').textContent = data.statistics.total_integrations;
                document.getElementById('stat-dependencies').textContent = data.statistics.total_dependencies;
                document.getElementById('stat-highrisk').textContent = data.statistics.high_risk_count;
                addDiagnosticLog('Statistics loaded successfully', 'info');
            } catch (error) {
                addDiagnosticLog('Stats loading exception: ' + error.message, 'warning');
                console.error('Failed to load stats:', error);
            }
        }
        
        async function visualize() {
            const viz = document.getElementById('visualization');
            viz.innerHTML = '<div class="loading">Loading...</div>';
            
            try {
                if (currentMode === 'impact') {
                    await visualizeImpact();
                } else {
                    const component = document.getElementById('component-select').value;
                    if (!component) {
                        viz.innerHTML = '<div class="empty"><div class="empty-icon">⚠️</div><p>Please select a component</p></div>';
                        return;
                    }
                    
                    if (currentMode === 'dependency') {
                        await visualizeDependencies(component);
                    } else if (currentMode === 'whereused') {
                        await visualizeWhereUsed(component);
                    }
                }
            } catch (error) {
                showError('Visualization failed: ' + error.message);
            }
        }
        
        async function visualizeDependencies(component) {
            const response = await fetch(`./api/dependency-tree/${component}`, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                showError(`Failed to load dependency tree: HTTP ${response.status} ${response.statusText}`);
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            let html = '<div class="tree-view">';
            html += `<div class="tree-node root">📦 ${data.name} (${data.component})`;
            if (data.version) {
                html += ` <span class="badge info">v${data.version}</span>`;
            }
            html += '</div>';
            
            if (data.dependencies.length === 0) {
                html += '<div class="tree-node">└─ <em>No dependencies</em></div>';
            } else {
                data.dependencies.forEach((dep, index) => {
                    const isLast = index === data.dependencies.length - 1;
                    const prefix = isLast ? '└─' : '├─';
                    const nodeClass = dep.high_risk ? 'high-risk' : (dep.shared ? 'shared' : 'dependency');
                    
                    html += `<div class="tree-node ${nodeClass}">`;
                    html += `${prefix} ${dep.package} ${dep.specifier}`;
                    
                    if (dep.high_risk) {
                        html += '<span class="badge high-risk">HIGH RISK</span>';
                    }
                    if (dep.shared) {
                        html += `<span class="badge shared">SHARED (${dep.shared_count})</span>`;
                    }
                    
                    html += '</div>';
                });
            }
            
            html += '</div>';
            document.getElementById('visualization').innerHTML = html;
        }
        
        async function visualizeWhereUsed(component) {
            const response = await fetch(`./api/where-used/${component}`, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                showError(`Failed to load where-used information: HTTP ${response.status} ${response.statusText}`);
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            let html = '<div class="tree-view">';
            
            if (data.type === 'package') {
                html += `<div class="tree-node root">📚 ${data.package}`;
                if (data.high_risk) {
                    html += '<span class="badge high-risk">HIGH RISK</span>';
                }
                html += `<span class="badge info">${data.user_count} users</span>`;
                html += '</div>';
                
                if (data.used_by.length === 0) {
                    html += '<div class="tree-node">└─ <em>Not used by any integration</em></div>';
                } else {
                    data.used_by.forEach((user, index) => {
                        const isLast = index === data.used_by.length - 1;
                        const prefix = isLast ? '└─' : '├─';
                        
                        html += `<div class="tree-node dependency">`;
                        html += `${prefix} ${user.integration} (${user.specifier})`;
                        html += '</div>';
                    });
                }
            } else {
                html += `<div class="tree-node root">🔧 ${data.name} (${data.component})</div>`;
                html += `<div class="tree-node">└─ <em>${data.note}</em></div>`;
            }
            
            html += '</div>';
            document.getElementById('visualization').innerHTML = html;
        }
        
        async function visualizeImpact() {
            const componentsInput = document.getElementById('impact-components').value.trim();
            
            if (!componentsInput) {
                document.getElementById('visualization').innerHTML = 
                    '<div class="empty"><div class="empty-icon">⚠️</div><p>Please enter component names</p></div>';
                return;
            }
            
            const response = await fetch(`./api/change-impact?components=${encodeURIComponent(componentsInput)}`, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                showError(`Failed to load change impact: HTTP ${response.status} ${response.statusText}`);
                return;
            }
            
            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }
            
            let html = '<div class="tree-view">';
            html += '<div class="tree-node root">⚡ Change Impact Analysis</div>';
            
            html += '<div class="impact-summary">';
            html += `<strong>Changed Components:</strong> ${data.changed_components.join(', ')}<br>`;
            html += `<strong>Total Affected Integrations:</strong> ${data.total_affected}<br>`;
            html += `<strong>High-Risk Changes:</strong> ${data.high_risk_changes.length}`;
            html += '</div>';
            
            if (data.high_risk_changes.length > 0) {
                html += '<div class="tree-node high-risk" style="margin-top: 15px;">⚠️ High-Risk Changes:</div>';
                data.high_risk_changes.forEach(change => {
                    html += `<div class="tree-node high-risk">  ├─ ${change.component} → ${change.package} (affects ${change.affected_count} integrations)</div>`;
                });
            }
            
            if (data.affected_packages.length > 0) {
                html += '<div class="tree-node" style="margin-top: 15px;">📦 Affected Packages:</div>';
                data.affected_packages.forEach((pkg, index) => {
                    const isLast = index === data.affected_packages.length - 1;
                    const prefix = isLast ? '└─' : '├─';
                    const nodeClass = pkg.high_risk ? 'high-risk' : 'dependency';
                    
                    html += `<div class="tree-node ${nodeClass}">  ${prefix} ${pkg.package} ${pkg.specifier}`;
                    if (pkg.high_risk) {
                        html += '<span class="badge high-risk">HIGH RISK</span>';
                    }
                    html += `<span class="badge info">${pkg.affected_count} affected</span>`;
                    html += '</div>';
                    
                    // Show affected integrations
                    if (pkg.affected_integrations.length > 0) {
                        const maxShow = 5;
                        const toShow = pkg.affected_integrations.slice(0, maxShow);
                        toShow.forEach((integration, i) => {
                            const isLastIntegration = i === toShow.length - 1 && pkg.affected_integrations.length <= maxShow;
                            const subPrefix = isLastIntegration ? '    └─' : '    ├─';
                            html += `<div class="tree-node" style="margin-left: 40px; color: #8b949e;">${subPrefix} ${integration}</div>`;
                        });
                        
                        if (pkg.affected_integrations.length > maxShow) {
                            html += `<div class="tree-node" style="margin-left: 40px; color: #8b949e;">    └─ ... and ${pkg.affected_integrations.length - maxShow} more</div>`;
                        }
                    }
                });
            }
            
            html += '</div>';
            document.getElementById('visualization').innerHTML = html;
        }
        
        function showError(message) {
            const viz = document.getElementById('visualization');
            // Escape HTML to prevent XSS, then convert newlines to <br> tags
            const escapedMessage = escapeHtml(message);
            const htmlMessage = escapedMessage.replace(/\n/g, '<br>');
            viz.innerHTML = `<div class="error">❌ Error: ${htmlMessage}</div>`;
            
            // Add button to show diagnostics
            viz.innerHTML += '<button onclick="toggleDiagnostics()" style="margin-top: 15px;">Show Diagnostic Logs</button>';
        }
        
        function showConfigError(data) {
            const viz = document.getElementById('visualization');
            const message = data.message || 'Service unavailable';
            const fix = data.fix || 'Please check add-on configuration';
            
            viz.innerHTML = `
                <div class="error">
                    <h3 style="margin-bottom: 15px;">⚙️ Configuration Required</h3>
                    <p style="margin-bottom: 10px;"><strong>Issue:</strong> ${escapeHtml(message)}</p>
                    <p style="margin-bottom: 15px;"><strong>How to fix:</strong></p>
                    <ol style="margin-left: 20px; margin-bottom: 15px;">
                        <li style="margin-bottom: 8px;">Go to <strong>Settings → Add-ons → Home Assistant Sentry</strong></li>
                        <li style="margin-bottom: 8px;">Click on the <strong>Configuration</strong> tab</li>
                        <li style="margin-bottom: 8px;">Enable <code>enable_dependency_graph: true</code></li>
                        <li style="margin-bottom: 8px;">Click <strong>Save</strong> and restart the add-on</li>
                    </ol>
                    <p style="font-size: 0.9em; color: #ffb3b3;">
                        💡 <strong>Note:</strong> The Web UI requires the dependency graph feature to be enabled. 
                        Check the add-on logs for more detailed information.
                    </p>
                    <button onclick="toggleDiagnostics()" style="margin-top: 15px;">Show Diagnostic Logs</button>
                </div>`;
            
            // Also update stats to show error state
            document.getElementById('stat-integrations').textContent = 'N/A';
            document.getElementById('stat-dependencies').textContent = 'N/A';
            document.getElementById('stat-highrisk').textContent = 'N/A';
            
            // Disable controls
            document.getElementById('component-select').disabled = true;
            document.getElementById('visualize-btn').disabled = true;
        }
    </script>
</body>
</html>
"""
