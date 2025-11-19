"""
Explainability module for LLM decisions using LIME.

Provides explanations for LLM outputs to meet regulatory compliance requirements.
"""

import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from lime.lime_text import LimeTextExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    logger.warning("LIME not available. Install with: pip install lime")


class LLMExplainer:
    """Provides explanations for LLM decisions."""
    
    def __init__(self, llm_processor, use_lime: bool = True):
        """
        Initialize explainer.
        
        Args:
            llm_processor: LLMProcessor instance for making predictions
            use_lime: Whether to use LIME (requires lime package)
        """
        self.llm_processor = llm_processor
        self.use_lime = use_lime and LIME_AVAILABLE
        
        if self.use_lime:
            self.explainer = LimeTextExplainer(class_names=['negative', 'positive'])
        else:
            logger.warning("LIME not available, using simple explanation method")
    
    def explain(self, input_text: str, max_features: int = 10) -> Dict:
        """
        Generate explanation for LLM output.
        
        Args:
            input_text: Input text to explain
            max_features: Maximum number of features to include in explanation
            
        Returns:
            Dictionary with explanation data
        """
        if not self.use_lime:
            return self._simple_explanation(input_text)
        
        try:
            # Get prediction
            prediction = self.llm_processor.process_document(input_text, max_tokens=50)
            
            if not prediction:
                return {"error": "Failed to get prediction"}
            
            # Extract output text
            output_text = ""
            if isinstance(prediction, dict):
                choices = prediction.get('choices', [])
                if choices:
                    output_text = choices[0].get('text', '')
            
            # Create prediction function for LIME
            def predict_proba(texts):
                """Predict probability distribution for LIME."""
                import numpy as np
                results = []
                for text in texts:
                    try:
                        response = self.llm_processor.process_document(text, max_tokens=50)
                        if response and isinstance(response, dict):
                            choices = response.get('choices', [])
                            if choices:
                                # Simple confidence: length of response as proxy
                                response_text = choices[0].get('text', '')
                                # Normalize to 0-1 range (simple heuristic)
                                confidence = min(len(response_text) / 100.0, 1.0)
                                results.append([1 - confidence, confidence])
                            else:
                                results.append([0.5, 0.5])
                        else:
                            results.append([0.5, 0.5])
                    except Exception as e:
                        logger.warning(f"Error in LIME prediction: {e}")
                        results.append([0.5, 0.5])
                
                return np.array(results)
            
            # Generate explanation
            explanation = self.explainer.explain_instance(
                input_text,
                predict_proba,
                num_features=max_features,
                num_samples=100
            )
            
            # Format explanation
            explanation_list = explanation.as_list()
            
            return {
                "method": "LIME",
                "features": [
                    {
                        "feature": feature,
                        "weight": float(weight),
                        "importance": abs(float(weight))
                    }
                    for feature, weight in explanation_list
                ],
                "output_text": output_text,
                "num_features": len(explanation_list)
            }
            
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {e}", exc_info=True)
            return self._simple_explanation(input_text)
    
    def _simple_explanation(self, input_text: str) -> Dict:
        """
        Generate simple explanation without LIME.
        
        Uses keyword extraction and simple heuristics.
        """
        import re
        
        # Extract key financial terms
        financial_keywords = [
            r'\$[\d,]+\.?\d*\s*(?:billion|million|B|M)',
            r'\d+%',
            r'(?:revenue|income|profit|loss|earnings|dividend)',
            r'Q[1-4]\s+\d{4}',
            r'(?:up|down|increase|decrease|growth)',
        ]
        
        features = []
        for pattern in financial_keywords:
            matches = re.finditer(pattern, input_text, re.IGNORECASE)
            for match in matches:
                features.append({
                    "feature": match.group(0),
                    "weight": 0.5,  # Default weight
                    "importance": 0.5
                })
        
        # Limit to top features
        features = sorted(features, key=lambda x: x['importance'], reverse=True)[:10]
        
        return {
            "method": "simple_keyword",
            "features": features,
            "num_features": len(features)
        }
    
    def explain_batch(self, texts: List[str], max_features: int = 10) -> List[Dict]:
        """
        Generate explanations for multiple texts.
        
        Args:
            texts: List of input texts
            max_features: Maximum features per explanation
            
        Returns:
            List of explanation dictionaries
        """
        explanations = []
        for text in texts:
            explanation = self.explain(text, max_features)
            explanations.append(explanation)
        return explanations
