"""
Streamlit Web Application for Vibe-to-Attribute Clothing Recommendation System
"""

import streamlit as st
import sys
import os
from typing import Dict, Any, List


try:
    from recommendation_system import VibeRecommendationSystem
except ImportError as e:
    st.error(f"Failed to import recommendation system: {e}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Vibe Fashion Recommender",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for conversation
if 'recommendation_system' not in st.session_state:
    with st.spinner("🔄 Initializing Fashion Recommendation System..."):
        try:
            st.session_state.recommendation_system = VibeRecommendationSystem()
            st.session_state.system_initialized = True
        except Exception as e:
            st.session_state.system_initialized = False
            st.error(f"Failed to initialize system: {e}")

# Initialize conversation state
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'pending_attributes' not in st.session_state:
    st.session_state.pending_attributes = {}
if 'missing_attributes' not in st.session_state:
    st.session_state.missing_attributes = []
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = False

def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<h1 class="main-header">�� Vibe Fashion Recommender</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transform your style ideas into perfect outfit recommendations using AI</p>', unsafe_allow_html=True)
    
    # Check if system is initialized
    if not st.session_state.get('system_initialized', False):
        st.error("❌ System failed to initialize. Please refresh the page.")
        return
    
    # Sidebar - System Status Only
    with st.sidebar:
        st.header("📊 System Status")
        if st.button("Check Status"):
            status = st.session_state.recommendation_system.get_system_status()
            for component, status_msg in status.items():
                if "Ready" in status_msg or "Loaded" in status_msg:
                    st.success(f"✅ {component}: {status_msg}")
                else:
                    st.warning(f"⚠️ {component}: {status_msg}")
        
        st.markdown("---")
        st.markdown("**💡 Tip:** Tell me your size and budget in the conversation!")
        st.markdown("*Example: 'I need a size M dress under $100 for a party'*")
    

    
    # Chat interface for conversation
    st.header("💬 Fashion Chat")
    
    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("**Conversation History:**")
        chat_container = st.container()
        with chat_container:
            for i, exchange in enumerate(st.session_state.conversation_history):
                # User message
                st.markdown(f"**You:** {exchange['user']}")
                # Assistant response
                if exchange.get('assistant'):
                    st.markdown(f"**Assistant:** {exchange['assistant']}")
                if i < len(st.session_state.conversation_history) - 1:
                    st.markdown("---")
    
    # Current pending context
    if st.session_state.pending_attributes:
        st.info(f"💭 I remember: {', '.join([f'{k}: {v}' for k, v in st.session_state.pending_attributes.items()])}")
    
    # User input with form to handle clearing better
    with st.form(key="user_input_form", clear_on_submit=True):
        user_input = st.text_input(
            "Continue the conversation:" if st.session_state.conversation_active else "What are you looking for?",
            placeholder="Tell me more details..." if st.session_state.missing_attributes else "e.g., I want something elegant for a dinner date...",
            key="user_input_field"
        )
        send_button = st.form_submit_button("💬 Send", type="primary")
    
    # Buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 New Request"):
            # Reset conversation
            st.session_state.conversation_history = []
            st.session_state.pending_attributes = {}
            st.session_state.missing_attributes = []
            st.session_state.conversation_active = False
            st.rerun()
    
    with col2:
        if st.button("✨ Get Final Recommendations"):
            if st.session_state.pending_attributes:
                get_final_recommendations(st.session_state.pending_attributes, {})
            else:
                st.warning("Please start a conversation first!")
    
    # Process user input (now triggered by form submit)
    if send_button and user_input.strip():
        process_user_input(user_input, {})

def process_user_input(user_input: str, user_prefs: Dict[str, Any]):
    """Process user input in conversational context."""
    
    # Combine current input with pending attributes to form complete query
    if st.session_state.pending_attributes:
        # Build context from previous conversation
        context_parts = []
        for key, value in st.session_state.pending_attributes.items():
            if isinstance(value, list):
                context_parts.append(f"{key}: {', '.join(value)}")
            else:
                context_parts.append(f"{key}: {value}")
        
        # Combine context with new input
        combined_query = f"Previous context: {'; '.join(context_parts)}. New information: {user_input}"
    else:
        combined_query = user_input
    
    with st.spinner("🤖 Processing your message..."):
        try:
            # Get recommendations with combined context and pending attributes
            # Pass pending attributes as user preferences (highest priority)
            merged_prefs = user_prefs.copy()
            merged_prefs.update(st.session_state.pending_attributes)
            
            result = st.session_state.recommendation_system.get_recommendations(
                user_query=combined_query,
                user_preferences=merged_prefs
            )
            
            # Add to conversation history
            exchange = {"user": user_input}
            
            if result['success']:
                # Got successful recommendations
                exchange["assistant"] = result['recommendation']
                st.session_state.conversation_history.append(exchange)
                st.session_state.conversation_active = False
                st.session_state.pending_attributes = {}
                st.session_state.missing_attributes = []
                
                # Display recommendations
                display_recommendations(result)
                
            else:
                # Need more information - maintain conversation state
                exchange["assistant"] = result['message']
                st.session_state.conversation_history.append(exchange)
                st.session_state.conversation_active = True
                st.session_state.missing_attributes = result.get('missing_attributes', [])
                
                # Update pending attributes with what we know so far
                if 'final_attributes' in result:
                    st.session_state.pending_attributes.update(result['final_attributes'])
                
                # Extract new attributes from current input only (not combined query)
                try:
                    # Analyze just the current user input to extract new attributes
                    nlp_result = st.session_state.recommendation_system.nlp_analyzer.analyze_query(user_input)
                    if nlp_result and 'extracted_attributes' in nlp_result:
                        extracted = nlp_result['extracted_attributes']
                        for key, value in extracted.items():
                            if value and value not in [None, "", []]:
                                st.session_state.pending_attributes[key] = value
                                print(f"✓ Updated pending attributes from current input: {key} = {value}")
                                # Show debug info for size and budget specifically
                                if key in ['size', 'budget']:
                                    print(f"  {key.title()} type: {type(value)}, value: {repr(value)}")
                except Exception as e:
                    print(f"Error extracting attributes from current input: {e}")
                    pass
                
                # Show the assistant's response
                st.info(f"💬 **Assistant:** {exchange['assistant']}")
                
                # Show follow-up questions
                if 'suggested_questions' in result:
                    st.markdown("**To help me better, please answer:**")
                    for question in result['suggested_questions']:
                        st.write(f"• {question}")
                
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def get_final_recommendations(pending_attributes: Dict[str, Any], user_prefs: Dict[str, Any]):
    """Get final recommendations with accumulated attributes."""
    
    # Build a query from accumulated attributes
    query_parts = []
    for key, value in pending_attributes.items():
        if isinstance(value, list):
            query_parts.append(f"{key}: {', '.join(value)}")
        else:
            query_parts.append(f"{key}: {value}")
    
    combined_query = f"Find clothing with: {'; '.join(query_parts)}"
    
    with st.spinner("🤖 Getting your final recommendations..."):
        try:
            result = st.session_state.recommendation_system.get_recommendations(
                user_query=combined_query,
                user_preferences=user_prefs
            )
            
            if result['success']:
                # Reset conversation state
                st.session_state.conversation_active = False
                st.session_state.pending_attributes = {}
                st.session_state.missing_attributes = []
                
                # Display recommendations
                display_recommendations(result)
            else:
                st.error(f"Still missing information: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def get_recommendations(user_query: str, user_prefs: Dict[str, Any]):
    """Get and display recommendations (legacy function for compatibility)."""
    
    with st.spinner("🤖 Analyzing your request and finding perfect matches..."):
        try:
            result = st.session_state.recommendation_system.get_recommendations(
                user_query=user_query,
                user_preferences=user_prefs
            )
            
            display_recommendations(result)
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

def display_recommendations(result: Dict[str, Any]):
    """Display the recommendation results."""
    
    if result['success']:
        # Main recommendation
        st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
        st.markdown("### 🎉 Your Perfect Match!")
        st.markdown(result['recommendation'])
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Product details
        if result['products']:
            st.header("👕 Product Details")
            
            for i, product in enumerate(result['products']):
                with st.expander(f"🛍️ {product['name']} - ${product['price']}", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Category:** {product['category']}")
                        st.write(f"**Price:** ${product['price']}")
                        if product.get('fit'):
                            st.write(f"**Fit:** {product['fit']}")
                        if product.get('fabric'):
                            st.write(f"**Fabric:** {product['fabric']}")
                    
                    with col2:
                        if product.get('color_or_print'):
                            st.write(f"**Color/Print:** {product['color_or_print']}")
                        st.write(f"**Available Sizes:** {product['available_sizes']}")
                        if product.get('sleeve_length'):
                            st.write(f"**Sleeve Length:** {product['sleeve_length']}")
                        if product.get('neckline'):
                            st.write(f"**Neckline:** {product['neckline']}")
                        if product.get('length'):
                            st.write(f"**Length:** {product['length']}")
                        if product.get('pant_type'):
                            st.write(f"**Pant Type:** {product['pant_type']}")
                        if product.get('occasion'):
                            st.write(f"**Occasion:** {product['occasion']}")
                    
                    if product.get('description'):
                        st.write(f"**Description:** {product['description']}")
    
    else:
        st.error(result['message'])
        if 'suggested_questions' in result:
            st.markdown("**Please help me by answering:**")
            for question in result['suggested_questions']:
                st.write(f"• {question}")

if __name__ == "__main__":
    main()
