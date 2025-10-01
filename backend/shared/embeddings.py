"""AI Embeddings support using Anthropic Claude."""

import os
from typing import List, Optional
import anthropic
import json


class EmbeddingGenerator:
    """Generate embeddings for semantic search using Claude."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the embedding generator."""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Claude.
        
        Since Anthropic doesn't have a direct embedding API, we'll use a simplified
        approach: create a hash-based vector representation.
        
        For production, you'd want to use OpenAI embeddings or similar.
        """
        if not text or not text.strip():
            return []
        
        try:
            # Clean the text
            cleaned_text = text.strip()[:8000]  # Limit length
            
            # For now, create a simple hash-based vector
            # In production, you'd use OpenAI's text-embedding-3-small or similar
            import hashlib
            
            # Create a 384-dimensional vector (common embedding size)
            hash_obj = hashlib.sha256(cleaned_text.encode())
            hash_bytes = hash_obj.digest()
            
            # Extend to 384 dimensions
            vector = []
            for i in range(48):  # 48 * 8 = 384
                byte_val = hash_bytes[i % 32]
                # Create 8 float values from each byte
                for bit in range(8):
                    vector.append(float((byte_val >> bit) & 1))
            
            # Normalize the vector
            magnitude = sum(x * x for x in vector) ** 0.5
            if magnitude > 0:
                vector = [x / magnitude for x in vector]
            
            print(f"✅ EMBEDDING: Generated {len(vector)}-dimensional vector for text of length {len(cleaned_text)}")
            return vector
            
        except Exception as e:
            print(f"❌ EMBEDDING: Error generating embedding: {e}")
            return []
    
    def generate_content_summary(self, text: str, max_words: int = 100) -> str:
        """Generate a summary of the content using Claude."""
        if not text or not text.strip():
            return ""
        
        try:
            cleaned_text = text.strip()[:10000]  # Limit for API
            
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cost-effective model
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"Summarize this web page content in {max_words} words or less, focusing on the main purpose and key information:\n\n{cleaned_text}"
                }]
            )
            
            summary = message.content[0].text.strip()
            print(f"✅ SUMMARY: Generated {len(summary)} character summary")
            return summary
            
        except Exception as e:
            print(f"❌ SUMMARY: Error generating summary: {e}")
            # Return truncated text as fallback
            return cleaned_text[:500]


# Alternative: OpenAI embeddings (recommended for production)
class OpenAIEmbeddingGenerator:
    """Generate embeddings using OpenAI's API (more reliable for production)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI embedding generator."""
        try:
            import openai
            self.openai = openai
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            
            if not self.api_key:
                raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
            
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = "text-embedding-3-small"
            print("✅ EMBEDDING: OpenAI embedding generator initialized")
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI's text-embedding-3-small model."""
        if not text or not text.strip():
            return []
        
        try:
            cleaned_text = text.strip()[:8000]  # Token limit
            
            response = self.client.embeddings.create(
                model=self.model,
                input=cleaned_text
            )
            
            embedding = response.data[0].embedding
            print(f"✅ EMBEDDING: Generated {len(embedding)}-dimensional vector using OpenAI")
            return embedding
            
        except Exception as e:
            print(f"❌ EMBEDDING: OpenAI error: {e}")
            return []


def get_embedding_generator() -> EmbeddingGenerator:
    """Get the appropriate embedding generator based on available API keys."""
    
    # Try OpenAI first (recommended)
    if os.getenv("OPENAI_API_KEY"):
        try:
            return OpenAIEmbeddingGenerator()
        except:
            pass
    
    # Fall back to basic hash-based embeddings
    if os.getenv("ANTHROPIC_API_KEY"):
        return EmbeddingGenerator()
    
    raise ValueError("No embedding API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")

