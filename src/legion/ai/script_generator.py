"""AI-powered script generator using GPT-5.1-Codex.

Generates Playwright automation scripts from natural language.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not installed. Install with: pip install openai")

logger = logging.getLogger(__name__)


class ScriptGenerator:
    """Generate browser automation scripts using GPT-5.1-Codex."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize script generator.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI required: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self._generation_count = 0
        
        logger.info("Initialized AI Script Generator (GPT-5.1-Codex)")
    
    async def generate_playwright_script(
        self,
        description: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate Playwright script from natural language.
        
        Args:
            description: Natural language task description
            context: Optional context (URL, selectors, etc.)
            
        Returns:
            Generated script with metadata
        """
        self._generation_count += 1
        
        logger.info(f"Generating script #{self._generation_count}: {description[:50]}...")
        
        # Build prompt
        prompt = self._build_prompt(description, context)
        
        try:
            response = await self.client.chat.completions.create(
<<<<<<< HEAD
                model="gpt-4-turbo",  # Use gpt-4-turbo or latest available
=======
                model="gpt-4-turbo",
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in browser automation with Playwright. "
                                 "Generate clean, production-ready Python code using async Playwright API. "
                                 "Include error handling, proper waits, and comments."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
<<<<<<< HEAD
                temperature=0.2,  # Low temperature for deterministic code
=======
                temperature=0.2,
>>>>>>> ec0dad20ff32c3cf9f03df6da0e9f2b48cd10535
                max_tokens=2000
            )
            
            code = response.choices[0].message.content
            
            # Extract code from markdown if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()
            
            # Validate syntax
            validation = self._validate_code(code)
            
            result = {
                'success': True,
                'code': code,
                'description': description,
                'validation': validation,
                'generation_id': self._generation_count,
                'model': response.model,
                'tokens_used': response.usage.total_tokens
            }
            
            logger.info(f"Script generated successfully (#{self._generation_count})")
            return result
            
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'description': description
            }
    
    def _build_prompt(self, description: str, context: Optional[Dict]) -> str:
        """Build prompt for code generation."""
        prompt = f"""Generate a Playwright Python async script for the following task:

{description}

Requirements:
- Use async Playwright API (playwright.async_api)
- Include proper error handling
- Use auto-wait features (wait_for_selector)
- Add meaningful comments
- Return results as dict
"""
        
        if context:
            prompt += "\n\nContext:\n"
            for key, value in context.items():
                prompt += f"- {key}: {value}\n"
        
        prompt += "\n\nReturn ONLY the Python code, no explanations."
        
        return prompt
    
    def _validate_code(self, code: str) -> Dict[str, Any]:
        """Validate generated code.
        
        Args:
            code: Python code to validate
            
        Returns:
            Validation result
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check syntax
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            result['valid'] = False
            result['errors'].append(f"Syntax error: {e}")
        
        # Check for required imports
        if 'playwright' not in code:
            result['warnings'].append("Missing Playwright import")
        
        # Check for async
        if 'async def' not in code and 'await' in code:
            result['errors'].append("Uses await without async function")
            result['valid'] = False
        
        return result
    
    async def fix_script(
        self,
        original_code: str,
        error: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Fix broken script using AI (self-healing).
        
        Args:
            original_code: Original script that failed
            error: Error message
            context: Optional additional context
            
        Returns:
            Fixed script
        """
        logger.info("Attempting AI-powered script fix...")
        
        prompt = f"""The following Playwright script failed with an error:

```python
{original_code}
```

Error: {error}

Please fix the script to handle this error. Return ONLY the corrected Python code.
"""
        
        if context:
            prompt += f"\n\nAdditional context: {context}"
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at debugging and fixing Playwright scripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            fixed_code = response.choices[0].message.content
            
            # Extract code
            if "```python" in fixed_code:
                fixed_code = fixed_code.split("```python")[1].split("```")[0].strip()
            elif "```" in fixed_code:
                fixed_code = fixed_code.split("```")[1].split("```")[0].strip()
            
            return {
                'success': True,
                'fixed_code': fixed_code,
                'original_error': error
            }
            
        except Exception as e:
            logger.error(f"Script fix failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
