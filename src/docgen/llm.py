"""
LLM integration module for communicating with Ollama and OpenAI APIs.
"""

import os
from typing import Optional, Dict, Any
import httpx
from openai import OpenAI

from rich.console import Console


# Model mapping with size information
MODEL_MAPPING = {
    "tiny": {
        "name": "tinyllama:1.1b",
        "size_gb": 0.6,
        "description": "Быстро, базовое качество"
    },
    "medium": {
        "name": "gemma2:2b", 
        "size_gb": 1.6,
        "description": "Баланс, хорошее качество"
    },
    "large": {
        "name": "qwen3:8b",
        "size_gb": 5.2,
        "description": "Отличное качество, лучшие результаты"
    }
}


def get_model_info(model_key: str) -> Dict[str, Any]:
    """Get model information by key.
    
    Args:
        model_key: Model key (tiny/medium/large or actual model name).
        
    Returns:
        Dictionary with model info (name, size_gb, description).
    """
    if model_key in MODEL_MAPPING:
        return MODEL_MAPPING[model_key]
    else:
        # Return as-is for custom model names
        return {
            "name": model_key,
            "size_gb": "unknown",
            "description": "Custom model"
        }


class LLMProvider:
    """Base class for LLM providers."""
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the LLM provider.
        
        Args:
            console: Rich console instance for output.
        """
        self.console = console or Console()
    
    def generate(self, prompt: str, system_prompt: str, **kwargs) -> str:
        """Generate text using the LLM.
        
        Args:
            prompt: User prompt.
            system_prompt: System prompt.
            **kwargs: Additional parameters.
            
        Returns:
            Generated text.
        """
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    """Ollama API provider."""
    
    def __init__(
        self,
        base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        model: str = "qwen3:8b",
        console: Optional[Console] = None
    ) -> None:
        super().__init__(console)
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.client = httpx.Client(timeout=300.0)
    
    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 4096,
                 temperature: float = 0.7) -> str:
        """Generate text using Ollama API.
        
        Args:
            prompt: User prompt.
            system_prompt: System prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            
        Returns:
            Generated text.
            
        Raises:
            Exception: If API call fails.
        """
        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                    "stream": False,
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
            
        except httpx.ConnectError:
            raise Exception(f"Could not connect to Ollama at {self.base_url}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")
    
    def check_connection(self) -> bool:
        """Check if Ollama is accessible.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "gpt-3.5-turbo", console: Optional[Console] = None) -> None:
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key.
            base_url: OpenAI API base URL.
            model: Model name to use.
            console: Rich console instance for output.
        """
        super().__init__(console)
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def generate(self, prompt: str, system_prompt: str, max_tokens: int = 4096,
                 temperature: float = 0.7) -> str:
        """Generate text using OpenAI API.
        
        Args:
            prompt: User prompt.
            system_prompt: System prompt.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            
        Returns:
            Generated text.
            
        Raises:
            Exception: If API call fails.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {e}")


class LLMFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(console: Optional[Console] = None) -> LLMProvider:
        """Create appropriate LLM provider based on environment configuration.
        
        Args:
            console: Rich console instance for output.
            
        Returns:
            LLM provider instance.
        """
        # Check for OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if openai_key:
            base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            
            console = console or Console()
            console.print("[green]Using OpenAI API provider[/green]")
            
            return OpenAIProvider(
                api_key=openai_key,
                base_url=base_url,
                model=model,
                console=console,
            )
        else:
            # Use Ollama by default
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:8b")
            
            console = console or Console()
            console.print(f"[green]Using Ollama API provider: {model}[/green]")
            
            provider = OllamaProvider(
                base_url=base_url,
                model=model,
                console=console,
            )
            
            # Check connection
            if not provider.check_connection():
                console.print(f"[yellow]Warning: Could not connect to Ollama at {base_url}[/yellow]")
                console.print("[yellow]Make sure Ollama is running and the model is installed[/yellow]")
            
            return provider
