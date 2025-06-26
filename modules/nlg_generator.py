"""
Natural Language Generation Module

Converts filtered product results and chosen attributes into natural language
suggestions for the user. Creates friendly, informative responses.
"""

from typing import Dict, List, Optional, Any
import random

class NLGGenerator:
    def __init__(self):
        """Initialize the natural language generator."""
        self.templates = self._init_templates()
        self.attribute_descriptions = self._init_attribute_descriptions()
    
    def _init_templates(self) -> Dict[str, List[str]]:
        """Initialize response templates for different scenarios."""
        return {
            'single_product': [
                "Perfect! I found {description} that would be ideal for {context}. {details} It's priced at ${price}.",
                "I recommend {description}. {details} At ${price}, it's {price_context} and perfect for {context}.",
                "How about {description}? {details} It's ${price} and would work beautifully for {context}."
            ],
            'multiple_products': [
                "I found {count} great options for {context}:",
                "Here are {count} perfect matches for {context}:",
                "I have {count} wonderful suggestions for {context}:"
            ],
            'product_item': [
                "• {name} - {description} (${price})",
                "• {name}: {description} for ${price}"
            ]
        }
    
    def _init_attribute_descriptions(self) -> Dict[str, Dict[str, str]]:
        """Initialize descriptions for different attribute values."""
        return {
            'fit': {
                'relaxed': 'comfortable and loose-fitting',
                'tailored': 'structured and well-fitted',
                'bodycon': 'form-fitting and flattering'
            },
            'occasion': {
                'casual': 'everyday wear',
                'formal': 'special occasions',
                'brunch': 'daytime social gatherings'
            }
        }
    
    def generate_suggestion(self, 
                          products: List[Dict[str, Any]], 
                          original_query: str,
                          attributes: Dict[str, Any]) -> str:
        """Generate a natural language suggestion based on products and context."""
        if not products:
            return "I couldn't find any items that match your criteria exactly. Try adjusting your preferences."
        
        context = self._extract_context(original_query, attributes)
        
        if len(products) == 1:
            return self._generate_single_product_response(products[0], context, attributes)
        else:
            return self._generate_multiple_products_response(products, context, attributes)
    
    def _extract_context(self, query: str, attributes: Dict[str, Any]) -> str:
        """Extract context description from query and attributes."""
        context_parts = []
        
        if 'occasion' in attributes:
            occasion = attributes['occasion'].lower()
            if occasion in self.attribute_descriptions['occasion']:
                context_parts.append(self.attribute_descriptions['occasion'][occasion])
            else:
                context_parts.append(occasion)
        
        if not context_parts:
            key_words = [word for word in query.lower().split() 
                        if word not in ['something', 'for', 'a', 'an', 'the', 'i', 'need', 'want']]
            if key_words:
                return ' '.join(key_words[:3])
            else:
                return "your request"
        
        return ', '.join(context_parts)
    
    def _generate_single_product_response(self, product: Dict[str, Any], context: str, attributes: Dict[str, Any]) -> str:
        """Generate response for a single product recommendation."""
        description = self._create_product_description(product)
        details = self._create_product_details(product, attributes)
        price_context = self._get_price_context(product['price'], attributes.get('budget'))
        
        template = random.choice(self.templates['single_product'])
        
        return template.format(
            description=description,
            context=context,
            details=details,
            price=product['price'],
            price_context=price_context
        )
    
    def _generate_multiple_products_response(self, products: List[Dict[str, Any]], context: str, attributes: Dict[str, Any]) -> str:
        """Generate response for multiple product recommendations."""
        intro_template = random.choice(self.templates['multiple_products'])
        intro = intro_template.format(count=len(products), context=context)
        
        product_lines = []
        for product in products[:3]:
            description = self._create_brief_description(product)
            item_template = random.choice(self.templates['product_item'])
            
            product_line = item_template.format(
                name=product['name'],
                description=description,
                price=product['price']
            )
            product_lines.append(product_line)
        
        return intro + "\n\n" + "\n".join(product_lines)
    
    def _create_product_description(self, product: Dict[str, Any]) -> str:
        """Create a rich description of the product."""
        parts = []
        
        if product.get('color_or_print'):
            parts.append(product['color_or_print'].lower())
        
        if product.get('fabric'):
            parts.append(product['fabric'].lower())
        
        if product.get('category'):
            parts.append(product['category'].lower())
        
        return ' '.join(parts) if parts else product.get('name', 'item')
    
    def _create_brief_description(self, product: Dict[str, Any]) -> str:
        """Create a brief description for product lists."""
        parts = []
        
        if product.get('color'):
            parts.append(product['color'])
        
        if product.get('pattern') and product['pattern'].lower() != 'solid':
            parts.append(product['pattern'])
        
        if product.get('fit'):
            parts.append(f"{product['fit']} fit")
        
        return ', '.join(parts) if parts else "stylish option"
    
    def _create_product_details(self, product: Dict[str, Any], attributes: Dict[str, Any]) -> str:
        """Create detailed product information."""
        details = []
        
        if product.get('brand'):
            details.append(f"by {product['brand']}")
        
        return '. '.join(details) + '.' if details else "A versatile piece."
    
    def _get_price_context(self, price: float, budget: Optional[float]) -> str:
        """Get contextual description of the price."""
        if budget and price <= budget * 0.8:
            return "a great value"
        elif price < 50:
            return "affordably priced"
        else:
            return "reasonably priced"
