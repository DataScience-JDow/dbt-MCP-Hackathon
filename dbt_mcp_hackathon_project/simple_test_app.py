import streamlit as st
import requests
import json

st.set_page_config(page_title="dbt MCP Test", page_icon="🤖")

st.title("🤖 dbt MCP Hackathon Project - Test Interface")

# Test backend connection
st.header("Backend Connection Test")

try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        st.success("✅ Backend is connected!")
        health_data = response.json()
        st.json(health_data)
    else:
        st.error(f"❌ Backend connection failed: {response.status_code}")
except Exception as e:
    st.error(f"❌ Backend connection error: {e}")

# Test model listing
st.header("Models Test")
if st.button("List Models"):
    try:
        response = requests.get("http://localhost:8000/models", timeout=10)
        if response.status_code == 200:
            models = response.json()
            st.success(f"✅ Found {models.get('total_count', 0)} models")
            
            # Show first few models
            if models.get('models'):
                st.subheader("Sample Models:")
                for model in models['models'][:5]:
                    with st.expander(f"📊 {model['name']}"):
                        st.write(f"**Description:** {model.get('description', 'No description')}")
                        st.write(f"**Materialization:** {model.get('materialization', 'Unknown')}")
                        st.write(f"**Columns:** {len(model.get('columns', []))}")
        else:
            st.error(f"❌ Failed to fetch models: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error fetching models: {e}")

# Test AI status
st.header("AI Services Test")
if st.button("Check AI Status"):
    try:
        response = requests.get("http://localhost:8000/ai-status", timeout=5)
        if response.status_code == 200:
            ai_status = response.json()
            st.success("✅ AI services status retrieved")
            st.json(ai_status)
        else:
            st.error(f"❌ Failed to get AI status: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Error getting AI status: {e}")

# Simple model generation test
st.header("Model Generation Test")
prompt = st.text_area("Enter a model description:", 
                     value="Create a simple customer summary model")

if st.button("Generate Model (SQL Only)"):
    if prompt:
        try:
            payload = {
                "prompt": prompt,
                "materialization": "view"
            }
            response = requests.post("http://localhost:8000/generate", 
                                   json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                st.success("✅ Model generated successfully!")
                st.subheader("Generated SQL:")
                st.code(result.get('sql', 'No SQL generated'), language='sql')
                st.subheader("Details:")
                st.json({
                    "model_name": result.get('model_name'),
                    "description": result.get('description'),
                    "confidence": result.get('confidence'),
                    "reasoning": result.get('reasoning')
                })
            else:
                st.error(f"❌ Generation failed: {response.status_code}")
                st.text(response.text)
        except Exception as e:
            st.error(f"❌ Error generating model: {e}")
    else:
        st.warning("Please enter a model description")

st.markdown("---")
st.markdown("**Testing the dbt MCP Hackathon Project integration**")