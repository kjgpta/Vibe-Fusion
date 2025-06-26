"""
NLP Query Analysis Module

Processes the user's natural language query to extract key fashion-related information
using spaCy for tokenization, POS tagging, and entity extraction.
"""

import spacy
import re
from typing import Dict, List, Optional, Any
import nltk
from nltk.corpus import stopwords

class NLPAnalyzer:
    def __init__(self):
        """Initialize the NLP analyzer with spaCy model and NLTK components."""
        try:
            # Load spaCy English model (download if needed)
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            print("spaCy English model not found. Please install it with: python -m spacy download en_core_web_md")
            raise
        
        # Initialize NLTK components
        try:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"NLTK setup warning: {e}")
            self.stop_words = set(['a', 'an', 'the', 'for', 'in', 'on', 'at', 'to', 'with'])
        
        # Fashion-specific entity patterns
        self.fashion_patterns = self._init_fashion_patterns()

        self._attr_map = {
            'occasion':   'occasions',
            'season':     'seasons',
            'style':      'styles',
            'category':   'categories',
            'fit':        'fits',
            'color':      'colors',
            'coverage':   'coverage',
            'size':       'sizes'
        }
    
    def _init_fashion_patterns(self) -> Dict[str, List[str]]:
        """Initialize fashion-specific patterns and keywords."""
        return {
            'occasions': [
                'brunch', 'lunch', 'dinner', 'party', 'wedding', 'office', 'work',
                'date', 'casual', 'formal', 'business', 'workout', 'gym', 'beach',
                'vacation', 'travel', 'interview', 'meeting', 'event', 'night out'
            ],
            'seasons': [
                'summer', 'winter', 'spring', 'fall', 'autumn', 'hot', 'cold',
                'warm', 'cool', 'sunny', 'rainy', 'snowy'
            ],
            'styles': [
                'casual', 'formal', 'business', 'dressy', 'elegant', 'edgy',
                'bohemian', 'boho', 'chic', 'trendy', 'classic', 'vintage',
                'modern', 'minimalist', 'romantic', 'sporty', 'preppy'
            ],
            'categories': [
                'dress','top', 'tops', 'pants', 'skirt'
            ],
            'fits': [
                'relaxed', 'stretch to fit', 'body hugging', 'tailored', 'oversized', 'flowy', 'bodycon', 'slim', 'sleek and straight'
            ],
            'colors': [
                'pastel yellow', 'deep blue', 'floral print', 'red', 'off-white', 'midnight navy sequin', 'sapphire blue', 'ruby red', 'etc.'
            ],
            'coverage': [
                'short sleeves', 'long sleeves', 'sleeveless', 'spaghetti straps', 'straps', 'short flutter sleeves', 'cap sleeves', 'quarter sleeves', 'long sleeves', 'full sleeves', 'cropped', 'bishop sleeves', 'balloon sleeves', 'bell sleeves', 'halter', 'tube', 'one-shoulder'
            ],
            'sizes': [
                'XS', 'S', 'M', 'L', 'XL', 'XXL'
            ]
        }
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize the input text."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove some common filler phrases
        filler_phrases = [
            'i want', 'i need', "i'm looking for", 'looking for',
            'can you find', 'help me find', 'show me', 'find me',
            'could you find', 'could you show me', 'do you have',
            'i would like', 'i’m interested in', 'would you please',
            'would you mind', 'give me', 'tell me about', 'what’s available',
            'what do you have for', 'any recommendations for',
            'do you know', 'please find', 'please show', 'please help me',
            'let me see', 'i’m curious about', 'i’m searching for',
            'looking to', 'seek', 'seeking', 'i’m hunting for'
        ]
        
        for phrase in filler_phrases:
            text = text.replace(phrase, '')
        
        return text.strip()
    
    def extract_key_phrases(self, text: str) -> Dict[str, Any]:
        """Extract key fashion-related phrases from the text using spaCy."""
        doc = self.nlp(text)
        
        extracted = {
            'occasion': None,
            'season': None,
            'style': None,
            'category': None,
            'fit': None,
            'color': None,
            'coverage': None,
            'size': None,
            'raw_phrases': [],
            'noun_chunks': [],
            'adjectives': []
        }
        
        # Extract noun chunks (potentially meaningful phrases)
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower()
            extracted['noun_chunks'].append(chunk_text)
            
            # Check for compound phrases (season + occasion)
            if any(season in chunk_text for season in self.fashion_patterns['seasons']) and \
               any(occasion in chunk_text for occasion in self.fashion_patterns['occasions']):
                extracted['raw_phrases'].append(chunk_text)
        
        # Extract adjectives (style descriptors)
        for token in doc:
            if token.pos_ == 'ADJ' and token.text.lower() not in self.stop_words:
                extracted['adjectives'].append(token.text.lower())
        
        # Match against fashion patterns
        # Don't filter out fashion-related words even if they're stop words
        all_fashion_words = set()
        for pattern_list in self.fashion_patterns.values():
            all_fashion_words.update(pattern_list)
        
        tokens = [token.text.lower() for token in doc if not token.is_punct and 
                 (not token.is_stop or token.text.lower() in all_fashion_words)]
        
        for token in tokens:
            # Check occasions
            if token in self.fashion_patterns['occasions'] and not extracted['occasion']:
                extracted['occasion'] = token
            
            # Check seasons
            if token in self.fashion_patterns['seasons'] and not extracted['season']:
                extracted['season'] = token
            
            # Check styles
            if token in self.fashion_patterns['styles'] and not extracted['style']:
                extracted['style'] = token
            
            # Check categories
            if token in self.fashion_patterns['categories'] and not extracted['category']:
                extracted['category'] = token
            
            # Check fits
            if token in self.fashion_patterns['fits'] and not extracted['fit']:
                extracted['fit'] = token
            
            # Check colors
            if token in self.fashion_patterns['colors'] and not extracted['color']:
                extracted['color'] = token
            
            # Check coverage
            if token in self.fashion_patterns['coverage'] and not extracted['coverage']:
                extracted['coverage'] = token
            
            # Check sizes
            if token in self.fashion_patterns['sizes'] and not extracted['size']:
                # Normalize size to standard format (XS, S, M, L, XL, XXL)
                size_mapping = {
                    'xs': 'XS', 'extra small': 'XS', 'size xs': 'XS',
                    's': 'S', 'small': 'S', 'size s': 'S',
                    'm': 'M', 'medium': 'M', 'size m': 'M',
                    'l': 'L', 'large': 'L', 'size l': 'L',
                    'xl': 'XL', 'extra large': 'XL', 'size xl': 'XL',
                    'xxl': 'XXL', 'extra extra large': 'XXL', '2xl': 'XXL', 'size xxl': 'XXL'
                }
                extracted['size'] = size_mapping.get(token, token.upper())
        
        # Look for compound phrases
        text_lower = text.lower()
        for chunk in extracted['noun_chunks']:
            if len(chunk.split()) > 1:  # Multi-word phrases
                extracted['raw_phrases'].append(chunk)
        
        # Special handling for compound season-occasion phrases
        season_occasion_patterns = [
            'summer brunch', 'winter formal', 'spring wedding', 'fall party',
            'summer party', 'winter date', 'spring casual', 'fall formal'
        ]
        
        for pattern in season_occasion_patterns:
            if pattern in text_lower:
                extracted['raw_phrases'].append(pattern)
                words = pattern.split()
                if words[0] in self.fashion_patterns['seasons']:
                    extracted['season'] = words[0]
                if words[1] in self.fashion_patterns['occasions']:
                    extracted['occasion'] = words[1]
        
        return extracted
    
    def analyze_query(self, user_query: str) -> Dict[str, Any]:
        """
        Main method to analyze user query and extract fashion attributes.
        
        Args:
            user_query: The user's natural language request
            
        Returns:
            Dictionary containing extracted fashion attributes
        """
        # Clean the input text
        cleaned_text = self.clean_text(user_query)
        
        # Extract key phrases and attributes
        extracted = self.extract_key_phrases(cleaned_text)
        
        # Extract budget information using regex
        budget = self._extract_budget(user_query)
        
        # Create structured output
        analysis_result = {
            'original_query': user_query,
            'cleaned_query': cleaned_text,
            'extracted_attributes': {
                'occasion': extracted['occasion'],
                'season': extracted['season'], 
                'style': extracted['style'],
                'category': extracted['category'],
                'fit': extracted['fit'],
                'color': extracted['color'],
                'coverage': extracted['coverage'],
                'size': extracted['size'],
                'budget': budget
            },
            'key_phrases': extracted['raw_phrases'],
            'noun_chunks': extracted['noun_chunks'],
            'adjectives': extracted['adjectives'],
            'confidence_scores': self._calculate_confidence(extracted)
        }
        
        return analysis_result
    
    def _calculate_confidence(self, extracted: Dict[str, Any]) -> Dict[str, float]:
        """Calculate confidence scores for extracted attributes."""
        confidences: Dict[str, float] = {}
        for attr, pattern_key in self._attr_map.items():
            value = extracted.get(attr)
            if not value:
                confidences[attr] = 0.0
                continue

            # Embed the extracted value
            value_doc = self.nlp(value)
            if not value_doc.vector_norm:
                # OOV or no vector — fall back to zero
                confidences[attr] = 0.0
                continue

            # Compare against each candidate pattern
            best_sim = 0.0
            for pat in self.fashion_patterns[pattern_key]:
                pat_doc = self.nlp(pat)
                if not pat_doc.vector_norm:
                    continue
                sim = value_doc.similarity(pat_doc)  # cosine under the hood
                if sim > best_sim:
                    best_sim = sim

            # Clamp to [0,1]
            confidences[attr] = max(0.0, min(1.0, best_sim))

        return confidences
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget information from text using regex patterns."""
        import re
        
        # Common budget patterns
        budget_patterns = [
            r'\$(\d+(?:\.\d{2})?)',  # $100, $99.99
            r'(\d+(?:\.\d{2})?)\s*dollars?',  # 100 dollars, 100.50 dollar
            r'under\s*\$?(\d+(?:\.\d{2})?)',  # under $100, under 100
            r'below\s*\$?(\d+(?:\.\d{2})?)',  # below $100, below 100
            r'less\s*than\s*\$?(\d+(?:\.\d{2})?)',  # less than $100, less than 100
            r'budget\s*of\s*\$?(\d+(?:\.\d{2})?)',  # budget of $100, budget of 100
            r'(\d+(?:\.\d{2})?)\s*dollar\s*budget',  # 100 dollar budget
            r'around\s*\$?(\d+(?:\.\d{2})?)',  # around $100, around 100
            r'up\s*to\s*\$?(\d+(?:\.\d{2})?)',  # up to $100, up to 100
            r'max\s*\$?(\d+(?:\.\d{2})?)',  # max $100, max 100
        ]
        
        text_lower = text.lower()
        
        for pattern in budget_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None

# Example usage and testing
if __name__ == "__main__":
    analyzer = NLPAnalyzer()
    
    # Test queries
    test_queries = [
        "Something casual for a summer brunch",
        "I need a formal dress for a winter wedding",
        "Looking for comfortable workout clothes",
        "Show me elegant black evening wear",
        "Casual jeans and a nice top for the office"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = analyzer.analyze_query(query)
        print(f"Extracted: {result['extracted_attributes']}")
        print(f"Key phrases: {result['key_phrases']}") 