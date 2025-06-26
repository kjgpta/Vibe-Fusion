"""
Cosine Similarity Matching & Rule-Based Mapping Module

Matches extracted keywords/phrases against curated "vibe-to-attribute" JSON knowledge base
using cosine similarity for semantic matching.
"""

import json
import os
import spacy
from typing import Dict, List, Tuple, Optional, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SimilarityMatcher:
    def __init__(self, vibes_data_dir: str = "data/vibes/", similarity_threshold: float = 0.8):
        """
        Initialize the similarity matcher with JSON knowledge base.
        
        Args:
            vibes_data_dir: Directory containing vibe-to-attribute JSON files
            similarity_threshold: Minimum similarity score to accept a match
        """
        self.vibes_data_dir = vibes_data_dir
        self.similarity_threshold = similarity_threshold
        
        # Load spaCy model for semantic similarity
        try:
            self.nlp = spacy.load("en_core_web_md")
        except OSError:
            print("Warning: spaCy model not available for similarity matching")
            self.nlp = None
        
        # Load all vibe mapping JSONs
        self.vibe_mappings = self._load_vibe_mappings()
        
        # Initialize TF-IDF vectorizer for backup similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            ngram_range=(1, 3)  # Include unigrams, bigrams, and trigrams
        )
        
        # Prepare all vibe keys for vectorization
        self._prepare_vibe_vectors()
    
    def _load_vibe_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load all vibe-to-attribute mapping JSON files."""
        mappings = {}
        
        if not os.path.exists(self.vibes_data_dir):
            print(f"Warning: Vibes data directory {self.vibes_data_dir} not found")
            return mappings
        
        json_files = [f for f in os.listdir(self.vibes_data_dir) if f.endswith('.json')]
        
        for json_file in json_files:
            file_path = os.path.join(self.vibes_data_dir, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    mapping_data = json.load(f)
                    mapping_name = json_file.replace('.json', '')
                    mappings[mapping_name] = mapping_data
                    print(f"Loaded {len(mapping_data)} mappings from {json_file}")
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return mappings
    
    def _prepare_vibe_vectors(self):
        """Prepare TF-IDF vectors for all vibe keys."""
        self.all_vibe_keys = []
        self.key_to_mapping = {}  # Maps vibe key to (mapping_type, attributes)
        
        for mapping_type, mapping_data in self.vibe_mappings.items():
            for vibe_key, attributes in mapping_data.items():
                self.all_vibe_keys.append(vibe_key)
                self.key_to_mapping[vibe_key] = (mapping_type, attributes)
        
        if self.all_vibe_keys:
            # Fit TF-IDF vectorizer on all vibe keys
            try:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.all_vibe_keys)
            except Exception as e:
                print(f"Warning: TF-IDF vectorization failed: {e}")
                self.tfidf_matrix = None
        else:
            print("Warning: No vibe keys found for vectorization")
            self.tfidf_matrix = None
    
    def calculate_spacy_similarity(self, phrase1: str, phrase2: str) -> float:
        """Calculate semantic similarity using spaCy word vectors."""
        if not self.nlp:
            return 0.0
        
        try:
            doc1 = self.nlp(phrase1)
            doc2 = self.nlp(phrase2)
            
            # Use spaCy's built-in similarity (cosine similarity of averaged word vectors)
            similarity = doc1.similarity(doc2)
            return float(similarity)
        except Exception as e:
            print(f"Warning: spaCy similarity calculation failed: {e}")
            return 0.0
    
    def calculate_tfidf_similarity(self, query_phrase: str) -> List[Tuple[str, float]]:
        """Calculate TF-IDF cosine similarity with all vibe keys."""
        if self.tfidf_matrix is None or self.tfidf_matrix.shape[0] == 0:
            return []
        
        try:
            # Transform query phrase
            query_vector = self.tfidf_vectorizer.transform([query_phrase])
            
            # Calculate cosine similarity with all vibe keys
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # Create list of (vibe_key, similarity_score) tuples
            similarity_pairs = list(zip(self.all_vibe_keys, similarities))
            
            # Sort by similarity score (descending)
            similarity_pairs.sort(key=lambda x: x[1], reverse=True)
            
            return similarity_pairs
        except Exception as e:
            print(f"Warning: TF-IDF similarity calculation failed: {e}")
            return []
    
    def find_best_matches(self, extracted_phrases: List[str], 
                         individual_attributes: Dict[str, str]) -> Dict[str, Any]:
        """
        Find best matching vibes for extracted phrases and individual attributes.
        
        Args:
            extracted_phrases: List of key phrases from NLP analysis
            individual_attributes: Individual attributes extracted (occasion, style, etc.)
            
        Returns:
            Dictionary containing matched attributes and confidence scores
        """
        matched_attributes = {}
        match_details = {
            'rule_based_matches': [],
            'similarity_scores': {},
            'confidence_scores': {},
            'method_used': {}
        }
        
        # Combine phrases and individual attributes for matching
        all_candidates = extracted_phrases.copy()
        
        # Add individual attributes that were extracted (only strings)
        for attr_type, attr_value in individual_attributes.items():
            if attr_value and isinstance(attr_value, str):
                all_candidates.append(attr_value)
        
        # Try to match each candidate phrase/attribute
        for candidate in all_candidates:
            if not candidate or len(candidate.strip()) < 2:
                continue
                
            best_match = self._find_best_match_for_phrase(candidate)
            
            if best_match:
                vibe_key, similarity_score, mapping_type, attributes = best_match
                
                # Record match details
                match_details['rule_based_matches'].append({
                    'input_phrase': candidate,
                    'matched_vibe': vibe_key,
                    'similarity_score': similarity_score,
                    'mapping_type': mapping_type,
                    'attributes': attributes
                })
                
                # Merge attributes if similarity is above threshold
                if similarity_score >= self.similarity_threshold:
                    for attr_key, attr_value in attributes.items():
                        if attr_key not in matched_attributes:
                            matched_attributes[attr_key] = attr_value
                            match_details['confidence_scores'][attr_key] = similarity_score
                            match_details['method_used'][attr_key] = 'rule_based_similarity'
                        elif match_details['confidence_scores'].get(attr_key, 0) < similarity_score:
                            # Keep the match with higher confidence
                            matched_attributes[attr_key] = attr_value
                            match_details['confidence_scores'][attr_key] = similarity_score
        
        return {
            'matched_attributes': matched_attributes,
            'match_details': match_details,
            'has_high_confidence_matches': any(
                score >= self.similarity_threshold 
                for score in match_details['confidence_scores'].values()
            )
        }
    
    def _find_best_match_for_phrase(self, phrase: str) -> Optional[Tuple[str, float, str, Dict]]:
        """
        Find the best matching vibe for a single phrase.
        
        Returns:
            Tuple of (vibe_key, similarity_score, mapping_type, attributes) or None
        """
        best_match = None
        best_score = 0.0
        
        # Method 1: Try exact or near-exact matches first
        phrase_lower = phrase.lower().strip()
        for vibe_key in self.all_vibe_keys:
            if phrase_lower == vibe_key.lower():
                mapping_type, attributes = self.key_to_mapping[vibe_key]
                return (vibe_key, 1.0, mapping_type, attributes)
        
        # Method 2: Use spaCy similarity if available
        if self.nlp:
            for vibe_key in self.all_vibe_keys:
                similarity = self.calculate_spacy_similarity(phrase, vibe_key)
                if similarity > best_score:
                    best_score = similarity
                    mapping_type, attributes = self.key_to_mapping[vibe_key]
                    best_match = (vibe_key, similarity, mapping_type, attributes)
        
        # Method 3: Use TF-IDF similarity as backup
        if best_score < 0.5:  # Only use TF-IDF if spaCy didn't find good matches
            tfidf_matches = self.calculate_tfidf_similarity(phrase)
            if tfidf_matches:
                top_vibe_key, top_score = tfidf_matches[0]
                if top_score > best_score:
                    mapping_type, attributes = self.key_to_mapping[top_vibe_key]
                    best_match = (top_vibe_key, top_score, mapping_type, attributes)
        
        return best_match
    
    def merge_attributes(self, *attribute_dicts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple attribute dictionaries, handling conflicts intelligently.
        
        Args:
            *attribute_dicts: Variable number of attribute dictionaries to merge
            
        Returns:
            Merged dictionary with conflict resolution
        """
        merged = {}
        
        for attr_dict in attribute_dicts:
            if not attr_dict:
                continue
                
            for key, value in attr_dict.items():
                if key not in merged:
                    merged[key] = value
                elif merged[key] != value:
                    # Handle conflicts - could be improved with domain knowledge
                    if isinstance(value, list) and isinstance(merged[key], list):
                        # Merge lists and remove duplicates
                        merged[key] = list(set(merged[key] + value))
                    elif isinstance(value, str) and isinstance(merged[key], str):
                        # For strings, keep the more specific one (longer usually means more specific)
                        if len(value) > len(merged[key]):
                            merged[key] = value
        
        return merged
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get a summary of loaded mappings for debugging."""
        summary = {
            'total_mappings': len(self.vibe_mappings),
            'total_vibe_keys': len(self.all_vibe_keys),
            'mapping_types': list(self.vibe_mappings.keys()),
            'sample_vibes': {}
        }
        
        for mapping_type, mapping_data in self.vibe_mappings.items():
            sample_keys = list(mapping_data.keys())[:3]  # First 3 keys as samples
            summary['sample_vibes'][mapping_type] = sample_keys
        
        return summary

# Example usage and testing
if __name__ == "__main__":
    # Initialize similarity matcher
    matcher = SimilarityMatcher()
    
    # Print mapping summary
    summary = matcher.get_mapping_summary()
    print("Mapping Summary:")
    print(json.dumps(summary, indent=2))
    
    # Test similarity matching
    test_phrases = [
        "summer brunch",
        "casual wear", 
        "comfortable fit",
        "pastel colors",
        "formal occasion"
    ]
    
    test_attributes = {
        'occasion': 'brunch',
        'style': 'casual',
        'fit': 'comfortable'
    }
    
    print("\nTesting similarity matching:")
    result = matcher.find_best_matches(test_phrases, test_attributes)
    
    print(f"Matched attributes: {result['matched_attributes']}")
    print(f"High confidence matches: {result['has_high_confidence_matches']}")
    print(f"Match details: {len(result['match_details']['rule_based_matches'])} matches found") 