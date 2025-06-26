"""
GPT-based Attribute Inference Module

Uses OpenAI's GPT models to infer fashion attributes from natural language queries
when rule-based matching doesn't provide sufficient confidence.
"""

import openai
import json
import os
from typing import Dict, List, Optional, Any
import dotenv

dotenv.load_dotenv()

class GPTInference:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize GPT inference with API configuration.
        
        Args:
            api_key: OpenAI API key (optional, will try to get from environment)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if self.api_key:
            openai.api_key = self.api_key
            self.available = True
            print("GPT inference initialized successfully")
        else:
            self.available = False
            print("GPT inference not available - no API key provided")
        
        # Define category-specific valid attributes
        self.category_attributes = {
            'top': ['fit', 'fabric', 'sleeve_length', 'color_or_print'],
            'dress': ['fit', 'fabric', 'sleeve_length', 'color_or_print', 'occasion', 'neckline'],
            'skirt': ['fabric', 'color_or_print', 'length'],
            'pants': ['fit', 'fabric', 'color_or_print', 'pant_type']
        }
        
        # Define valid values for each attribute based on actual data
        self.valid_values = {
            'category': ['top', 'dress', 'skirt', 'pants'],
            'fit': ['Relaxed', 'Stretch to fit', 'Body hugging', 'Tailored', 'Oversized', 'Flowy', 'Bodycon', 'Slim', 'Sleek and straight'],
            'fabric': ['Linen', 'Silk', 'Cotton', 'Rayon', 'Satin', 'Modal jersey', 'Crepe', 'Tencel', 'Chambray', 'Velvet', 'Chiffon', 'Denim', 'Wool-blend', 'Sequined velvet', 'Tulle', 'Organic cotton', 'Viscose', 'Cotton poplin', 'Linen blend', 'Cotton gauze', 'Ribbed jersey', 'Lace overlay', 'Tencel twill'],
            'sleeve_length': ['Sleeveless', 'Spaghetti straps', 'Straps', 'Short sleeves', 'Short flutter sleeves', 'Cap sleeves', 'Quarter sleeves', 'Long sleeves', 'Full sleeves', 'Cropped', 'Bishop sleeves', 'Balloon sleeves', 'Bell sleeves', 'Halter', 'Tube', 'One-shoulder'],
            'neckline': ['V neck', 'Sweetheart', 'Square neck', 'Boat neck', 'Tubetop', 'Halter', 'Cowl neck', 'Collar', 'One-shoulder', 'Polo collar', 'Illusion bateau', 'Round neck'],
            'length': ['Mini', 'Short', 'Midi', 'Maxi'],
            'pant_type': ['Wide-legged', 'Ankle length', 'Flared', 'Wide hem', 'Straight ankle', 'Mid-rise', 'Low-rise'],
            'occasion': ['Party', 'Vacation', 'Everyday', 'Evening', 'Work', 'Vocation']
        }
    
    def infer_attributes(self, 
                        user_query: str, 
                        existing_attributes: Dict[str, Any] = None,
                        vibe_mappings: Dict[str, List[Dict]] = None) -> Optional[Dict[str, Any]]:
        """
        Use GPT to infer missing fashion attributes from user query.
        
        Args:
            user_query: Natural language fashion request
            existing_attributes: Already inferred attributes from rule-based matching
            vibe_mappings: Available vibe-to-attribute mappings for context
            
        Returns:
            Dictionary of inferred attributes or None if GPT unavailable
        """
        if not self.available:
            return None
        
        existing_attributes = existing_attributes or {}
        
        try:
            # Create system prompt with context
            system_prompt = self._create_system_prompt(vibe_mappings)
            
            # Create user prompt
            user_prompt = self._create_user_prompt(user_query, existing_attributes)
            
            # Call GPT
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            try:
                if result_text.startswith('```json'):
                    result_text = result_text.replace('```json', '').replace('```', '').strip()
                elif result_text.startswith('```'):
                    result_text = result_text.replace('```', '').strip()
                
                attributes = json.loads(result_text)
                
                # Validate and clean attributes
                validated_attributes = self._validate_attributes(attributes)
                
                print(f"GPT inferred attributes: {validated_attributes}")
                return validated_attributes
                
            except json.JSONDecodeError:
                print(f"GPT response not valid JSON: {result_text}")
                return None
                
        except Exception as e:
            print(f"GPT inference error: {e}")
            return None
    
    def _create_system_prompt(self, vibe_mappings: Optional[Dict] = None) -> str:
        """Create system prompt with context about fashion attributes."""
        
        prompt = """You are a fashion stylist AI that converts natural language requests into structured fashion attributes.

IMPORTANT RULES:
1. Only return valid JSON with no additional text
2. Only use attributes that are valid for the specified category
3. Use EXACT values from the provided lists
4. If unsure about a value, omit that attribute rather than guessing

CATEGORIES AND THEIR VALID ATTRIBUTES:
- top: fit, fabric, sleeve_length, color_or_print
- dress: fit, fabric, sleeve_length, color_or_print, occasion, neckline  
- skirt: fabric, color_or_print, length
- pants: fit, fabric, color_or_print, pant_type

VALID VALUES FOR ATTRIBUTES:

Fit: Relaxed, Stretch to fit, Body hugging, Tailored, Oversized, Flowy, Bodycon, Slim, Sleek and straight

Fabric: Linen, Silk, Cotton, Rayon, Satin, Modal jersey, Crepe, Tencel, Chambray, Velvet, Chiffon, Denim, Wool-blend, Sequined velvet, Tulle, Organic cotton, Viscose, Cotton poplin, Linen blend, Cotton gauze, Ribbed jersey, Lace overlay, Tencel twill

Sleeve Length: Sleeveless, Spaghetti straps, Straps, Short sleeves, Short flutter sleeves, Cap sleeves, Quarter sleeves, Long sleeves, Full sleeves, Cropped, Bishop sleeves, Balloon sleeves, Bell sleeves, Halter, Tube, One-shoulder

Neckline: V neck, Sweetheart, Square neck, Boat neck, Tubetop, Halter, Cowl neck, Collar, One-shoulder, Polo collar, Illusion bateau, Round neck

Length: Mini, Short, Midi, Maxi

Pant Type: Wide-legged, Ankle length, Flared, Wide hem, Straight ankle, Mid-rise, Low-rise

Occasion: Party, Vacation, Everyday, Evening, Work, Vocation

Color/Print examples: Pastel yellow, Deep blue, Floral print, Red, Off-white, Midnight navy sequin, Sapphire blue, Ruby red, etc.

EXAMPLE RESPONSES:
For "casual summer top": {"category": "top", "fit": "Relaxed", "fabric": "Linen", "sleeve_length": "Short sleeves"}
For "elegant evening dress": {"category": "dress", "fit": "Body hugging", "fabric": "Silk", "occasion": "Evening", "neckline": "V neck"}
For "comfortable wide leg pants": {"category": "pants", "fit": "Relaxed", "pant_type": "Wide-legged"}
"""
        
        if vibe_mappings:
            prompt += f"\n\nAVAILABLE VIBE MAPPINGS FOR CONTEXT:\n{json.dumps(vibe_mappings, indent=2)}"
        
        return prompt
    
    def _create_user_prompt(self, user_query: str, existing_attributes: Dict[str, Any]) -> str:
        """Create user prompt with query and existing attributes."""
        
        prompt = f"Convert this fashion request to structured attributes: '{user_query}'\n\n"
        
        if existing_attributes:
            prompt += f"Already identified attributes: {json.dumps(existing_attributes)}\n"
            prompt += "Please fill in any missing attributes or improve existing ones.\n\n"
        
        prompt += "Return ONLY valid JSON with the inferred attributes:"
        
        return prompt
    
    def _validate_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Validate attributes against known valid values and category constraints."""
        validated = {}
        
        # Get category to determine valid attributes
        category = attributes.get('category', '').lower()
        valid_attrs = self.category_attributes.get(category, [])
        
        for attr, value in attributes.items():
            attr_lower = attr.lower()
            
            # Skip if not valid for this category (unless it's category itself)
            if attr_lower != 'category' and attr_lower not in valid_attrs:
                continue
            
            # Validate against known values
            if attr_lower in self.valid_values:
                if isinstance(value, list):
                    # For list values, validate each item
                    validated_list = []
                    for item in value:
                        if item in self.valid_values[attr_lower]:
                            validated_list.append(item)
                    if validated_list:
                        validated[attr] = validated_list
                else:
                    # For single values
                    if value in self.valid_values[attr_lower]:
                        validated[attr] = value
            else:
                # For attributes not in valid_values (like color_or_print), keep as-is
                validated[attr] = value
        
        return validated
    
    def get_available_attributes(self, category: str) -> List[str]:
        """Get list of valid attributes for a specific category."""
        return self.category_attributes.get(category.lower(), [])
    
    def is_available(self) -> bool:
        """Check if GPT inference is available."""
        return self.available 