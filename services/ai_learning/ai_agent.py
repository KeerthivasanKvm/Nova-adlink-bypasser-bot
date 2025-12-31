"""
AI Learning Agent with Google Gemini
Core AI agent that learns from bypass attempts using FREE Gemini API
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import re

# Google Gemini imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Alternative AI (optional)
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from config import Config
from database import db

logger = logging.getLogger(__name__)


class AIBypassAgent:
    """
    Intelligent AI agent using Google Gemini (FREE)
    Learns from bypass attempts and generates custom strategies
    """
    
    def __init__(self):
        """Initialize AI agent with Gemini"""
        self.gemini_model = None
        self.anthropic_client = None
        
        # Initialize available AI clients
        self._initialize_clients()
        
        # Learning statistics
        self.total_analyses = 0
        self.successful_generations = 0
        self.learned_patterns = {}
    
    def _initialize_clients(self):
        """Initialize AI API clients"""
        
        # Google Gemini (Primary - FREE)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and GEMINI_AVAILABLE:
            try:
                genai.configure(api_key=gemini_key)
                # Use Gemini 1.5 Flash (Fast & Free with generous quota)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("✅ Google Gemini initialized (FREE)")
            except Exception as e:
                logger.error(f"❌ Gemini initialization failed: {e}")
        
        # Anthropic Claude (Backup - Optional)
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key and ANTHROPIC_AVAILABLE:
            self.anthropic_client = AsyncAnthropic(api_key=anthropic_key)
            logger.info("✅ Anthropic Claude initialized (Backup)")
        
        if not self.gemini_model and not self.anthropic_client:
            logger.warning("⚠️ No AI clients available. AI learning disabled.")
            logger.warning("💡 Get FREE Gemini API key: https://makersuite.google.com/app/apikey")
    
    async def analyze_page_structure(self, url: str, html_content: str) -> Dict[str, Any]:
        """
        Analyze page structure using AI to identify protection mechanisms
        
        Args:
            url: Target URL
            html_content: Page HTML content
        
        Returns:
            Analysis results with detected protection types
        """
        if not self._is_available():
            return {'error': 'AI service not available'}
        
        try:
            self.total_analyses += 1
            
            # Prepare analysis prompt
            prompt = self._create_analysis_prompt(url, html_content)
            
            # Use available AI model (Gemini first)
            if self.gemini_model:
                result = await self._analyze_with_gemini(prompt)
            elif self.anthropic_client:
                result = await self._analyze_with_anthropic(prompt)
            else:
                return {'error': 'No AI model available'}
            
            # Parse and structure the response
            analysis = self._parse_analysis_result(result)
            
            logger.info(f"✅ AI analysis completed for {url}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return {'error': str(e)}
    
    def _create_analysis_prompt(self, url: str, html_content: str) -> str:
        """Create prompt for AI analysis"""
        # Truncate HTML if too long (Gemini can handle large context but let's optimize)
        html_snippet = html_content[:15000] if len(html_content) > 15000 else html_content
        
        return f"""
You are an expert web scraping and link bypass specialist. Analyze this webpage and identify protection mechanisms.

URL: {url}

HTML Content (truncated if necessary):
```html
{html_snippet}
```

Identify the following:
1. **Protection Type**: What kind of link protection is being used?
   - countdown_timer (wait X seconds)
   - cloudflare_protection (CF challenge)
   - captcha (reCAPTCHA, hCaptcha, etc.)
   - redirect_chain (multiple redirects)
   - javascript_obfuscation (hidden in JS)
   - base64_encoded (encoded links)
   - cookie_required (needs cookies)
   - form_submission (requires form POST)
   - dynamic_loading (AJAX/fetch)
   - multiple_steps (complex multi-step)

2. **Key Elements**: Important HTML elements (IDs, classes, tags)

3. **JavaScript Functions**: JS functions that need execution

4. **Bypass Strategy**: Step-by-step instructions to bypass

5. **Difficulty**: easy, medium, or hard

6. **Recommended Method**: Best approach to bypass this

Respond in valid JSON format only:
{{
    "protection_type": "type_here",
    "confidence": 85,
    "key_elements": ["element1", "element2"],
    "javascript_required": true,
    "bypass_strategy": ["step1", "step2", "step3"],
    "estimated_difficulty": "medium",
    "recommended_method": "method_name",
    "additional_notes": "any important details"
}}

IMPORTANT: Respond ONLY with the JSON object, no additional text or markdown.
"""
    
    async def _analyze_with_gemini(self, prompt: str) -> str:
        """Analyze using Google Gemini (FREE)"""
        try:
            # Generate response asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=2000,
                    )
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"❌ Gemini analysis failed: {e}")
            raise
    
    async def _analyze_with_anthropic(self, prompt: str) -> str:
        """Analyze using Anthropic Claude (Backup)"""
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.3,
                system="You are an expert web scraping and bypass specialist. Analyze webpage structures and provide detailed bypass strategies in JSON format.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"❌ Anthropic analysis failed: {e}")
            raise
    
    def _parse_analysis_result(self, result: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = result.strip()
            
            # Remove markdown code blocks
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
            
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Try to parse as JSON
            analysis = json.loads(cleaned)
            
            # Validate required fields
            required_fields = ['protection_type', 'bypass_strategy']
            if not all(field in analysis for field in required_fields):
                raise ValueError("Missing required fields in analysis")
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse AI response as JSON: {e}")
            # Try to extract JSON from text
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {
                'protection_type': 'unknown',
                'error': 'Failed to parse AI response',
                'raw_response': result[:500]  # Truncate for logging
            }
        except Exception as e:
            logger.error(f"❌ Error parsing analysis: {e}")
            return {
                'protection_type': 'unknown',
                'error': str(e)
            }
    
    async def generate_bypass_code(self, analysis: Dict[str, Any], url: str) -> Optional[str]:
        """
        Generate custom bypass code based on analysis
        
        Args:
            analysis: AI analysis results
            url: Target URL
        
        Returns:
            Generated Python code as string
        """
        if not self._is_available():
            return None
        
        try:
            prompt = self._create_code_generation_prompt(analysis, url)
            
            if self.gemini_model:
                code = await self._generate_with_gemini(prompt)
            elif self.anthropic_client:
                code = await self._generate_with_anthropic(prompt)
            else:
                return None
            
            self.successful_generations += 1
            logger.info(f"✅ Generated custom bypass code for {url}")
            
            return code
            
        except Exception as e:
            logger.error(f"❌ Code generation failed: {e}")
            return None
    
    def _create_code_generation_prompt(self, analysis: Dict[str, Any], url: str) -> str:
        """Create prompt for code generation"""
        return f"""
You are an expert Python developer specializing in web scraping. Generate working Python code to bypass the protection.

Analysis Results:
```json
{json.dumps(analysis, indent=2)}
```

Target URL: {url}

Generate a Python async function called `custom_bypass` that:
1. Takes `url` as parameter
2. Implements the bypass strategy from the analysis
3. Returns the final bypassed/direct URL as a string
4. Uses these libraries: aiohttp, BeautifulSoup4, selenium (if needed)
5. Handles errors gracefully with try-except
6. Includes comments explaining each step
7. Has proper timeout handling

Requirements:
- Must be async function
- Return None if bypass fails
- Include proper error handling
- Use existing libraries only (aiohttp, bs4, selenium)
- Keep it simple and working

Example structure:
```python
import aiohttp
from bs4 import BeautifulSoup

async def custom_bypass(url):
    try:
        # Your bypass logic here
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
        
        soup = BeautifulSoup(html, 'html.parser')
        # Extract final URL
        final_url = soup.find('a', class_='download-link')['href']
        return final_url
    except Exception as e:
        print(f"Error: {{e}}")
        return None
```

Generate ONLY the Python code, no explanations or markdown. Start directly with imports.
"""
    
    async def _generate_with_gemini(self, prompt: str) -> str:
        """Generate code using Google Gemini"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=3000,
                    )
                )
            )
            
            # Clean the response (remove markdown if present)
            code = response.text.strip()
            
            # Remove markdown code blocks
            if code.startswith('```python'):
                code = code[9:]
            elif code.startswith('```'):
                code = code[3:]
            
            if code.endswith('```'):
                code = code[:-3]
            
            return code.strip()
            
        except Exception as e:
            logger.error(f"❌ Gemini code generation failed: {e}")
            raise
    
    async def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate code using Anthropic (Backup)"""
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.2,
                system="You are an expert Python developer specializing in web scraping. Generate clean, working Python code.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"❌ Anthropic code generation failed: {e}")
            raise
    
    async def learn_from_success(
        self,
        url: str,
        method_used: str,
        analysis: Dict[str, Any],
        execution_time: float
    ):
        """
        Store successful bypass pattern for future use
        
        Args:
            url: Original URL
            method_used: Method that succeeded
            analysis: AI analysis that was used
            execution_time: Time taken to bypass
        """
        try:
            domain = self._extract_domain(url)
            
            # Create learning record
            pattern = {
                'domain': domain,
                'protection_type': analysis.get('protection_type', 'unknown'),
                'method_used': method_used,
                'success_rate': 100,
                'total_attempts': 1,
                'successful_attempts': 1,
                'avg_execution_time': execution_time,
                'analysis': analysis,
                'created_at': datetime.utcnow(),
                'last_success': datetime.utcnow()
            }
            
            # Store in Firebase
            pattern_ref = db.db.collection('learned_patterns').document(domain)
            pattern_ref.set(pattern)
            
            # Cache in memory
            self.learned_patterns[domain] = pattern
            
            logger.info(f"✅ Learned pattern stored for {domain}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store learned pattern: {e}")
    
    async def learn_from_failure(
        self,
        url: str,
        failed_methods: List[str],
        error_message: str
    ):
        """
        Learn from failed bypass attempts
        
        Args:
            url: Original URL
            failed_methods: Methods that failed
            error_message: Error encountered
        """
        try:
            domain = self._extract_domain(url)
            
            from google.cloud import firestore
            
            # Update pattern if exists
            pattern_ref = db.db.collection('learned_patterns').document(domain)
            pattern_doc = pattern_ref.get()
            
            if pattern_doc.exists:
                # Update failure statistics
                pattern_ref.update({
                    'total_attempts': firestore.Increment(1),
                    'last_failure': datetime.utcnow(),
                    'failed_methods': firestore.ArrayUnion(failed_methods),
                    'last_error': error_message
                })
                
                logger.info(f"✅ Updated failure data for {domain}")
            else:
                # Create new failure record
                pattern_ref.set({
                    'domain': domain,
                    'protection_type': 'unknown',
                    'total_attempts': 1,
                    'successful_attempts': 0,
                    'success_rate': 0,
                    'failed_methods': failed_methods,
                    'last_error': error_message,
                    'created_at': datetime.utcnow(),
                    'needs_ai_analysis': True
                })
            
        except Exception as e:
            logger.error(f"❌ Failed to record failure: {e}")
    
    async def get_learned_pattern(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve learned pattern for domain
        
        Args:
            url: Target URL
        
        Returns:
            Learned pattern if exists
        """
        try:
            domain = self._extract_domain(url)
            
            # Check memory cache first
            if domain in self.learned_patterns:
                return self.learned_patterns[domain]
            
            # Query Firebase
            pattern_ref = db.db.collection('learned_patterns').document(domain)
            pattern_doc = pattern_ref.get()
            
            if pattern_doc.exists:
                pattern = pattern_doc.to_dict()
                
                # Cache in memory
                self.learned_patterns[domain] = pattern
                
                return pattern
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get learned pattern: {e}")
            return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    
    def _is_available(self) -> bool:
        """Check if AI service is available"""
        return self.gemini_model is not None or self.anthropic_client is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_analyses': self.total_analyses,
            'successful_generations': self.successful_generations,
            'learned_patterns_count': len(self.learned_patterns),
            'available_models': {
                'gemini': self.gemini_model is not None,
                'anthropic': self.anthropic_client is not None
            },
            'primary_model': 'Google Gemini 1.5 Flash (FREE)' if self.gemini_model else 'None'
        }


# Create global AI agent instance
ai_agent = AIBypassAgent()
