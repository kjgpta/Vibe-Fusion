"""
Main Vibe-to-Attribute Clothing Recommendation System

Coordinates all modules to provide end-to-end fashion recommendations
from user queries to natural language suggestions.
"""

import os
import sys
from typing import Dict, List, Optional, Any

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.nlp_analyzer import NLPAnalyzer
from modules.similarity_matcher import SimilarityMatcher
from modules.gpt_inference import GPTInference
from modules.catalog_filter import CatalogFilter
from modules.nlg_generator import NLGGenerator

class VibeRecommendationSystem:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the complete recommendation system.
        
        Args:
            config: Configuration dictionary with system settings
        """
        self.config = config or {}
        
        # Initialize all modules
        self.nlp_analyzer = NLPAnalyzer()
        self.similarity_matcher = SimilarityMatcher(
            vibes_data_dir=self.config.get('vibes_data_dir', 'data/vibes/'),
            similarity_threshold=self.config.get('similarity_threshold', 0.8)
        )
        self.gpt_inference = GPTInference()
        self.catalog_filter = CatalogFilter(
            catalog_file=self.config.get('catalog_file', 'data/Apparels_shared.xlsx')
        )
        self.nlg_generator = NLGGenerator()
        
        print("✓ Vibe Recommendation System initialized successfully!")
    
    def get_recommendations(self, 
                          user_query: str,
                          user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main method to get clothing recommendations from a user query.
        
        Args:
            user_query: Natural language request from user
            user_preferences: Additional user preferences (size, budget, etc.)
            
        Returns:
            Dictionary containing recommendations and processing details
        """
        print(f"\n🔍 Processing query: '{user_query}'")
        
        # Step 1: NLP Analysis
        print("Step 1: Analyzing natural language query...")
        nlp_result = self.nlp_analyzer.analyze_query(user_query)
        extracted_attributes = nlp_result['extracted_attributes']
        key_phrases = nlp_result['key_phrases']
        
        print(f"✓ Extracted attributes: {extracted_attributes}")
        print(f"✓ Key phrases: {key_phrases}")
        
        # Step 2: Similarity Matching
        print("\nStep 2: Matching against vibe knowledge base...")
        similarity_result = self.similarity_matcher.find_best_matches(
            extracted_phrases=key_phrases,
            individual_attributes=extracted_attributes
        )
        
        rule_based_attributes = similarity_result['matched_attributes']
        has_high_confidence = similarity_result['has_high_confidence_matches']
        
        print(f"✓ Rule-based matches: {rule_based_attributes}")
        print(f"✓ High confidence matches: {has_high_confidence}")
        
        # Step 3: GPT Inference (if needed)
        gpt_attributes = {}
        if not has_high_confidence or len(rule_based_attributes) < 3:
            print("\nStep 3: Using GPT for attribute inference...")
            gpt_attributes = self.gpt_inference.infer_attributes(
                user_query=user_query,
                existing_attributes={**extracted_attributes, **rule_based_attributes},
                vibe_mappings=self.similarity_matcher.vibe_mappings
            )
            
            if gpt_attributes:
                print(f"✓ GPT inferred attributes: {gpt_attributes}")
            else:
                print("⚠ GPT inference not available or failed")
        else:
            print("\nStep 3: Skipping GPT inference (high confidence rule-based matches)")
        
        # Step 4: Merge attributes
        print("\nStep 4: Merging attributes...")
        final_attributes = self._merge_all_attributes(
            extracted_attributes,
            rule_based_attributes,
            gpt_attributes,
            user_preferences or {}
        )
        
        print(f"✓ Final attributes: {final_attributes}")
        
        # Step 5: Check for missing critical attributes
        missing_attributes = self._check_missing_attributes(final_attributes)
        if missing_attributes:
            print(f"⚠ Missing critical attributes: {missing_attributes}")
            
            # Generate user-friendly questions and use the first one as the main message
            follow_up_questions = self._generate_follow_up_questions(missing_attributes)
            user_friendly_message = follow_up_questions[0] if follow_up_questions else "I need more information to help you find the perfect clothing item."
            
            return {
                'success': False,
                'message': user_friendly_message,
                'missing_attributes': missing_attributes,
                'suggested_questions': follow_up_questions,
                'final_attributes': final_attributes,
                'processing_details': {
                    'nlp_analysis': nlp_result,
                    'similarity_matching': similarity_result
                }
            }
        
        # Step 6: Product Filtering
        print("\nStep 5: Filtering product catalog...")
        matching_products = self.catalog_filter.filter_products(
            attributes=final_attributes,
            max_results=self.config.get('max_results', 5)
        )
        
        print(f"✓ Found {len(matching_products)} matching products")
        
        # Step 7: Natural Language Generation
        print("\nStep 6: Generating natural language response...")
        suggestion = self.nlg_generator.generate_suggestion(
            products=matching_products,
            original_query=user_query,
            attributes=final_attributes
        )
        
        # Use the suggestion as-is (NLGGenerator already handles tone internally)
        final_suggestion = suggestion
        
        print("✓ Generated recommendation response")
        
        return {
            'success': True,
            'recommendation': final_suggestion,
            'products': matching_products,
            'final_attributes': final_attributes,
            'processing_details': {
                'nlp_analysis': nlp_result,
                'similarity_matching': similarity_result,
                'gpt_inference': gpt_attributes,
                'products_found': len(matching_products)
            }
        }
    
    def _merge_all_attributes(self, 
                            extracted: Dict[str, Any],
                            rule_based: Dict[str, Any],
                            gpt_inferred: Dict[str, Any],
                            user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge attributes from all sources with proper priority."""
        
        # Priority order: user_prefs > rule_based > gpt_inferred > extracted
        merged = {}
        
        # Start with extracted (lowest priority)
        for key, value in extracted.items():
            if value:
                merged[key] = value
        
        # Override with GPT inferred (handle None case)
        if gpt_inferred:
            for key, value in gpt_inferred.items():
                if value:
                    merged[key] = value
        
        # Override with rule-based (higher confidence)
        for key, value in rule_based.items():
            if value:
                merged[key] = value
        
        # Override with user preferences (highest priority)
        for key, value in user_prefs.items():
            if value:
                merged[key] = value
        
        return merged
    
    def _check_missing_attributes(self, attributes: Dict[str, Any]) -> List[str]:
        """Check for missing critical attributes."""
        critical_attributes = ['category', 'size', 'budget']  # Must have category, size, and budget
        recommended_attributes = ['occasion', 'season']  # Good to have
        
        missing = []
        
        # Check critical attributes
        for attr in critical_attributes:
            value = attributes.get(attr)
            is_missing = attr not in attributes or not value
            print(f"✓ Checking {attr}: value={repr(value)}, type={type(value)}, is_missing={is_missing}")
            if is_missing:
                missing.append(attr)
        
        # Check if we have at least some context (only if we have category, size, and budget)
        if 'category' in attributes and 'size' in attributes and 'budget' in attributes:
            context_attributes = ['occasion', 'season', 'style', 'fit']
            has_context = any(attr in attributes and attributes[attr] for attr in context_attributes)
            
            if not has_context:
                missing.extend(['occasion or style'])
        
        return missing
    
    def _generate_follow_up_questions(self, missing_attributes: List[str]) -> List[str]:
        """Generate follow-up questions for missing attributes with helpful examples."""
        questions = []
        
        # Get available options from the system
        available_categories = ["dress", "top", "pants", "skirt", "jacket", "shirt", "blouse"]
        available_occasions = ["casual", "formal", "work", "party", "date", "wedding", "brunch", "vacation"]
        available_styles = ["casual", "formal", "chic", "bohemian", "minimalist", "edgy", "romantic", "professional"]
        available_fits = ["relaxed", "tailored", "loose", "fitted", "oversized", "slim", "regular"]
        available_sizes = ["XS", "S", "M", "L", "XL", "XXL"]
        
        question_templates = {
            'category': f"What type of clothing are you looking for? Choose from: {', '.join(available_categories)}",
            'size': f"What size do you need? Available sizes: {', '.join(available_sizes)}",
            'budget': "What's your budget? You can say something like '$50', 'under $100', or '200 dollars'",
            'occasion': f"What's the occasion? For example: {', '.join(available_occasions[:6])}",
            'season': "What season is this for? (spring, summer, fall, winter)",
            'style': f"What style are you going for? Options include: {', '.join(available_styles[:6])}",
            'fit': f"How would you like it to fit? Choose from: {', '.join(available_fits[:4])}"
        }
        
        for attr in missing_attributes:
            if attr in question_templates:
                questions.append(question_templates[attr])
            elif 'or' in attr:  # Handle compound attributes like "occasion or style"
                if 'occasion' in attr:
                    questions.append(f"Tell me about the occasion or style! For example: {', '.join(available_occasions[:4])} or {', '.join(available_styles[:4])}")
                else:
                    questions.append(f"Could you tell me more about the {attr}? Give me some details!")
        
        return questions
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get status of all system components."""
        status = {
            'nlp_analyzer': 'Ready',
            'similarity_matcher': f"Loaded {len(self.similarity_matcher.all_vibe_keys)} vibe mappings",
            'gpt_inference': 'Ready' if self.gpt_inference.available else 'Not configured (missing API key)',
            'catalog_filter': f"Loaded {len(self.catalog_filter.catalog_df)} products" if not self.catalog_filter.catalog_df.empty else 'No catalog loaded',
            'nlg_generator': 'Ready'
        }
        
        return status
    
    def interactive_session(self):
        """Run an interactive recommendation session."""
        print("🌟 Welcome to the Vibe-to-Attribute Clothing Recommendation System!")
        print("Ask me for clothing recommendations using natural language.")
        print("Type 'quit' to exit, 'status' to see system status.\n")
        
        while True:
            try:
                user_input = input("👤 What are you looking for? ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Thanks for using the recommendation system! Goodbye!")
                    break
                
                if user_input.lower() == 'status':
                    status = self.get_system_status()
                    print("\n📊 System Status:")
                    for component, status_msg in status.items():
                        print(f"  • {component}: {status_msg}")
                    print()
                    continue
                
                if not user_input:
                    print("Please enter a clothing request or type 'quit' to exit.\n")
                    continue
                
                # Get recommendations
                result = self.get_recommendations(user_input)
                
                if result['success']:
                    print(f"\n🤖 {result['recommendation']}\n")
                else:
                    print(f"\n🤖 {result['message']}")
                    if 'suggested_questions' in result:
                        print("\nTo help me better, please answer:")
                        for question in result['suggested_questions']:
                            print(f"  • {question}")
                    print()
                
            except KeyboardInterrupt:
                print("\n👋 Thanks for using the recommendation system! Goodbye!")
                break
            except Exception as e:
                print(f"❌ An error occurred: {e}")
                print("Please try again with a different request.\n")

# Example usage and testing
if __name__ == "__main__":
    # Initialize system
    system = VibeRecommendationSystem()
    
    # Check system status
    print("System Status:")
    status = system.get_system_status()
    for component, status_msg in status.items():
        print(f"  • {component}: {status_msg}")
    
    # Test with sample queries
    test_queries = [
        "Something casual for a summer brunch",
        "I need a formal black dress for an evening event",
        "Comfortable workout clothes for the gym"
    ]
    
    print("\n" + "="*50)
    print("Testing with sample queries:")
    print("="*50)
    
    for query in test_queries:
        print(f"\n🧪 Testing: '{query}'")
        result = system.get_recommendations(query)
        
        if result['success']:
            print(f"✅ Success: {result['recommendation']}")
        else:
            print(f"❌ Failed: {result['message']}")
    
    # Start interactive session if run directly
    print("\n" + "="*50)
    print("Starting interactive session...")
    print("="*50)
    system.interactive_session() 