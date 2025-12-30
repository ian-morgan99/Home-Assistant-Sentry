"""
Web Server for Dependency Tree Visualization
Provides a web interface to visualize component dependencies and impact analysis
"""
import json
import logging
from aiohttp import web
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DependencyTreeWebServer:
    """Web server for dependency tree visualization"""
    
    def __init__(self, dependency_graph_builder, config_manager, port=8099):
        """
        Initialize the web server
        
        Args:
            dependency_graph_builder: DependencyGraphBuilder instance
            config_manager: ConfigManager instance
            port: Port to run the server on
        """
        self.dependency_graph_builder = dependency_graph_builder
        self.config = config_manager
        self.port = port
        self.app = None
        self.runner = None
        self.site = None
        
    async def start(self):
        """Start the web server"""
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
        
        self.app = web.Application()
        self._setup_routes()
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await self.site.start()
        
        logger.info(f"✅ Dependency tree visualization started successfully")
        logger.info(f"   Available at http://localhost:{self.port}")
        logger.info(f"   Or via Home Assistant ingress panel (Sentry in sidebar)")
        logger.info(f"   Total integrations: {len(self.dependency_graph_builder.integrations)}")
        
    async def stop(self):
        """Stop the web server"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Web server stopped")
        
    def _setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get('/', self._handle_index)
        self.app.router.add_get('/api/components', self._handle_get_components)
        self.app.router.add_get('/api/dependency-tree/{component}', self._handle_dependency_tree)
        self.app.router.add_get('/api/where-used/{component}', self._handle_where_used)
        self.app.router.add_get('/api/change-impact', self._handle_change_impact)
        self.app.router.add_get('/api/graph-data', self._handle_graph_data)
    
    def _determine_component_type(self, domain: str, integration: Dict) -> str:
        """
        Determine the type of a component based on its domain and manifest
        
        Args:
            domain: Integration domain
            integration: Integration manifest data
        
        Returns:
            str: Component type ('core', 'addon', 'hacs', 'integration')
        """
        # Check if it's a core integration
        if domain in ['homeassistant', 'hassio', 'supervisor']:
            return 'core'
        
        # Check for HACS indicators in the manifest
        manifest = integration
        if 'version' in manifest and manifest.get('version'):
            # Custom integrations typically have version numbers
            # Check for common HACS patterns
            documentation_url = manifest.get('documentation', '').lower()
            issue_tracker = manifest.get('issue_tracker', '').lower()
            
            if 'github.com' in documentation_url or 'github.com' in issue_tracker:
                # Likely a HACS integration
                return 'hacs'
        
        # Check if it's located in custom_components (HACS installs here)
        # Note: We can't directly check filesystem in this context, but we can infer
        # from other properties
        
        # Default to integration for built-in components
        return 'integration'
    
    def _get_type_label(self, component_type: str) -> str:
        """
        Get a user-friendly label for a component type
        
        Args:
            component_type: The component type code
        
        Returns:
            str: Formatted label for display
        """
        type_labels = {
            'core': 'Core',
            'addon': 'Add-on',
            'hacs': 'HACS',
            'integration': 'Integration'
        }
        return type_labels.get(component_type, 'Unknown')
        
    async def _handle_index(self, request):
        """Serve the main HTML page"""
        html = self._generate_html()
        return web.Response(text=html, content_type='text/html')
        
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
            type_order = {'core': 0, 'addon': 1, 'hacs': 2, 'integration': 3}
            components.sort(key=lambda x: (type_order.get(x['type'], 999), x['name'].lower()))
            
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
        </header>
        
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
        
        // NOTE: All API fetch() calls use relative URLs with './' prefix (e.g., './api/components')
        // This ensures the URLs resolve correctly both when accessed directly at the server root
        // and when accessed through Home Assistant's ingress proxy at /api/hassio_ingress/ha_sentry/
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            loadComponents();
            loadStats();
            setupModeButtons();
            handleUrlFragment();  // Handle URL fragment for deep linking
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
                const maxAttempts = 50;  // 5 seconds max wait
                let attempts = 0;
                const checkComponents = setInterval(() => {
                    attempts++;
                    if (components.length > 0) {
                        clearInterval(checkComponents);
                        const select = document.getElementById('component-select');
                        select.value = value;
                        if (select.value === value) {  // Verify the option exists
                            visualize();
                        } else {
                            // Component not found in list, show error
                            console.warn(`Component '${value}' not found in component list`);
                            showError(`Component '${value}' not found. It may not be a tracked integration.`);
                        }
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkComponents);
                        showError('Timeout waiting for components to load');
                    }
                }, 100);
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
                
                // Wait a bit then trigger visualization
                setTimeout(() => visualize(), 500);
            } else if (mode === 'dependency' && value) {
                // Set mode to dependency (default mode)
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                const dependencyBtn = document.querySelector('.mode-btn[data-mode="dependency"]');
                if (dependencyBtn) {
                    dependencyBtn.classList.add('active');
                    currentMode = 'dependency';
                }
                
                // Wait for components to load, then select and visualize
                const maxAttempts = 50;  // 5 seconds max wait
                let attempts = 0;
                const checkComponents = setInterval(() => {
                    attempts++;
                    if (components.length > 0) {
                        clearInterval(checkComponents);
                        const select = document.getElementById('component-select');
                        select.value = value;
                        if (select.value === value) {  // Verify the option exists
                            visualize();
                        }
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkComponents);
                        showError('Timeout waiting for components to load');
                    }
                }, 100);
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
            try {
                const response = await fetch('./api/components', {
                    credentials: 'same-origin'
                });
                
                if (response.status === 503) {
                    // Service unavailable - show detailed configuration error
                    try {
                        const data = await response.json();
                        showConfigError(data);
                    } catch (e) {
                        showConfigError({ error: 'Service unavailable', message: 'The dependency graph service is not available.' });
                    }
                    return;
                }
                
                if (!response.ok) {
                    showError(`Failed to load components: HTTP ${response.status} ${response.statusText}`);
                    return;
                }
                
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                components = data.components;
                const select = document.getElementById('component-select');
                select.innerHTML = '<option value="">-- Select a component --</option>';
                
                components.forEach(comp => {
                    const option = document.createElement('option');
                    option.value = comp.domain;
                    // Show type label and name, with dependency count
                    option.textContent = `[${comp.type_label}] ${comp.name} (${comp.dependency_count} deps)`;
                    select.appendChild(option);
                });
            } catch (error) {
                showError('Failed to load components: ' + error.message);
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('./api/graph-data', {
                    credentials: 'same-origin'
                });
                
                if (response.status === 503) {
                    return; // Don't show stats if service unavailable
                }
                
                if (!response.ok) {
                    console.error(`Failed to load stats: HTTP ${response.status} ${response.statusText}`);
                    return;
                }
                
                const data = await response.json();
                
                if (data.error) {
                    return;
                }
                
                document.getElementById('stat-integrations').textContent = data.statistics.total_integrations;
                document.getElementById('stat-dependencies').textContent = data.statistics.total_dependencies;
                document.getElementById('stat-highrisk').textContent = data.statistics.high_risk_count;
            } catch (error) {
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
            viz.innerHTML = `<div class="error">❌ Error: ${message}</div>`;
        }
        
        function showConfigError(data) {
            const viz = document.getElementById('visualization');
            const message = data.message || 'Service unavailable';
            const fix = data.fix || 'Please check add-on configuration';
            
            viz.innerHTML = `
                <div class="error">
                    <h3 style="margin-bottom: 15px;">⚙️ Configuration Required</h3>
                    <p style="margin-bottom: 10px;"><strong>Issue:</strong> ${message}</p>
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
