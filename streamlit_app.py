from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests
import streamlit as st


API_BASE = "http://localhost:8000"


def api_post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
    r.raise_for_status()
    if r.status_code == 204:
        return {}
    return r.json()


def api_get(path: str) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", timeout=30)
    r.raise_for_status()
    if r.status_code == 204:
        return {}
    return r.json()


st.set_page_config(page_title="Agent Forge Debug", layout="wide")

if "sessionId" not in st.session_state:
    st.session_state.sessionId = ""
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "docs_cache" not in st.session_state:
    st.session_state.docs_cache = []
if "history" not in st.session_state:
    st.session_state.history = {}


with st.sidebar:
    st.header("Session")
    session_input = st.text_input("sessionId", value=st.session_state.sessionId)
    if st.button("Open Session"):
        if not session_input:
            st.warning("Enter a sessionId")
        else:
            api_post("/open-session", {"sessionId": session_input})
            st.session_state.sessionId = session_input
            st.success("Session opened")

    st.divider()
    st.subheader("Agents")
    if st.session_state.agents:
        for sid, info in st.session_state.agents.items():
            st.caption(f"{sid}: {info}")


tab_create, tab_tools, tab_search, tab_chat, tab_task_executor = st.tabs(["Create Agent", "Available Tools", "Search Documentation", "Chat", "Task Executor"])

with tab_create:
    st.subheader("Create Agent")
    system_prompt = st.text_area("system_prompt", height=140)
    prompt_args = st.text_area("prompt_args (JSON object)", value="{}")
    opening_message = st.text_input("opening_message", value="")
    # Get available tools
    try:
        tools_response = api_get("/tools/names")
        available_tool_names = tools_response.get("tool_names", [])
        
        if available_tool_names:
            st.subheader("Available Tools")
            
            # Show tool descriptions
            tools_info_response = api_get("/tools")
            tools_info = {tool["name"]: tool for tool in tools_info_response.get("tools", [])}
            
            # Create columns for better layout
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_tools = st.multiselect(
                    "Select tools to enable for this agent",
                    options=available_tool_names,
                    help="Choose which tools this agent can use. The agent will automatically decide when to use each tool.",
                    key="tool_selection"
                )
                tools = selected_tools
            
            with col2:
                if selected_tools:
                    st.write("**Selected Tools:**")
                    for tool_name in selected_tools:
                        tool_info = tools_info.get(tool_name, {})
                        st.write(f"• **{tool_name}**: {tool_info.get('description', 'No description')}")
                else:
                    st.info("No tools selected. Agent will work without tools.")
        else:
            st.warning("No tools available. Check if the server is running properly.")
            tools = st.text_input("tools (JSON list)", value="[]")
            try:
                tools = json.loads(tools)
            except:
                tools = []
    except Exception as e:
        st.error(f"Failed to load tools: {str(e)}")
        tools = st.text_input("tools (JSON list)", value="[]")
        try:
            tools = json.loads(tools)
        except:
            tools = []
    st.subheader("Output Schema (Optional)")
    st.write("Define a JSON schema for how the agent should format its responses.")
    
    with st.expander("ℹ️ What is an Output Schema?", expanded=False):
        st.write("""
        **Output Schema** defines how the agent should structure its responses:
        
        - **JSON Schema Format**: Use standard JSON Schema syntax
        - **Response Formatting**: Agent will format responses according to this schema
        - **PydanticOutputParser**: Automatically generates format instructions for the LLM
        - **Validation**: Ensures responses match the expected structure
        
        Example:
        ```json
        {
          "type": "object",
          "properties": {
            "problem_summary": {"type": "string", "description": "Brief summary of the problem"},
            "urgency_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "next_steps": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["problem_summary", "urgency_level"]
        }
        ```
        """)
    
    # Example schema templates
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Problem Analysis Template", help="Template for problem analysis responses"):
            st.session_state.problem_analysis_schema = True
    
    with col2:
        if st.button("📊 Data Collection Template", help="Template for data collection responses"):
            st.session_state.data_collection_schema = True
    
    with col3:
        if st.button("🔧 Technical Support Template", help="Template for technical support responses"):
            st.session_state.tech_support_schema = True
    
    # Apply schema templates
    if hasattr(st.session_state, 'problem_analysis_schema') and st.session_state.problem_analysis_schema:
        output_schema = '''{
  "type": "object",
  "properties": {
    "problem_summary": {"type": "string", "description": "Brief summary of the problem"},
    "urgency_level": {"type": "string", "enum": ["low", "medium", "high"], "description": "How urgent is this problem"},
    "affected_systems": {"type": "array", "items": {"type": "string"}, "description": "Systems or components affected"},
    "next_steps": {"type": "array", "items": {"type": "string"}, "description": "Recommended next steps"}
  },
  "required": ["problem_summary", "urgency_level"]
}'''
        st.session_state.problem_analysis_schema = False
    elif hasattr(st.session_state, 'data_collection_schema') and st.session_state.data_collection_schema:
        output_schema = '''{
  "type": "object",
  "properties": {
    "collected_data": {"type": "object", "description": "All collected information"},
    "missing_fields": {"type": "array", "items": {"type": "string"}, "description": "Fields still needed"},
    "data_quality": {"type": "string", "enum": ["excellent", "good", "fair", "poor"], "description": "Quality of collected data"},
    "completion_status": {"type": "string", "enum": ["complete", "partial", "incomplete"], "description": "Data collection status"}
  },
  "required": ["collected_data", "completion_status"]
}'''
        st.session_state.data_collection_schema = False
    elif hasattr(st.session_state, 'tech_support_schema') and st.session_state.tech_support_schema:
        output_schema = '''{
  "type": "object",
  "properties": {
    "issue_diagnosis": {"type": "string", "description": "Diagnosis of the technical issue"},
    "root_cause": {"type": "string", "description": "Identified root cause"},
    "solution_steps": {"type": "array", "items": {"type": "string"}, "description": "Step-by-step solution"},
    "prevention_tips": {"type": "array", "items": {"type": "string"}, "description": "Tips to prevent this issue"}
  },
  "required": ["issue_diagnosis", "solution_steps"]
}'''
        st.session_state.tech_support_schema = False
    else:
        output_schema = ""
    
    output_schema = st.text_area(
        "JSON Schema for agent response format",
        value=output_schema,
        placeholder='{\n  "type": "object",\n  "properties": {\n    "problem_summary": {"type": "string"},\n    "urgency_level": {"type": "string"}\n  },\n  "required": ["problem_summary"]\n}',
        help="Enter a valid JSON Schema that defines how the agent should format its responses"
    )
    
    # Acceptance Criteria Section
    st.subheader("Acceptance Criteria (Optional)")
    st.write("Define criteria for when the agent should consider its task complete.")
    
    with st.expander("ℹ️ What are Acceptance Criteria?", expanded=False):
        st.write("""
        **Acceptance Criteria** help agents automatically determine when they've completed their objectives:
        
        - **Required Information**: Data the agent must collect (e.g., customer_name, issue_type)
        - **Completion Conditions**: Actions that must be completed (e.g., issue_categorized, solution_provided)
        - **Success Indicators**: Signs that objectives are achieved (e.g., customer_acknowledged_solution)
        
        When enabled, the agent will respond in a structured format and automatically evaluate its completion status.
        """)
    
    use_acceptance_criteria = st.checkbox("Enable completion evaluation", value=False)
    
    if use_acceptance_criteria:
        with st.container():
            # Example templates
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📞 Customer Service Template", help="Template for customer service agents"):
                    st.session_state.customer_service_template = True
            
            with col2:
                if st.button("📊 Data Collection Template", help="Template for data collection agents"):
                    st.session_state.data_collection_template = True
            
            with col3:
                if st.button("🔧 Technical Support Template", help="Template for technical support agents"):
                    st.session_state.tech_support_template = True
            
            # Apply templates
            if hasattr(st.session_state, 'customer_service_template') and st.session_state.customer_service_template:
                required_info = "customer_name\nissue_type\ncontact_method"
                completion_conditions = "issue_categorized\nnext_steps_provided"
                success_indicators = "customer_acknowledged_solution"
                st.session_state.customer_service_template = False
            elif hasattr(st.session_state, 'data_collection_template') and st.session_state.data_collection_template:
                required_info = "user_name\nemail_address\nphone_number\npreferences"
                completion_conditions = "all_fields_collected\ndata_validated"
                success_indicators = "user_confirmed_data"
                st.session_state.data_collection_template = False
            elif hasattr(st.session_state, 'tech_support_template') and st.session_state.tech_support_template:
                required_info = "problem_description\nsystem_info\nerror_messages"
                completion_conditions = "issue_diagnosed\nsolution_provided"
                success_indicators = "user_understands_solution"
                st.session_state.tech_support_template = False
            else:
                required_info = ""
                completion_conditions = ""
                success_indicators = ""
            
            st.write("**Required Information to Collect:**")
            required_info = st.text_area(
                "List of information fields the agent must collect (one per line)",
                value=required_info,
                placeholder="customer_name\nissue_type\ncontact_method",
                help="Each line should be a field name the agent needs to collect"
            )
            
            st.write("**Completion Conditions:**")
            completion_conditions = st.text_area(
                "List of conditions that must be met for completion (one per line)",
                value=completion_conditions,
                placeholder="issue_categorized\nnext_steps_provided",
                help="Each line should be a condition that must be satisfied"
            )
            
            st.write("**Success Indicators:**")
            success_indicators = st.text_area(
                "List of success indicators to look for (one per line)",
                value=success_indicators,
                placeholder="customer_acknowledged_solution",
                help="Each line should be a sign that the objective is achieved"
            )
            
            # Convert text areas to lists
            required_info_list = [line.strip() for line in required_info.split('\n') if line.strip()]
            completion_conditions_list = [line.strip() for line in completion_conditions.split('\n') if line.strip()]
            success_indicators_list = [line.strip() for line in success_indicators.split('\n') if line.strip()]
            
            # Create acceptance criteria object
            if required_info_list or completion_conditions_list or success_indicators_list:
                acceptance_criteria = {
                    "required_information": required_info_list if required_info_list else None,
                    "completion_conditions": completion_conditions_list if completion_conditions_list else None,
                    "success_indicators": success_indicators_list if success_indicators_list else None
                }
            else:
                acceptance_criteria = None
    else:
        acceptance_criteria = None
    
    llm_provider = st.selectbox("llm_provider", options=["bedrock", "openai"], index=0)
    llm_model = st.text_input("llm_model (optional)")

    st.markdown("Docs to attach:")
    search_text = st.text_input("search_text", key="create_search_text")
    k = st.number_input("number_of_results", min_value=1, max_value=10, value=3)
    if st.button("Search Docs", key="create_search_btn"):
        res = api_post("/search-documentation", {"search_text": search_text, "number_of_results": int(k)})
        st.session_state.docs_cache = res.get("results", [])
    attach = st.multiselect(
        "Select docs",
        options=[json.dumps(d) for d in st.session_state.docs_cache],
        format_func=lambda s: json.loads(s)["title"],
    )

    if st.button("Create Agent"):
        if not st.session_state.sessionId:
            st.warning("Open a session first")
        else:
            try:
                payload = {
                    "sessionId": st.session_state.sessionId,
                    "system_prompt": system_prompt,
                    "prompt_args": json.loads(prompt_args or "{}"),
                    "opening_message": opening_message or None,
                    "tools": tools if isinstance(tools, list) else json.loads(tools or "[]"),
                    "output_schema": output_schema or None,
                    "acceptance_criteria": acceptance_criteria,
                    "docs": [json.loads(a) for a in attach],
                    "llm_provider": llm_provider,
                    "llm_model": llm_model or None,
                }
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
            else:
                res = api_post("/create-agent", payload)
                agent_id = res.get("agentId")
                if agent_id:
                    st.success(f"Created agent {agent_id}")
                    st.session_state.agents.setdefault(st.session_state.sessionId, []).append(agent_id)

with tab_tools:
    st.subheader("Available Tools")
    st.write("These are all the tools available for agents to use. Select tools when creating an agent.")
    
    try:
        tools_response = api_get("/tools")
        available_tools = tools_response.get("tools", [])
        
        if available_tools:
            for tool in available_tools:
                with st.expander(f"🔧 {tool['name']}", expanded=False):
                    st.write(f"**Description:** {tool['description']}")
                    
                    # Show parameters if available
                    parameters = tool.get('parameters', {})
                    if parameters and 'properties' in parameters:
                        st.write("**Parameters:**")
                        for param_name, param_info in parameters['properties'].items():
                            param_type = param_info.get('type', 'unknown')
                            param_desc = param_info.get('description', 'No description')
                            required = param_name in parameters.get('required', [])
                            required_text = " (required)" if required else " (optional)"
                            st.write(f"  - `{param_name}` ({param_type}){required_text}: {param_desc}")
                    else:
                        st.write("**Parameters:** No detailed parameter information available")
                    
                    # Show example usage
                    if tool['name'] == 'calculator':
                        st.code("Example: calculator('2 + 3 * 4')")
                    elif tool['name'] == 'file_read':
                        st.code("Example: file_read('README.md')")
                    elif tool['name'] == 'file_write':
                        st.code("Example: file_write('output.txt', 'Hello World')")
                    elif tool['name'] == 'rest_api_request':
                        st.code("Example: rest_api_request('https://api.example.com/users', 'GET')")
                    elif tool['name'] == 'get_request':
                        st.code("Example: get_request('https://api.example.com/users')")
                    elif tool['name'] == 'post_request':
                        st.code("Example: post_request('https://api.example.com/users', {'name': 'John'})")
                    elif tool['name'] == 'put_request':
                        st.code("Example: put_request('https://api.example.com/users/1', {'name': 'Jane'})")
                    elif tool['name'] == 'patch_request':
                        st.code("Example: patch_request('https://api.example.com/users/1', {'name': 'Bob'})")
                    elif tool['name'] == 'delete_request':
                        st.code("Example: delete_request('https://api.example.com/users/1')")
        else:
            st.warning("No tools available. Check if the server is running properly.")
            
    except Exception as e:
        st.error(f"Failed to load tools: {str(e)}")

with tab_search:
    st.subheader("Search Documentation")
    s = st.text_input("search_text", key="search_text_tab")
    k2 = st.number_input("number_of_results", min_value=1, max_value=10, value=5, key="k2")
    if st.button("Search", key="search_btn_tab"):
        res = api_post("/search-documentation", {"search_text": s, "number_of_results": int(k2)})
        st.session_state.docs_cache = res.get("results", [])
    for d in st.session_state.docs_cache:
        with st.expander(d["title"]):
            try:
                content_res = api_post("/get-document", {"doc_pointer": d})
                st.code(content_res.get("content", ""))
            except Exception as e:
                st.error(str(e))

with tab_chat:
    st.subheader("Chat")
    sid = st.text_input("sessionId", value=st.session_state.sessionId, key="chat_sid")
    agents = st.session_state.agents.get(sid, [])
    agent = st.selectbox("agentId", options=agents)
    user_message = st.text_area("user_message", height=120)
    user_args = st.text_input("user_args (JSON list)", value="[]")
    if st.button("Send"):
        try:
            payload = {
                "sessionId": sid,
                "agentId": agent,
                "user_message": user_message,
                "user_args": json.loads(user_args or "[]"),
            }
        except Exception as e:
            st.error(f"Invalid JSON: {e}")
        else:
            res = api_post("/chat", payload)
            reply = res.get("agent_response", "")
            system_status = res.get("system_status")
            schema_success = res.get("schema_success")
            
            # Display the agent response
            st.write(reply)
            
            # Display schema success status if available
            if schema_success is not None:
                if schema_success:
                    st.success("✅ Response formatted successfully according to schema")
                else:
                    st.warning("⚠️ Response formatting failed - using original format")
            
            # Display system status if available (completion evaluation)
            if system_status:
                if system_status == "complete":
                    st.success(f"🎉 Agent Status: {system_status.upper()} - Agent has completed its objectives!")
                else:
                    st.info(f"🔄 Agent Status: {system_status.upper()} - Agent is continuing to work...")


with tab_task_executor:
    st.subheader("Task Executor Agent")
    st.write("Execute tasks automatically using the Task Executor Agent. This agent can find suitable tasks, map inputs intelligently, and execute them.")
    
    # Task Executor Status
    st.subheader("Agent Status")
    try:
        status_response = api_get("/api/task-executor/status")
        if status_response.get("status") == "running":
            st.success("✅ Task Executor Agent is running")
            
            # Display status information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", status_response.get("status", "Unknown"))
            with col2:
                uptime = status_response.get("uptime", 0)
                st.metric("Uptime", f"{uptime:.1f}s")
            with col3:
                st.metric("Version", status_response.get("version", "Unknown"))
            
            # Display configuration
            with st.expander("Configuration Details", expanded=False):
                st.write(f"**Task Executor URL:** {status_response.get('task_executor_url', 'Not configured')}")
                st.write(f"**Current Runtime Context:** {status_response.get('current_runtime_context', 'None')}")
        else:
            st.error("❌ Task Executor Agent is not running")
    except Exception as e:
        st.error(f"Failed to get Task Executor status: {str(e)}")
        st.info("Make sure the Task Executor Agent is properly initialized in the server.")
    
    st.divider()
    
    # Task Execution Interface
    st.subheader("Execute Task")
    
    # Action Description
    action_description = st.text_area(
        "Action Description",
        placeholder="Describe what you want to accomplish (e.g., 'Send an email to john@example.com about the project update')",
        help="Provide a clear description of the action you want to perform. The agent will find the most suitable task and execute it.",
        height=100
    )
    
    # Context ID
    context_id = st.text_input(
        "Context ID",
        value="user-123",
        help="Runtime context identifier for variable retrieval and task execution"
    )
    
    # Example actions
    with st.expander("💡 Example Actions", expanded=False):
        st.write("Here are some example actions you can try:")
        
        examples = [
            "Send an email to john@example.com about the project update",
            "Create a PDF report with the quarterly sales data",
            "Schedule a team meeting for tomorrow at 2 PM",
            "Analyze the customer data from the database",
            "Process the payment information for order #12345",
            "Generate a summary of last week's activities"
        ]
        
        for i, example in enumerate(examples, 1):
            if st.button(f"Use Example {i}", key=f"example_{i}"):
                st.session_state.example_action = example
                st.rerun()
        
        if hasattr(st.session_state, 'example_action'):
            action_description = st.session_state.example_action
            st.session_state.example_action = None
    
    # Execute button
    if st.button("🚀 Execute Task", type="primary"):
        if not action_description.strip():
            st.warning("Please enter an action description")
        else:
            try:
                # Execute the task
                with st.spinner("Executing task..."):
                    execute_payload = {
                        "action_description": action_description,
                        "context_id": context_id
                    }
                    
                    execute_response = api_post("/api/task-executor/execute", execute_payload)
                
                # Display results
                if execute_response.get("success"):
                    st.success("✅ Task executed successfully!")
                    
                    # Display execution details
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Execution Time", f"{execute_response.get('execution_time', 0):.2f}s")
                    
                    with col2:
                        st.metric("Success", "Yes")
                    
                    # Display task information
                    task_info = execute_response.get("task_info", {})
                    if task_info:
                        st.subheader("Task Information")
                        st.write(f"**Task ID:** {task_info.get('task_id', 'Unknown')}")
                        st.write(f"**Task Name:** {task_info.get('task_name', 'Unknown')}")
                        st.write(f"**Description:** {task_info.get('description', 'No description')}")
                    
                    # Display mapped inputs
                    mapped_inputs = execute_response.get("mapped_inputs", {})
                    if mapped_inputs:
                        st.subheader("Input Mappings")
                        for input_name, mapping in mapped_inputs.items():
                            with st.expander(f"Input: {input_name}", expanded=False):
                                st.write(f"**Value:** {mapping.get('value', 'N/A')}")
                                st.write(f"**Assignment Type:** {mapping.get('assignment_type', 'N/A')}")
                                if mapping.get('variable_id'):
                                    st.write(f"**Variable ID:** {mapping.get('variable_id')}")
                    
                    # Display execution result
                    result = execute_response.get("result", {})
                    if result:
                        st.subheader("Execution Result")
                        st.json(result)
                
                else:
                    st.error("❌ Task execution failed")
                    error_message = execute_response.get("error_message", "Unknown error")
                    st.error(f"Error: {error_message}")
                    
                    # Display execution time even for failed tasks
                    execution_time = execute_response.get("execution_time", 0)
                    if execution_time > 0:
                        st.info(f"Execution time: {execution_time:.2f}s")
                
            except Exception as e:
                st.error(f"Failed to execute task: {str(e)}")
    
    st.divider()
    
    # Task Executor Tools
    st.subheader("Available Tools")
    st.write("The Task Executor Agent uses these tools to interact with the task executor server:")
    
    try:
        tools_response = api_get("/api/task-executor/tools")
        tools = tools_response.get("tools", [])
        
        if tools:
            for tool in tools:
                with st.expander(f"🔧 {tool.get('name', 'Unknown Tool')}", expanded=False):
                    st.write(f"**Description:** {tool.get('description', 'No description')}")
                    
                    # Show parameters if available
                    parameters = tool.get('parameters', {})
                    if parameters and 'properties' in parameters:
                        st.write("**Parameters:**")
                        for param_name, param_info in parameters['properties'].items():
                            param_type = param_info.get('type', 'unknown')
                            param_desc = param_info.get('description', 'No description')
                            required = param_name in parameters.get('required', [])
                            required_text = " (required)" if required else " (optional)"
                            st.write(f"  - `{param_name}` ({param_type}){required_text}: {param_desc}")
                    else:
                        st.write("**Parameters:** No detailed parameter information available")
        else:
            st.info("No tools available. The Task Executor Agent may not be properly initialized.")
            
    except Exception as e:
        st.error(f"Failed to load Task Executor tools: {str(e)}")
    
    st.divider()
    
    # Health Check
    st.subheader("Health Check")
    try:
        health_response = api_get("/api/task-executor/health")
        if health_response.get("status") == "healthy":
            st.success("✅ Task Executor Agent is healthy")
        else:
            st.warning("⚠️ Task Executor Agent health check failed")
    except Exception as e:
        st.error(f"Health check failed: {str(e)}")

