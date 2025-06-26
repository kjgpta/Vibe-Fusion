"""
Product Catalog Filtering Module
"""

import pandas as pd
import os
from typing import Dict, List, Optional, Any

class CatalogFilter:
    def __init__(self, catalog_file: str = "data/Apparels_shared.xlsx"):
        self.catalog_file = catalog_file
        self.catalog_df = None
        
        # Define category-specific valid attributes
        self.category_attributes = {
            'top': ['fit', 'fabric', 'sleeve_length', 'color_or_print'],
            'dress': ['fit', 'fabric', 'sleeve_length', 'color_or_print', 'occasion', 'neckline'],
            'skirt': ['fabric', 'color_or_print', 'length'],
            'pants': ['fit', 'fabric', 'color_or_print', 'pant_type']
        }
        
        self.load_catalog()
    
    def load_catalog(self):
        """Load the product catalog from file."""
        if not os.path.exists(self.catalog_file):
            print(f"Warning: Catalog file {self.catalog_file} not found")
            self.catalog_df = pd.DataFrame()
            return
        
        try:
            if self.catalog_file.endswith('.xlsx'):
                self.catalog_df = pd.read_excel(self.catalog_file)
            elif self.catalog_file.endswith('.csv'):
                self.catalog_df = pd.read_csv(self.catalog_file)
            
            print(f"Loaded catalog with {len(self.catalog_df)} products")
            self._standardize_columns()
            
        except Exception as e:
            print(f"Error loading catalog: {e}")
            self.catalog_df = pd.DataFrame()
    
    def _standardize_columns(self):
        """Standardize column names and handle data types."""
        if self.catalog_df.empty:
            return
        
        # First, normalize column names to lowercase and replace spaces with underscores
        column_mapping = {}
        for col in self.catalog_df.columns:
            new_col = col.lower().replace(' ', '_').replace('/', '_')
            column_mapping[col] = new_col
        
        self.catalog_df = self.catalog_df.rename(columns=column_mapping)
        
        # Clean up category column (remove leading space from ' pants')
        if 'category' in self.catalog_df.columns:
            self.catalog_df['category'] = self.catalog_df['category'].str.strip()
        
        # Convert price to numeric
        if 'price' in self.catalog_df.columns:
            self.catalog_df['price'] = pd.to_numeric(self.catalog_df['price'], errors='coerce')
        
        print(f"Catalog columns: {self.catalog_df.columns.tolist()}")
    
    def filter_products(self, attributes: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
        """Filter products based on provided attributes."""
        if self.catalog_df.empty:
            return []
        
        filtered_df = self.catalog_df.copy()
        
        # Apply filters based on attributes
        if 'category' in attributes and attributes['category']:
            category = attributes['category'].lower()
            filtered_df = filtered_df[filtered_df['category'].str.lower().eq(category)]
        
        if 'budget' in attributes and attributes['budget']:
            try:
                budget = float(attributes['budget'])
                filtered_df = filtered_df[filtered_df['price'] <= budget]
            except (ValueError, TypeError):
                pass
        
        if 'size' in attributes and attributes['size']:
            size = str(attributes['size'])
            size_mask = filtered_df['available_sizes'].str.contains(size, case=False, na=False)
            filtered_df = filtered_df[size_mask]
        
        # Apply category-specific filters
        current_category = attributes.get('category', '').lower()
        
        # Fit filter (for categories that have it)
        if 'fit' in attributes and attributes['fit'] and current_category in ['top', 'dress', 'pants'] and 'fit' in filtered_df.columns:
            fit = attributes['fit'].lower()
            filtered_df = filtered_df[filtered_df['fit'].str.lower().eq(fit)]
        
        # Fabric filter (only if fabric column exists in catalog)
        if 'fabric' in attributes and attributes['fabric'] and 'fabric' in filtered_df.columns:
            fabric = attributes['fabric']
            if isinstance(fabric, list):
                # Handle list of fabrics
                fabric_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                for f in fabric:
                    fabric_mask = fabric_mask | filtered_df['fabric'].str.lower().str.contains(f.lower(), na=False)
                filtered_df = filtered_df[fabric_mask]
            else:
                fabric_mask = filtered_df['fabric'].str.lower().str.contains(fabric.lower(), na=False)
                filtered_df = filtered_df[fabric_mask]
        
        # Color or print filter
        if 'color_or_print' in attributes and attributes['color_or_print']:
            color_print = attributes['color_or_print']
            if isinstance(color_print, list):
                # Handle list of colors/prints
                color_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
                for cp in color_print:
                    color_mask = color_mask | filtered_df['color'].str.lower().str.contains(cp.lower(), na=False)
                filtered_df = filtered_df[color_mask]
            else:
                color_mask = filtered_df['color'].str.lower().str.contains(color_print.lower(), na=False)
                filtered_df = filtered_df[color_mask]
        
        # Sleeve length filter (for tops and dresses)
        if 'sleeve_length' in attributes and attributes['sleeve_length'] and current_category in ['top', 'dress'] and 'sleeve_length' in filtered_df.columns:
            sleeve = attributes['sleeve_length'].lower()
            sleeve_mask = filtered_df['sleeve_length'].str.lower().str.contains(sleeve, na=False)
            filtered_df = filtered_df[sleeve_mask]
        
        # Neckline filter (for dresses)
        if 'neckline' in attributes and attributes['neckline'] and current_category == 'dress' and 'neckline' in filtered_df.columns:
            neckline = attributes['neckline'].lower()
            neckline_mask = filtered_df['neckline'].str.lower().str.contains(neckline, na=False)
            filtered_df = filtered_df[neckline_mask]
        
        # Length filter (for skirts)
        if 'length' in attributes and attributes['length'] and current_category == 'skirt' and 'length' in filtered_df.columns:
            length = attributes['length']
            if isinstance(length, list):
                length_mask = filtered_df['length'].isin(length)
            else:
                length_mask = filtered_df['length'].str.lower().eq(length.lower())
            filtered_df = filtered_df[length_mask]
        
        # Pant type filter (for pants)
        if 'pant_type' in attributes and attributes['pant_type'] and current_category == 'pants' and 'pant_type' in filtered_df.columns:
            pant_type = attributes['pant_type'].lower()
            pant_type_mask = filtered_df['pant_type'].str.lower().str.contains(pant_type, na=False)
            filtered_df = filtered_df[pant_type_mask]
        
        # Occasion filter (for dresses)
        if 'occasion' in attributes and attributes['occasion'] and current_category == 'dress' and 'occasion' in filtered_df.columns:
            occasion = attributes['occasion'].lower()
            occasion_mask = filtered_df['occasion'].str.lower().str.contains(occasion, na=False)
            filtered_df = filtered_df[occasion_mask]
        
        # Sort and limit results
        if 'price' in filtered_df.columns:
            filtered_df = filtered_df.sort_values('price')
        
        filtered_df = filtered_df.head(max_results)
        
        # Convert to list of dictionaries
        results = []
        for _, row in filtered_df.iterrows():
            product = {
                'product_id': row.get('product_id', ''),
                'name': row.get('name', ''),
                'category': row.get('category', ''),
                'price': row.get('price', 0),
                'available_sizes': row.get('available_sizes', ''),
                'fit': row.get('fit', ''),
                'fabric': row.get('fabric', ''),
                'sleeve_length': row.get('sleeve_length', ''),
                'color_or_print': row.get('color', ''),  # Column is 'color' not 'color_or_print'
                'occasion': row.get('occasion', ''),
                'neckline': row.get('neckline', ''),
                'length': row.get('length', ''),
                'pant_type': row.get('pant_type', ''),
                'description': f"{row.get('fabric', '')} {row.get('category', '')} in {row.get('color', '')}"
            }
            results.append(product)
        
        return results
    
    def get_catalog_summary(self) -> Dict[str, Any]:
        """Get summary statistics of the catalog."""
        if self.catalog_df.empty:
            return {"error": "Catalog not loaded"}
        
        return {
            "total_products": len(self.catalog_df),
            "categories": self.catalog_df['category'].value_counts().to_dict() if 'category' in self.catalog_df.columns else {},
            "price_range": {
                "min": float(self.catalog_df['price'].min()),
                "max": float(self.catalog_df['price'].max()),
                "average": float(self.catalog_df['price'].mean())
            } if 'price' in self.catalog_df.columns else {},
            "available_fits": list(self.catalog_df['fit'].dropna().unique()) if 'fit' in self.catalog_df.columns else [],
            "available_fabrics": list(self.catalog_df['fabric'].dropna().unique()) if 'fabric' in self.catalog_df.columns else [],
            "category_attributes": self.category_attributes
        }
    
    def get_valid_attributes_for_category(self, category: str) -> List[str]:
        """Get list of valid attributes for a specific category."""
        return self.category_attributes.get(category.lower(), [])
