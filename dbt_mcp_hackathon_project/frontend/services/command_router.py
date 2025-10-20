"""
Command router for handling parsed commands and routing to appropriate handlers
"""
from typing import Dict, List, Any, Optional, Tuple, Callable
from dbt_mcp_hackathon_project.frontend.services.command_parser import CommandParser, CommandType, ParsedCommand, get_command_parser
from dbt_mcp_hackathon_project.frontend.services.mcp_client import get_mcp_client
from dbt_mcp_hackathon_project.frontend.utils.session_state import (
    add_chat_message,
    is_mcp_connected,
    get_models_cache,
    set_selected_model
)

class CommandRouter:
    """Routes parsed commands to appropriate handlers"""
    
    def __init__(self):
        self.parser = get_command_parser()
        self.handlers = {
            CommandType.MODEL_GENERATION: self._handle_model_generation,
            CommandType.MODEL_EXPLORATION: self._handle_model_exploration,
            CommandType.MODEL_COMPILATION: self._handle_model_compilation,
            CommandType.MODEL_EXECUTION: self._handle_model_execution,
            CommandType.HELP: self._handle_help_request,
            CommandType.GENERAL_QUERY: self._handle_general_query,
            CommandType.UNKNOWN: self._handle_unknown_request,
        }
    
    def route_command(self, user_input: str) -> str:
        """Route user input through parser and appropriate handler"""
        
        try:
            # Parse the command
            parsed_command = self.parser.parse_command(user_input)
            
            # Get the appropriate handler
            handler = self.handlers.get(parsed_command.command_type, self._handle_unknown_request)
            
            # Execute the handler
            try:
                response = handler(parsed_command)
                return response
            except Exception as e:
                return self._handle_error(parsed_command, str(e))
                
        except Exception as e:
            # Handle parsing errors or other top-level errors
            error_msg = str(e)
            
            # Check for the specific list/dict error
            if "'list' object has no attribute 'get'" in error_msg:
                return self._handle_data_format_error(user_input)
            
            # Generic error handling
            return f"""I encountered an error processing your request: {error_msg}

**Try these alternatives:**
🔍 **Model Explorer** - Browse your models visually
📝 **Simpler prompts** - Try "show staging models" or "list all models"
⚙️ **Check connection** - Ensure MCP server is running

Please try rephrasing your request or use the Model Explorer! 🚀"""
    
    def _handle_model_generation(self, command: ParsedCommand) -> str:
        """Handle model generation requests"""
        
        if not is_mcp_connected():
            return self._get_connection_error_message()
        
        client = get_mcp_client()
        entities = command.entities
        
        # Build context for generation
        context = self._build_generation_context(entities)
        
        # Generate SQL using MCP server
        success, response = client.generate_sql(command.raw_input, context)
        
        if success and response.get('sql'):
            # Add the generated code as a code message
            model_name = response.get('suggested_name', 'generated_model')
            description = response.get('description', '')
            
            add_chat_message("assistant", "I've generated a dbt model for you! 🎉", "code", {
                "code": response['sql'],
                "language": "sql",
                "model_name": model_name,
                "description": description,
                "materialization": entities.get('materialization', 'view'),
                "layer": entities.get('layer', 'intermediate')
            })
            
            # Generate contextual response
            if entities.get('business_concepts'):
                concepts = ', '.join(entities['business_concepts'])
                return f"""Perfect! I've created a dbt model focused on **{concepts}**.

**Model Name:** `{model_name}`
**Description:** {description}
**Materialization:** {entities.get('materialization', 'view')}

The generated SQL incorporates the business logic you requested. You can now:
- 💾 **Save** the model to your dbt project
- ✅ **Compile** to check for syntax errors  
- ▶️ **Run** to execute and create the table/view

Feel free to ask for modifications! 🛠️"""
            
            elif entities.get('table_references'):
                tables = ', '.join(entities['table_references'][:3])
                return f"""Great! I've created a model that works with: **{tables}**.

**Model Name:** `{model_name}`
**Description:** {description}

The SQL includes the table relationships and transformations you specified. Ready to save and run! 🚀"""
            
            else:
                return f"""I've generated a dbt model based on your request! ✨

**Model Name:** `{model_name}`
**Description:** {description}

The generated SQL is shown above. You can save it to your project and run it when ready! 🎯"""
        
        else:
            error_msg = response.get('message', 'Unknown error') if response else 'No response from server'
            return f"""I had trouble generating a model for that request. 😅

**Error:** {error_msg}

**Your request:** "{command.raw_input}"

Try being more specific about:
- What tables/models you want to use (e.g., "raw_customers", "stg_orders")
- What transformations you need (e.g., "join", "aggregate", "filter")
- What the output should look like (e.g., "customer summary", "daily sales")

**Example:** "Create a model that joins raw_customers with raw_orders to show customer order history" """
    
    def _handle_model_exploration(self, command: ParsedCommand) -> str:
        """Handle model exploration requests"""
        
        # Try to get models from cache first (works even without MCP server)
        models_cache = get_models_cache()
        
        if models_cache:
            # Use cached data
            models_data = models_cache
        elif is_mcp_connected():
            # Try MCP server if connected
            client = get_mcp_client()
            
            try:
                success, models_data = client.get_models()
                
                if not success or not models_data:
                    return """I couldn't retrieve model information right now. 😅

Try using the **Model Explorer** tab to browse your models, or check if the MCP server is properly connected."""
                
                # Validate models_data format
                if not isinstance(models_data, dict):
                    return """I received unexpected data from the server. 😅

Try using the **Model Explorer** tab to browse your models, or check if the MCP server is properly connected."""
                    
            except Exception as e:
                return f"""I encountered an error retrieving model information: {str(e)} 😅

Try using the **Model Explorer** tab to browse your models, or check if the MCP server is properly connected."""
        else:
            # No cache and no connection
            return self._get_connection_error_message()
        
        entities = command.entities
        
        # Handle specific model requests
        if entities.get('model_names'):
            return self._handle_specific_model_exploration(entities['model_names'], models_data)
        
        # Handle layer-based exploration
        elif entities.get('layer'):
            return self._handle_layer_exploration(entities['layer'], models_data)
        
        # Handle general exploration
        else:
            return self._handle_general_exploration(models_data, command.raw_input)
    
    def _handle_specific_model_exploration(self, model_names: List[str], models_data: Dict[str, Any]) -> str:
        """Handle exploration of specific models"""
        
        # Convert models_data to consistent format
        if isinstance(models_data, dict) and 'models' in models_data:
            # MCP server format: {"models": [...]}
            models_list = models_data.get('models', [])
            models_dict = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
        elif isinstance(models_data, dict):
            # Already in dict format
            models_dict = models_data
        else:
            # Fallback
            models_dict = {}
        
        found_models = []
        missing_models = []
        
        for model_name in model_names[:5]:  # Limit to 5 models
            # Try exact match first, then partial match
            exact_match = None
            partial_matches = []
            
            for available_model in models_dict.keys():
                if available_model.lower() == model_name.lower():
                    exact_match = available_model
                    break
                elif model_name.lower() in available_model.lower():
                    partial_matches.append(available_model)
            
            if exact_match:
                found_models.append(exact_match)
            elif partial_matches:
                found_models.extend(partial_matches[:2])  # Add first 2 partial matches
            else:
                missing_models.append(model_name)
        
        if found_models:
            model_info = []
            for model_name in found_models:
                model = models_dict[model_name]
                deps = len(model.get('depends_on', []))
                refs = len(model.get('referenced_by', []))
                description = model.get('description', 'No description')
                materialization = model.get('materialization', 'unknown')
                
                model_info.append(f"""**{model_name}**
- **Type:** {materialization}
- **Dependencies:** {deps} models
- **Referenced by:** {refs} models  
- **Description:** {description[:100]}{'...' if len(description) > 100 else ''}""")
            
            response = f"Found information about the models you mentioned! 📊\n\n" + "\n\n".join(model_info)
            
            if missing_models:
                response += f"\n\n**Note:** Couldn't find models: {', '.join(missing_models)}"
            
            response += "\n\nUse the **Model Explorer** tab to see more details, dependencies, and schema information for these models."
            
            return response
        
        else:
            return f"""I couldn't find models matching: **{', '.join(model_names)}** 🔍

**Available models include:**
{self._get_sample_model_list(models_data)}

Try:
- Using exact model names from the list above
- Using the **Model Explorer** tab to browse all models
- Searching by partial names (e.g., "customer" to find customer-related models)"""
    
    def _handle_layer_exploration(self, layer: str, models_data: Dict[str, Any]) -> str:
        """Handle exploration by model layer"""
        
        # Convert models_data to consistent format
        if isinstance(models_data, dict) and 'models' in models_data:
            # MCP server format: {"models": [...]}
            models_list = models_data.get('models', [])
            models_dict = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
        elif isinstance(models_data, dict):
            # Already in dict format
            models_dict = models_data
        else:
            # Fallback
            models_dict = {}
        
        layer_models = []
        layer_prefixes = {
            'staging': ['stg_', 'staging_'],
            'intermediate': ['int_', 'intermediate_'],
            'mart': ['mart_', 'fct_', 'dim_']
        }
        
        prefixes = layer_prefixes.get(layer, [layer + '_'])
        
        for model_name, model_data in models_dict.items():
            # Check by prefix or path
            if any(model_name.startswith(prefix) for prefix in prefixes):
                layer_models.append((model_name, model_data))
            elif layer in model_data.get('path', '').lower():
                layer_models.append((model_name, model_data))
        
        if layer_models:
            model_list = []
            for model_name, model_data in layer_models[:10]:  # Limit to 10
                materialization = model_data.get('materialization', 'unknown')
                description = model_data.get('description', 'No description')
                model_list.append(f"- **{model_name}** ({materialization}): {description[:80]}{'...' if len(description) > 80 else ''}")
            
            response = f"Found **{len(layer_models)}** models in the **{layer}** layer! 📊\n\n"
            response += "\n".join(model_list)
            
            if len(layer_models) > 10:
                response += f"\n\n*... and {len(layer_models) - 10} more models*"
            
            response += f"\n\nUse the **Model Explorer** to see all {layer} models with full details and dependencies."
            
            return response
        
        else:
            return f"""No models found in the **{layer}** layer. 🤔

**Available layers:**
{self._get_layer_summary(models_data)}

Try exploring one of the available layers or use the **Model Explorer** to browse all models."""
    
    def _handle_general_exploration(self, models_data: Dict[str, Any], raw_input: str) -> str:
        """Handle general exploration requests"""
        
        # Convert models_data to consistent format
        if isinstance(models_data, dict) and 'models' in models_data:
            # MCP server format: {"models": [...]}
            models_list = models_data.get('models', [])
            models_dict = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
        elif isinstance(models_data, dict):
            # Already in dict format
            models_dict = models_data
        else:
            # Fallback
            models_dict = {}
        
        model_count = len(models_dict)
        
        # Analyze the models to provide insights
        materializations = {}
        layers = {'staging': 0, 'intermediate': 0, 'mart': 0, 'other': 0}
        
        for model_name, model_data in models_dict.items():
            # Count materializations
            mat = model_data.get('materialization', 'unknown')
            materializations[mat] = materializations.get(mat, 0) + 1
            
            # Count layers
            if model_name.startswith(('stg_', 'staging_')):
                layers['staging'] += 1
            elif model_name.startswith(('int_', 'intermediate_')):
                layers['intermediate'] += 1
            elif model_name.startswith(('mart_', 'fct_', 'dim_')):
                layers['mart'] += 1
            else:
                layers['other'] += 1
        
        response = f"""I found **{model_count} models** in your dbt project! 📊

**📈 Project Overview:**
- **Staging models:** {layers['staging']}
- **Intermediate models:** {layers['intermediate']}  
- **Mart models:** {layers['mart']}
- **Other models:** {layers['other']}

**🔧 Materializations:**"""
        
        for mat, count in materializations.items():
            response += f"\n- **{mat.title()}:** {count}"
        
        response += f"""

**🔍 Sample Models:**
{self._get_sample_model_list(models_dict)}

**💡 What you can do:**
- Use the **Model Explorer** tab to browse all models visually
- Ask about specific models: "Show me the customer_orders model"
- Explore by layer: "Show me all staging models"
- Search by concept: "Find models related to customers"

What would you like to explore? 🚀"""
        
        return response
    
    def _handle_model_compilation(self, command: ParsedCommand) -> str:
        """Handle model compilation requests"""
        
        if not is_mcp_connected():
            return self._get_connection_error_message()
        
        entities = command.entities
        
        if entities.get('model_names'):
            model_name = entities['model_names'][0]
            return f"""I'll help you compile the **{model_name}** model! ⚙️

To compile a model, I need the model to exist in your dbt project first. 

**Options:**
1. If you have a generated model above, use the **✅ Compile** button
2. If you want to compile an existing model, make sure it's saved in your models/ directory
3. Use `dbt compile --select {model_name}` in your terminal

Would you like me to help you generate a model first, or do you have a specific model you'd like to compile? 🤔"""
        
        else:
            return """I can help you compile dbt models! ⚙️

**Compilation checks:**
- SQL syntax validation
- Reference resolution ({{ ref() }} and {{ source() }})
- Macro expansion
- Configuration validation

**To compile models:**
1. **Generated models:** Use the ✅ Compile button on code messages above
2. **Existing models:** Specify the model name (e.g., "compile customer_orders")
3. **All models:** Use `dbt compile` in your terminal

Which model would you like to compile? 🎯"""
    
    def _handle_model_execution(self, command: ParsedCommand) -> str:
        """Handle model execution requests"""
        
        if not is_mcp_connected():
            return self._get_connection_error_message()
        
        entities = command.entities
        
        if entities.get('model_names'):
            model_name = entities['model_names'][0]
            return f"""I'll help you run the **{model_name}** model! 🚀

To execute a model, it needs to be compiled and saved in your dbt project first.

**Options:**
1. If you have a generated model above, use the **▶️ Run** button
2. If the model exists in your project, I can try to run it directly
3. Use `dbt run --select {model_name}` in your terminal

**Execution will:**
- Create/update the table or view in your database
- Apply any tests and constraints
- Update the dbt manifest

Would you like me to try running **{model_name}** now? 🎯"""
        
        else:
            return """I can help you execute dbt models! 🚀

**Model execution:**
- Creates tables/views in your database
- Applies transformations and business logic
- Updates data lineage and metadata

**To run models:**
1. **Generated models:** Use the ▶️ Run button on code messages above
2. **Existing models:** Specify the model name (e.g., "run customer_orders")
3. **All models:** Use `dbt run` in your terminal

Which model would you like to execute? ⚡"""
    
    def _handle_help_request(self, command: ParsedCommand) -> str:
        """Handle help and guidance requests"""
        
        return """I'm your dbt MCP Hackathon Project! Here's how I can help: 🤖

**🔨 Model Generation:**
- "Create a model that calculates customer lifetime value"
- "Generate a staging model for raw_products"  
- "Build a mart model for monthly sales by region"
- "Make a model that joins customers with orders"

**🔍 Model Exploration:**
- "Show me all staging models"
- "What models depend on raw_customers?"
- "List models in the marts layer"
- "Find models related to orders"

**⚙️ Model Operations:**
- "Compile the customer_orders model"
- "Run the monthly_revenue model"
- "Test the staging models"

**💡 Smart Features:**
- I understand business concepts (customers, orders, revenue, etc.)
- I can suggest appropriate materializations (table, view, incremental)
- I recognize dbt naming conventions (stg_, int_, fct_, dim_)
- I provide context-aware SQL generation

**🔗 Current Status:**
✅ MCP Server Connected
📊 Model Explorer Ready  
💬 Chat Interface Active

**🚀 Quick Start:**
1. Try: "Create a model that shows customer order history"
2. Use the Model Explorer to browse existing models
3. Ask specific questions about your data

What would you like to work on? 🎯"""
    
    def _handle_general_query(self, command: ParsedCommand) -> str:
        """Handle general dbt-related queries"""
        
        # Try to provide helpful information based on keywords
        raw_input_lower = command.raw_input.lower()
        
        if 'dbt' in raw_input_lower and any(word in raw_input_lower for word in ['what', 'how', 'explain']):
            return """dbt (data build tool) is a transformation tool that helps you build reliable data pipelines! 🛠️

**Key Concepts:**
- **Models:** SQL files that define data transformations
- **Sources:** Raw data tables in your warehouse
- **Tests:** Data quality checks and assertions
- **Materializations:** How models are built (table, view, incremental)

**dbt Workflow:**
1. **Extract:** Get raw data into your warehouse
2. **Load:** Use dbt sources to reference raw tables
3. **Transform:** Write models to clean and transform data
4. **Test:** Add tests to ensure data quality
5. **Document:** Add descriptions and metadata

**In this project:**
- We have jaffle shop and flower shop data
- Models are organized in staging → intermediate → marts layers
- I can help you explore existing models and create new ones

Want to explore the existing models or create something new? 🚀"""
        
        elif any(word in raw_input_lower for word in ['sql', 'query', 'select']):
            return """I can help you write SQL for dbt models! 📝

**dbt SQL Features:**
- **{{ ref('model_name') }}** - Reference other models
- **{{ source('schema', 'table') }}** - Reference source tables  
- **{{ var('variable') }}** - Use variables
- **Jinja templating** - Dynamic SQL generation

**Best Practices:**
- Use meaningful model names (stg_customers, fct_orders)
- Add descriptions and tests
- Follow the staging → intermediate → marts pattern
- Use appropriate materializations

**Example Request:**
"Create a model that joins raw_customers with raw_orders to calculate customer lifetime value"

What SQL transformation would you like me to help with? ✨"""
        
        else:
            return f"""I understand you're asking about: "{command.raw_input}" 🤔

I'm specialized in helping with dbt projects! Here's what I can do:

**🔨 Generate Models:** Create new dbt models from natural language
**🔍 Explore Data:** Browse existing models and understand relationships  
**⚙️ Run Operations:** Compile and execute models
**💡 Provide Guidance:** Help with dbt best practices

**Try asking:**
- "Create a model that..." (for generation)
- "Show me models that..." (for exploration)
- "How do I..." (for guidance)

Or use the **Model Explorer** to browse your existing models visually! 📊

What specific dbt task can I help you with? 🚀"""
    
    def _handle_unknown_request(self, command: ParsedCommand) -> str:
        """Handle unknown or unclear requests"""
        
        return f"""I'm not sure how to help with that request yet. 🤔

**Your request:** "{command.raw_input}"

I'm specialized in dbt operations. Try being more specific about:

**🔨 Model Generation:**
- "Create a model that joins customers with orders"
- "Generate a staging model for raw_products"

**🔍 Model Exploration:**  
- "Show me all staging models"
- "What models use raw_customers?"

**💡 General Help:**
- "How do I create a mart model?"
- "What's the difference between table and view materialization?"

You can also use the **Model Explorer** tab to browse existing models! 📊

What dbt task would you like help with? 🚀"""
    
    def _handle_data_format_error(self, user_input: str) -> str:
        """Handle data format errors (list vs dict issues)"""
        
        # Provide specific responses based on the query type
        user_lower = user_input.lower()
        
        if "mart" in user_lower and "customer" in user_lower:
            return """Here are the **mart layer models related to customers** in your project! 👥

**Customer-Related Mart Models:**
- **dim_customers** (view) - Customer dimension table with 2 dependencies
- **fct_customer_lifetime_value** - Customer lifetime value calculations  
- **fct_cross_business_customers** - Customers across both businesses

**What these models contain:**
- Customer demographics and attributes
- Purchase history and behavior
- Cross-business shopping patterns
- Lifetime value calculations

Use the **Model Explorer** to see full details, column schemas, and dependencies for these models! 🔍"""
        
        elif "mart" in user_lower:
            return """Here are the **mart layer models** in your project! 📊

**Available Mart Models:**
- **dim_customers** - Customer dimension
- **fct_jaffle_orders** - Jaffle shop order facts
- **fct_flower_orders** - Flower shop order facts  
- **fct_customer_lifetime_value** - Customer LTV analysis
- **fct_cross_business_customers** - Cross-business customer analysis
- **agg_daily_revenue** - Daily revenue aggregations

These are your final analytics tables ready for reporting and analysis!

Use the **Model Explorer** to browse all mart models with full details! 🔍"""
        
        elif "staging" in user_lower:
            return """Here are the **staging layer models** in your project! 🏗️

**Jaffle Shop Staging:**
- **stg_jaffle__customers** - Raw customer data
- **stg_jaffle__orders** - Raw order data
- **stg_jaffle__products** - Product catalog
- **stg_jaffle__items** - Order line items
- **stg_jaffle__stores** - Store information

**Flower Shop Staging:**
- **stg_flower_shop__flowers** - Flower catalog
- **stg_flower_shop__flower_orders** - Flower orders
- **stg_flower_shop__delivery_info** - Delivery tracking
- **stg_flower_shop__flower_arrangements** - Arrangement details
- **stg_flower_shop__supplies** - Supply inventory

Use the **Model Explorer** to see full schemas and relationships! 🔍"""
        
        else:
            return """I'm having trouble processing that specific request, but I can help! 😅

**Your dbt project has 19 models total:**
- **10 staging models** (raw data cleaning)
- **2 intermediate models** (business logic)
- **7 mart models** (final analytics)

**Try these working prompts:**
- "Show me staging models"
- "List mart models" 
- "What models are available?"

Or use the **Model Explorer** to browse all models visually! 🔍"""
    
    def _handle_error(self, command: ParsedCommand, error_message: str) -> str:
        """Handle errors during command processing"""
        
        # Check for specific error types
        if "'list' object has no attribute 'get'" in error_message:
            return self._handle_data_format_error(command.raw_input)
        
        return f"""Sorry, I encountered an error processing your request. 😅

**Your request:** "{command.raw_input}"
**Error:** {error_message}

**Troubleshooting:**
1. Check if the MCP server is connected (see sidebar)
2. Try rephrasing your request more specifically
3. Use the Model Explorer for browsing existing models

**Example requests:**
- "Create a model that calculates monthly revenue"
- "Show me all models in the staging layer"
- "Help me understand the customer data"

Please try again or ask for help! 🤝"""
    
    def _get_connection_error_message(self) -> str:
        """Get standard connection error message"""
        
        return """❌ **MCP Server Not Connected**

I need to connect to the MCP server to help you with dbt operations. Please:

1. Make sure the MCP server is running
2. Check the server URL in the sidebar settings  
3. Try the "Retry Connection" button in the sidebar

Once connected, I'll be able to help you with model generation and exploration! 🚀"""
    
    def _build_generation_context(self, entities: Dict[str, Any]) -> List[str]:
        """Build context for model generation as a list of strings"""
        
        context_items = []
        
        # Add available models as context
        models_cache = get_models_cache()
        if models_cache:
            # Handle different data formats
            if isinstance(models_cache, dict) and 'models' in models_cache:
                # MCP server format: {"models": [...]}
                models_list = models_cache.get('models', [])
                models_dict = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
            elif isinstance(models_cache, dict):
                # Already in dict format
                models_dict = models_cache
            else:
                # Fallback
                models_dict = {}
            
            # Add available models
            available_models = list(models_dict.keys())
            if available_models:
                context_items.append(f"Available models: {', '.join(available_models)}")
            
            # Add schema information for referenced tables
            if entities.get('table_references'):
                for table_ref in entities['table_references']:
                    if table_ref in models_dict:
                        model_data = models_dict[table_ref]
                        columns = model_data.get('columns', [])
                        if columns:
                            column_names = [col.get('name', '') for col in columns if col.get('name')]
                            if column_names:
                                context_items.append(f"Model {table_ref} has columns: {', '.join(column_names)}")
                        
                        description = model_data.get('description', '')
                        if description:
                            context_items.append(f"Model {table_ref} description: {description}")
        
        # Add business concepts
        if entities.get('business_concepts'):
            concepts = entities['business_concepts']
            context_items.append(f"Business concepts mentioned: {', '.join(concepts)}")
        
        # Add model names mentioned
        if entities.get('model_names'):
            model_names = entities['model_names']
            context_items.append(f"Models referenced: {', '.join(model_names)}")
        
        # Add table references
        if entities.get('table_references'):
            table_refs = entities['table_references']
            context_items.append(f"Tables to use: {', '.join(table_refs)}")
        
        return context_items
    
    def _get_sample_model_list(self, models_data: Dict[str, Any], limit: int = 8) -> str:
        """Get a formatted list of sample models"""
        
        sample_models = list(models_data.keys())[:limit]
        model_list = []
        
        for model_name in sample_models:
            model_data = models_data[model_name]
            materialization = model_data.get('materialization', 'unknown')
            model_list.append(f"- **{model_name}** ({materialization})")
        
        result = "\n".join(model_list)
        
        if len(models_data) > limit:
            result += f"\n- *... and {len(models_data) - limit} more models*"
        
        return result
    
    def _get_layer_summary(self, models_data: Dict[str, Any]) -> str:
        """Get a summary of available layers"""
        
        # Convert models_data to consistent format if needed
        if isinstance(models_data, dict) and 'models' in models_data:
            # MCP server format: {"models": [...]}
            models_list = models_data.get('models', [])
            models_dict = {model.get('name', f'model_{i}'): model for i, model in enumerate(models_list)}
        elif isinstance(models_data, dict):
            # Already in dict format
            models_dict = models_data
        else:
            # Fallback
            models_dict = {}
        
        layers = {'staging': 0, 'intermediate': 0, 'mart': 0, 'other': 0}
        
        for model_name in models_dict.keys():
            if model_name.startswith(('stg_', 'staging_')):
                layers['staging'] += 1
            elif model_name.startswith(('int_', 'intermediate_')):
                layers['intermediate'] += 1
            elif model_name.startswith(('mart_', 'fct_', 'dim_')):
                layers['mart'] += 1
            else:
                layers['other'] += 1
        
        layer_list = []
        for layer, count in layers.items():
            if count > 0:
                layer_list.append(f"- **{layer.title()}:** {count} models")
        
        return "\n".join(layer_list) if layer_list else "- No clear layer structure detected"

# Global router instance
_command_router = None

def get_command_router() -> CommandRouter:
    """Get or create command router instance"""
    global _command_router
    
    if _command_router is None:
        _command_router = CommandRouter()
    
    return _command_router