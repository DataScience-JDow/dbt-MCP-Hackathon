"""
Model explorer interface component
"""
import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    get_models_cache, 
    get_selected_model, 
    set_selected_model,
    is_loading,
    is_mcp_connected
)
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client
from dbt_mcp_hackathon_project.frontend.components.loading_components import (
    render_loading_spinner,
    render_skeleton_model_cards,
    render_empty_state,
    render_error_state,
    LoadingContext
)

def render_model_explorer():
    """Render the main model explorer interface"""
    
    # Welcome section for home page
    render_home_welcome()
    
    st.header("🔍 Model Explorer")
    st.markdown("Browse and explore your dbt models")
    
    # Check if we have model data
    models_cache = get_models_cache()
    
    if not models_cache and not is_loading("models"):
        render_no_data_state()
        return
    
    if is_loading("models"):
        render_loading_state()
        return
    
    # Extract models from cache (handle different formats)
    if isinstance(models_cache, dict) and 'models' in models_cache:
        # MCP server format: {"models": [...]}
        models_list = models_cache.get('models', [])
        # Convert list to dict format expected by filter_models
        models_data = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
    elif isinstance(models_cache, dict):
        # Already in dict format
        models_data = models_cache
    else:
        # Fallback for unexpected format
        st.error("⚠️ Unexpected models data format")
        return
    
    if not models_data:
        render_no_data_state()
        return
    
    # Show project statistics
    render_quick_stats()
    
    # Main layout: search/filters on top, then two columns
    render_search_and_filters()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_model_list(models_data)
    
    with col2:
        render_model_detail_panel(models_data)

def render_home_welcome():
    """Render welcome section for the home page"""
    
    st.markdown("""
    ## 👋 Welcome to dbt MCP Hackathon Project
    
    Your AI-powered companion for dbt development. Explore your existing models below or switch to the **Chat Interface** to generate new ones with natural language.
    """)
    
    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💬 Generate New Model", use_container_width=True, type="primary"):
            st.session_state.current_page = "Chat Interface"
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Models", use_container_width=True):
            load_models_from_server(force_refresh=True)
    
    with col3:
        # Connection status indicator
        if is_mcp_connected():
            st.success("✅ MCP Server Connected")
        else:
            st.error("❌ MCP Server Disconnected")
    
    st.markdown("---")

def render_no_data_state():
    """Render state when no model data is available"""
    
    if not is_mcp_connected():
        st.error("❌ MCP server not connected. Please check the connection in the sidebar.")
        
        st.markdown("""
        ### Getting Started
        
        To use dbt MCP Hackathon Project, you need to start the MCP backend server:
        
        1. **Start the backend**: Run `python start_full_app.py` in your terminal
        2. **Check connection**: Look for green status in the sidebar
        3. **Load models**: Your dbt models will appear automatically
        
        **What you can do without the backend:**
        - Browse this interface and learn the layout
        - Switch to Chat Interface to see the AI conversation UI
        - Check the sidebar for connection settings
        """)
        return
    
    st.info("📊 No model data available. Click below to load models from the MCP server.")
    
    st.markdown("""
    ### Your dbt Project
    
    This project contains **19 dbt models** across two sample businesses:
    - **🏪 Jaffle Shop**: Coffee shop with customers, orders, and products  
    - **🌸 Flower Shop**: Flower delivery with arrangements and orders
    - **📊 Cross-Business**: Combined analytics and comparisons
    
    Models are organized in **staging → intermediate → marts** layers following dbt best practices.
    """)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Load Models", key="load_models_btn", type="primary"):
            load_models_from_server()

def render_loading_state():
    """Render enhanced loading state with skeleton cards"""
    
    st.markdown("### Loading Models...")
    render_loading_spinner("Fetching model data from MCP server...")
    
    # Show skeleton cards while loading
    st.markdown("---")
    render_skeleton_model_cards(5)

def render_search_and_filters():
    """Render search bar and filter controls"""
    
    # Search bar
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_query = st.text_input(
            "🔍 Search models",
            value=st.session_state.search_query,
            placeholder="Search by name, description, or tags...",
            key="model_search"
        )
        if search_query != st.session_state.search_query:
            st.session_state.search_query = search_query
    
    with col2:
        materialization_options = ["All", "table", "view", "incremental", "ephemeral"]
        materialization_filter = st.selectbox(
            "Materialization",
            materialization_options,
            index=materialization_options.index(st.session_state.filter_materialization),
            key="materialization_filter"
        )
        if materialization_filter != st.session_state.filter_materialization:
            st.session_state.filter_materialization = materialization_filter
    
    with col3:
        layer_options = ["All", "staging", "intermediate", "marts"]
        layer_filter = st.selectbox(
            "Layer",
            layer_options,
            index=layer_options.index(st.session_state.filter_layer),
            key="layer_filter"
        )
        if layer_filter != st.session_state.filter_layer:
            st.session_state.filter_layer = layer_filter

def render_model_list(models_data: Dict[str, Any]):
    """Render the searchable list of models with pagination"""
    
    st.subheader("📋 Models")
    
    # Filter models based on search and filters
    filtered_models = filter_models(models_data)
    
    if not filtered_models:
        render_empty_state(
            "No Models Found",
            "No models match the current search and filter criteria. Try adjusting your filters or search terms.",
            "Clear Filters",
            lambda: clear_all_filters()
        )
        return
    
    # Pagination settings
    models_per_page = st.session_state.get('results_per_page', 25)
    total_models = len(filtered_models)
    total_pages = (total_models - 1) // models_per_page + 1
    
    # Initialize page state (use separate key to avoid conflicts with navigation)
    if 'model_page' not in st.session_state:
        st.session_state.model_page = 1
    
    # Ensure model_page is always an integer (with error handling)
    try:
        st.session_state.model_page = int(st.session_state.model_page)
    except (ValueError, TypeError):
        # If model_page is not a valid integer, reset to 1
        st.session_state.model_page = 1
    
    # Display model count and pagination info
    st.caption(f"Showing {total_models} models ({total_pages} pages)")
    
    # Pagination controls (top)
    if total_pages > 1:
        render_pagination_controls(total_pages, "top")
    
    # Calculate models for current page
    current_page = st.session_state.model_page
    start_idx = (current_page - 1) * models_per_page
    end_idx = start_idx + models_per_page
    
    # Convert to list for slicing
    model_items = list(filtered_models.items())
    page_models = model_items[start_idx:end_idx]
    
    # Render models for current page with container for performance
    with st.container():
        st.markdown('<div class="model-list-container">', unsafe_allow_html=True)
        
        for model_name, model_info in page_models:
            render_model_card(model_name, model_info)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Pagination controls (bottom)
    if total_pages > 1:
        render_pagination_controls(total_pages, "bottom")

def render_model_card(model_name: str, model_info: Dict[str, Any]):
    """Render a single model card"""
    
    selected_model = get_selected_model()
    is_selected = selected_model == model_name
    
    # Create a container for the model card
    with st.container():
        # Apply selection styling
        if is_selected:
            st.markdown(
                f'<div class="model-card selected">',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="model-card">',
                unsafe_allow_html=True
            )
        
        # Model header
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{model_name}**")
            
            # Model description
            description = model_info.get('description', 'No description available')
            if len(description) > 100:
                description = description[:100] + "..."
            st.caption(description)
        
        with col2:
            # Materialization badge
            materialization = model_info.get('materialization', 'unknown')
            st.markdown(
                f'<span style="background-color: #e3f2fd; padding: 2px 8px; '
                f'border-radius: 12px; font-size: 0.8em;">{materialization}</span>',
                unsafe_allow_html=True
            )
        
        # Model metadata
        col1, col2, col3 = st.columns(3)
        
        with col1:
            columns_count = len(model_info.get('columns', []))
            st.metric("Columns", columns_count)
        
        with col2:
            depends_on_count = len(model_info.get('depends_on', []))
            st.metric("Dependencies", depends_on_count)
        
        with col3:
            referenced_by_count = len(model_info.get('referenced_by', []))
            st.metric("References", referenced_by_count)
        
        # Select button
        if st.button(
            "View Details" if not is_selected else "Selected",
            key=f"select_{model_name}",
            disabled=is_selected
        ):
            set_selected_model(model_name)
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("")  # Add spacing

def render_model_detail_panel(models_data: Dict[str, Any]):
    """Render the detailed view of the selected model"""
    
    selected_model = get_selected_model()
    
    if not selected_model:
        render_no_selection_state()
        return
    
    if selected_model not in models_data:
        st.error(f"Model '{selected_model}' not found in data.")
        return
    
    model_info = models_data[selected_model]
    
    st.subheader(f"📊 {selected_model}")
    
    # Model overview
    render_model_overview(model_info)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Schema", "🔗 Dependencies", "📈 Lineage"])
    
    with tab1:
        render_model_schema(model_info)
    
    with tab2:
        render_model_dependencies(model_info, models_data)
    
    with tab3:
        render_model_lineage(selected_model, models_data)

def render_no_selection_state():
    """Render state when no model is selected"""
    st.info("👈 Select a model from the list to view details")
    
    st.markdown("""
    ### Model Explorer Features
    
    - **Search**: Find models by name, description, or tags
    - **Filter**: Filter by materialization type or layer
    - **Dependencies**: View upstream and downstream relationships
    - **Schema**: Explore model columns and data types
    - **Lineage**: Visualize data flow through your models
    """)

def render_model_overview(model_info: Dict[str, Any]):
    """Render model overview information"""
    
    # Basic info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Path:**")
        st.code(model_info.get('path', 'Unknown'))
        
        st.markdown("**Materialization:**")
        st.code(model_info.get('materialization', 'Unknown'))
    
    with col2:
        tags = model_info.get('tags', [])
        if tags:
            st.markdown("**Tags:**")
            for tag in tags:
                st.markdown(f"- `{tag}`")
        else:
            st.markdown("**Tags:** None")
    
    # Description
    description = model_info.get('description')
    if description:
        st.markdown("**Description:**")
        st.markdown(description)

def render_model_schema(model_info: Dict[str, Any]):
    """Render model schema information"""
    
    columns = model_info.get('columns', [])
    
    if not columns:
        st.warning("⚠️ No column information available for this model.")
        
        # Check if we can get manifest info to provide better guidance
        if is_mcp_connected():
            try:
                client = get_mcp_client()
                success, manifest_info = client.get_manifest_info()
                
                if success and manifest_info.get('loaded'):
                    models_without_columns = manifest_info.get('models_without_columns', 0)
                    total_models = manifest_info.get('total_models', 0)
                    
                    if models_without_columns > 0:
                        st.info(f"""📋 **Column Information Missing**
                        
**Status:** {models_without_columns} of {total_models} models don't have column definitions.

**To add column information:**
1. Create or update `schema.yml` files in your models directory
2. Define columns for each model:
```yaml
models:
  - name: {model_info.get('name', 'your_model')}
    columns:
      - name: column_name
        data_type: varchar
        description: "Description of the column"
```
3. Run `dbt compile` to update the manifest
4. Refresh the Model Explorer

**Alternative:** Run `dbt docs generate` to auto-detect columns from the database.""")
                    else:
                        st.info("Column information should be available. Try refreshing the model data.")
                else:
                    st.info("Run `dbt compile` to generate column information, then refresh the model data.")
            except Exception:
                st.info("To see column information, add column definitions to your `schema.yml` files and run `dbt compile`.")
        else:
            st.info("Connect to the MCP server to see column information and get detailed guidance.")
        
        return
    
    # Create DataFrame for columns
    columns_data = []
    for col in columns:
        columns_data.append({
            'Column': col.get('name', ''),
            'Type': col.get('data_type', ''),
            'Description': col.get('description', ''),
            'Tests': ', '.join(col.get('tests', []))
        })
    
    df = pd.DataFrame(columns_data)
    
    # Display as interactive table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

def render_model_dependencies(model_info: Dict[str, Any], models_data: Dict[str, Any]):
    """Render model dependencies"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Upstream Dependencies:**")
        depends_on = model_info.get('depends_on', [])
        
        if depends_on:
            for dep in depends_on:
                if dep in models_data:
                    if st.button(f"📊 {dep}", key=f"dep_{dep}"):
                        set_selected_model(dep)
                        st.rerun()
                else:
                    st.markdown(f"- {dep}")
        else:
            st.info("No upstream dependencies")
    
    with col2:
        st.markdown("**Downstream References:**")
        referenced_by = model_info.get('referenced_by', [])
        
        if referenced_by:
            for ref in referenced_by:
                if ref in models_data:
                    if st.button(f"📊 {ref}", key=f"ref_{ref}"):
                        set_selected_model(ref)
                        st.rerun()
                else:
                    st.markdown(f"- {ref}")
        else:
            st.info("No downstream references")

def render_model_lineage(selected_model: str, models_data: Dict[str, Any]):
    """Render model lineage visualization using networkx and plotly"""
    
    try:
        # Create directed graph
        G = create_lineage_graph(selected_model, models_data)
        
        if len(G.nodes()) == 0:
            st.info("No lineage data available for visualization.")
            return
        
        # Create plotly visualization
        fig = create_lineage_plot(G, selected_model)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add legend
        st.markdown("""
        **Legend:**
        - 🔵 Selected model
        - 🟢 Upstream dependencies
        - 🟡 Downstream references
        - ⚪ Other connected models
        """)
        
    except Exception as e:
        st.error(f"Error creating lineage visualization: {str(e)}")
        st.info("Lineage visualization requires networkx and plotly packages.")

def filter_models(models_data: Dict[str, Any]) -> Dict[str, Any]:
    """Filter models based on search query and filters"""
    
    filtered = {}
    search_query = st.session_state.search_query.lower()
    materialization_filter = st.session_state.filter_materialization
    layer_filter = st.session_state.filter_layer
    
    for model_name, model_info in models_data.items():
        # Search filter
        if search_query:
            searchable_text = (
                model_name.lower() + " " +
                model_info.get('description', '').lower() + " " +
                " ".join(model_info.get('tags', [])).lower()
            )
            if search_query not in searchable_text:
                continue
        
        # Materialization filter
        if materialization_filter != "All":
            if model_info.get('materialization') != materialization_filter:
                continue
        
        # Layer filter (based on path)
        if layer_filter != "All":
            model_path = model_info.get('path', '')
            if layer_filter not in model_path:
                continue
        
        filtered[model_name] = model_info
    
    return filtered

def create_lineage_graph(selected_model: str, models_data: Dict[str, Any]) -> nx.DiGraph:
    """Create a networkx graph for model lineage"""
    
    G = nx.DiGraph()
    
    # Add the selected model and its immediate connections
    visited = set()
    
    def add_model_and_connections(model_name: str, depth: int = 0, max_depth: int = 2):
        if depth > max_depth or model_name in visited:
            return
        
        visited.add(model_name)
        
        if model_name in models_data:
            model_info = models_data[model_name]
            
            # Add node
            G.add_node(model_name, **model_info)
            
            # Add upstream dependencies
            for dep in model_info.get('depends_on', []):
                if dep in models_data:
                    G.add_edge(dep, model_name)
                    add_model_and_connections(dep, depth + 1, max_depth)
            
            # Add downstream references
            for ref in model_info.get('referenced_by', []):
                if ref in models_data:
                    G.add_edge(model_name, ref)
                    add_model_and_connections(ref, depth + 1, max_depth)
    
    add_model_and_connections(selected_model)
    
    return G

def create_lineage_plot(G: nx.DiGraph, selected_model: str) -> go.Figure:
    """Create a plotly figure for the lineage graph"""
    
    # Use spring layout for positioning
    pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Prepare node traces
    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        
        # Color nodes based on relationship to selected model
        if node == selected_model:
            node_colors.append('blue')
        elif node in G.predecessors(selected_model):
            node_colors.append('green')
        elif node in G.successors(selected_model):
            node_colors.append('orange')
        else:
            node_colors.append('lightgray')
    
    # Prepare edge traces
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Create figure
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='gray'),
        hoverinfo='none',
        mode='lines',
        showlegend=False
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="middle center",
        marker=dict(
            size=20,
            color=node_colors,
            line=dict(width=2, color='white')
        ),
        showlegend=False
    ))
    
    # Update layout
    fig.update_layout(
        title=f"Model Lineage: {selected_model}",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20,l=5,r=5,t=40),
        annotations=[
            dict(
                text="Drag to pan, scroll to zoom",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.005, y=-0.002,
                xanchor='left', yanchor='bottom',
                font=dict(color='gray', size=12)
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white'
    )
    
    return fig

def load_models_from_server(force_refresh: bool = False):
    """Load models from MCP server"""
    
    client = get_mcp_client()
    
    # Check connection first
    if not client.health_check():
        st.error("Cannot connect to MCP server. Please check if the server is running.")
        return
    
    # Load models
    success, models_data = client.get_models(force_refresh=force_refresh)
    
    if success:
        st.success(f"✅ Loaded {len(models_data)} models from MCP server")
        st.rerun()
    else:
        error_msg = models_data.get('message', 'Unknown error occurred')
        st.error(f"❌ Failed to load models: {error_msg}")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_cached_model_data():
    """Get cached model data with automatic refresh"""
    
    client = get_mcp_client()
    success, models_data = client.get_models()
    
    if success:
        return models_data
    else:
        return {}


def render_pagination_controls(total_pages: int, position: str):
    """Render pagination controls"""
    
    current_page = st.session_state.model_page
    
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⏮️ First", disabled=current_page == 1, key=f"first_{position}"):
            st.session_state.model_page = 1
            st.rerun()
    
    with col2:
        if st.button("◀️ Prev", disabled=current_page == 1, key=f"prev_{position}"):
            st.session_state.model_page = current_page - 1
            st.rerun()
    
    with col3:
        # Page selector
        page_options = list(range(1, total_pages + 1))
        selected_page = st.selectbox(
            f"Page {current_page} of {total_pages}",
            page_options,
            index=current_page - 1,
            key=f"page_select_{position}"
        )
        
        if selected_page != current_page:
            st.session_state.model_page = int(selected_page)
            st.rerun()
    
    with col4:
        if st.button("▶️ Next", disabled=current_page == total_pages, key=f"next_{position}"):
            st.session_state.model_page = current_page + 1
            st.rerun()
    
    with col5:
        if st.button("⏭️ Last", disabled=current_page == total_pages, key=f"last_{position}"):
            st.session_state.model_page = total_pages
            st.rerun()


def clear_all_filters():
    """Clear all search and filter criteria"""
    st.session_state.search_query = ""
    st.session_state.filter_materialization = "All"
    st.session_state.filter_layer = "All"
    st.session_state.model_page = 1
    st.rerun()


def optimize_model_data_loading():
    """Optimize model data loading with caching and lazy loading"""
    
    # Check if we need to refresh data
    cache_key = "models_cache_timestamp"
    cache_duration = 300  # 5 minutes
    
    import time
    current_time = time.time()
    last_cache_time = st.session_state.get(cache_key, 0)
    
    if current_time - last_cache_time > cache_duration:
        # Cache expired, refresh data
        with LoadingContext("models", "Refreshing model data..."):
            load_models_from_server(force_refresh=True)
        
        st.session_state[cache_key] = current_time


def render_model_performance_metrics():
    """Render performance metrics for the model explorer"""
    
    models_data = get_models_cache()
    
    if not models_data:
        return
    
    models = models_data.get('models', [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Models", len(models))
    
    with col2:
        # Count by materialization
        materializations = {}
        for model in models:
            mat = model.get('materialization', 'unknown')
            materializations[mat] = materializations.get(mat, 0) + 1
        
        most_common = max(materializations.items(), key=lambda x: x[1]) if materializations else ("N/A", 0)
        st.metric("Most Common Type", f"{most_common[0]} ({most_common[1]})")
    
    with col3:
        # Count models with tests
        models_with_tests = sum(1 for model in models if any(
            col.get('tests', []) for col in model.get('columns', [])
        ))
        st.metric("Models with Tests", models_with_tests)
    
    with col4:
        # Average columns per model
        total_columns = sum(len(model.get('columns', [])) for model in models)
        avg_columns = total_columns / len(models) if models else 0
        st.metric("Avg Columns", f"{avg_columns:.1f}")


def render_quick_stats():
    """Render quick statistics about the dbt project"""
    
    models_data = get_models_cache()
    
    if not models_data:
        return
    
    with st.expander("📊 Project Statistics", expanded=False):
        render_model_performance_metrics()
        
        # Column information status
        st.markdown("### Column Information Status")
        
        models = models_data.get('models', [])
        models_with_columns = sum(1 for model in models if model.get('columns'))
        models_without_columns = len(models) - models_with_columns
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("With Columns", models_with_columns)
        with col2:
            st.metric("Without Columns", models_without_columns)
        with col3:
            if models_without_columns > 0:
                st.warning(f"{models_without_columns} models missing column info")
            else:
                st.success("All models have column info")
        
        if models_without_columns > 0:
            st.info("💡 Add column definitions to schema.yml files and run `dbt compile` to see column information.")
        
        # Layer distribution
        st.markdown("### Model Distribution by Layer")
        
        layer_counts = {}
        
        for model in models:
            path = model.get('path', '')
            if 'staging' in path.lower():
                layer = 'Staging'
            elif 'intermediate' in path.lower():
                layer = 'Intermediate'
            elif 'marts' in path.lower():
                layer = 'Marts'
            else:
                layer = 'Other'
            
            layer_counts[layer] = layer_counts.get(layer, 0) + 1
        
        # Display as columns
        if layer_counts:
            cols = st.columns(len(layer_counts))
            for i, (layer, count) in enumerate(layer_counts.items()):
                with cols[i]:
                    st.metric(layer, count)


@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_model_search_index(models_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Create a search index for faster model searching"""
    
    search_index = {}
    models = models_data.get('models', [])
    
    for model in models:
        model_name = model.get('name', '')
        search_terms = []
        
        # Add name
        search_terms.append(model_name.lower())
        
        # Add description words
        description = model.get('description', '')
        if description:
            search_terms.extend(description.lower().split())
        
        # Add tags
        tags = model.get('tags', [])
        search_terms.extend([tag.lower() for tag in tags])
        
        # Add materialization
        materialization = model.get('materialization', '')
        if materialization:
            search_terms.append(materialization.lower())
        
        # Add path components
        path = model.get('path', '')
        if path:
            path_parts = path.lower().replace('/', ' ').replace('\\', ' ').split()
            search_terms.extend(path_parts)
        
        search_index[model_name] = search_terms
    
    return search_index


def fast_model_search(models_data: Dict[str, Any], query: str) -> List[str]:
    """Perform fast model search using the search index"""
    
    if not query:
        return [model.get('name', '') for model in models_data.get('models', [])]
    
    search_index = get_model_search_index(models_data)
    query_terms = query.lower().split()
    
    matching_models = []
    
    for model_name, search_terms in search_index.items():
        # Check if all query terms match
        if all(any(term in search_term for search_term in search_terms) for term in query_terms):
            matching_models.append(model_name)
    
    return matching_models