# app.py
import streamlit as st
import requests
import time

# Configuration
API_URL = "http://localhost:8000"  # Change to your deployed URL

def main():
    st.set_page_config(
        page_title="SHL Assessment Recommender",
        page_icon="📊",
        layout="wide"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .assessment-card {
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        .header {text-align: center;}
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="header">🔍 SHL Assessment Recommender</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Input Section
    with st.form("recommendation_form"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            query = st.text_area(
                "Describe your hiring needs:",
                placeholder="Example: Need cognitive and personality tests for analyst roles under 45 minutes...",
                height=100
            )
        
        # with col2:
        #     max_duration = st.slider(
        #         "Maximum duration (minutes):",
        #         min_value=10,
        #         max_value=MAX_DURATION,
        #         value=60
        #     )
            submitted = st.form_submit_button("Get Recommendations")

    # Handle Submission
    if submitted:
        if not query.strip():
            st.error("Please enter a valid job description")
            return
            
        with st.spinner("Finding the best assessments..."):
            try:
                response = requests.post(
                    f"{API_URL}/recommend",
                    json={
                        "query": query
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if not data["recommended_assessments"]:
                    st.warning("No matching assessments found. Try broadening your search.")
                    return
                
                # Display results
                st.markdown(f"**Found {len(data['recommended_assessments'])} recommendations:**")
                
                for assessment in data["recommended_assessments"]:
                    with st.container():
                        st.markdown(f"""
                        <div class="assessment-card">
                            <h3>{assessment['name']}</h3>
                            <p><b>Duration:</b> {assessment['duration']} mins</p>
                            <p><b>Test Types:</b> {', '.join(assessment['test_type'])}</p>
                            <p><b>Remote Support:</b> {assessment['remote_support']}</p>
                            <p><b>Adaptive Testing:</b> {assessment['adaptive_support']}</p>
                            <a href="{assessment['url']}" target="_blank">View Assessment Details →</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the API: {str(e)}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
