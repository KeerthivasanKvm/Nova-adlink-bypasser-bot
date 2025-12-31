"""
Intelligent Bypass System
Combines traditional methods with AI learning for adaptive bypassing
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

from .ai_learning.ai_agent import ai_agent
from .bypasser import BypassEngine  # Your traditional bypass methods
from database import db

logger = logging.getLogger(__name__)


class IntelligentBypassSystem:
    """
    Intelligent bypass system that learns from attempts
    Combines 10 traditional methods with AI learning
    """
    
    def __init__(self):
        """Initialize intelligent bypass system"""
        self.bypass_engine = BypassEngine()
        self.ai_agent = ai_agent
        
        # Statistics
        self.total_attempts = 0
        self.successful_bypasses = 0
        self.ai_assisted_bypasses = 0
        self.cache_hits = 0
    
    async def bypass(self, url: str, user_id: int = None) -> Dict[str, Any]:
        """
        Main bypass method with AI learning
        
        Args:
            url: URL to bypass
            user_id: User ID for tracking
        
        Returns:
            Bypass result with metadata
        """
        self.total_attempts += 1
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Starting intelligent bypass for: {url}")
            
            # Step 1: Check cache first
            cached_result = await self._check_cache(url)
            if cached_result:
                self.cache_hits += 1
                logger.info(f"💾 Cache hit for: {url}")
                return self._format_result(
                    success=True,
                    url=cached_result,
                    method='cache',
                    time_taken=time.time() - start_time,
                    from_cache=True
                )
            
            # Step 2: Check if we have a learned pattern for this domain
            learned_pattern = await self.ai_agent.get_learned_pattern(url)
            if learned_pattern and learned_pattern.get('success_rate', 0) > 50:
                logger.info(f"🧠 Found learned pattern for domain")
                result = await self._try_learned_method(url, learned_pattern)
                if result['success']:
                    self.successful_bypasses += 1
                    self.ai_assisted_bypasses += 1
                    await self._cache_result(url, result['url'])
                    return result
            
            # Step 3: Try traditional bypass methods (1-10)
            logger.info(f"🔧 Trying traditional bypass methods...")
            traditional_result = await self._try_traditional_methods(url)
            if traditional_result['success']:
                self.successful_bypasses += 1
                await self._cache_result(url, traditional_result['url'])
                
                # Learn from this success if it's a new pattern
                if not learned_pattern:
                    await self._learn_from_success(
                        url,
                        traditional_result['method'],
                        time.time() - start_time
                    )
                
                return traditional_result
            
            # Step 4: All traditional methods failed - Use AI
            logger.info(f"🤖 Traditional methods failed. Activating AI agent...")
            ai_result = await self._ai_assisted_bypass(url, traditional_result.get('failed_methods', []))
            
            if ai_result['success']:
                self.successful_bypasses += 1
                self.ai_assisted_bypasses += 1
                await self._cache_result(url, ai_result['url'])
                
                # Learn from AI success
                await self._learn_from_ai_success(
                    url,
                    ai_result.get('analysis'),
                    ai_result.get('method'),
                    time.time() - start_time
                )
                
                return ai_result
            
            # Step 5: Everything failed
            logger.warning(f"❌ All bypass methods failed for: {url}")
            await self.ai_agent.learn_from_failure(
                url,
                traditional_result.get('failed_methods', []),
                ai_result.get('error', 'Unknown error')
            )
            
            return self._format_result(
                success=False,
                url=None,
                method='none',
                time_taken=time.time() - start_time,
                error='All bypass methods failed'
            )
            
        except Exception as e:
            logger.error(f"❌ Intelligent bypass error: {e}")
            return self._format_result(
                success=False,
                url=None,
                method='error',
                time_taken=time.time() - start_time,
                error=str(e)
            )
    
    async def _check_cache(self, url: str) -> Optional[str]:
        """Check Firebase cache for previously bypassed URL"""
        try:
            return db.get_cached_bypass(url)
        except Exception as e:
            logger.error(f"❌ Cache check error: {e}")
            return None
    
    async def _cache_result(self, original_url: str, bypassed_url: str):
        """Cache successful bypass result"""
        try:
            db.cache_bypass(original_url, bypassed_url)
        except Exception as e:
            logger.error(f"❌ Cache storage error: {e}")
    
    async def _try_learned_method(
        self,
        url: str,
        learned_pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Try bypass using learned pattern
        
        Args:
            url: Target URL
            learned_pattern: Previously learned pattern
        
        Returns:
            Bypass result
        """
        start_time = time.time()
        
        try:
            method_name = learned_pattern.get('method_used')
            logger.info(f"🎯 Trying learned method: {method_name}")
            
            # Get the method from bypass engine
            method = getattr(self.bypass_engine, method_name, None)
            if not method:
                logger.warning(f"⚠️ Learned method {method_name} not found")
                return self._format_result(False, None, 'learned_method_not_found', time.time() - start_time)
            
            # Execute learned method
            result = await method(url)
            
            if result:
                logger.info(f"✅ Learned method succeeded!")
                
                # Update success statistics
                await self._update_pattern_success(learned_pattern['domain'])
                
                return self._format_result(
                    success=True,
                    url=result,
                    method=f"learned_{method_name}",
                    time_taken=time.time() - start_time
                )
            else:
                logger.warning(f"⚠️ Learned method failed")
                return self._format_result(False, None, 'learned_method_failed', time.time() - start_time)
            
        except Exception as e:
            logger.error(f"❌ Learned method execution error: {e}")
            return self._format_result(False, None, 'learned_method_error', time.time() - start_time, str(e))
    
    async def _try_traditional_methods(self, url: str) -> Dict[str, Any]:
        """
        Try all 10 traditional bypass methods in priority order
        
        Args:
            url: Target URL
        
        Returns:
            Bypass result
        """
        start_time = time.time()
        failed_methods = []
        
        # Priority order based on success rate (you can adjust)
        methods = [
            ('html_form', self.bypass_engine.method_html_form),
            ('css_hidden', self.bypass_engine.method_css_hidden),
            ('javascript', self.bypass_engine.method_javascript),
            ('countdown_timer', self.bypass_engine.method_countdown),
            ('dynamic_content', self.bypass_engine.method_dynamic),
            ('cloudflare', self.bypass_engine.method_cloudflare),
            ('redirect_chain', self.bypass_engine.method_redirect),
            ('base64_decode', self.bypass_engine.method_base64),
            ('url_decode', self.bypass_engine.method_url_decode),
            ('browser_automation', self.bypass_engine.method_browser_auto)
        ]
        
        for method_name, method_func in methods:
            try:
                logger.info(f"  → Trying method: {method_name}")
                result = await method_func(url)
                
                if result:
                    logger.info(f"  ✅ Success with method: {method_name}")
                    return self._format_result(
                        success=True,
                        url=result,
                        method=method_name,
                        time_taken=time.time() - start_time
                    )
                else:
                    failed_methods.append(method_name)
                    logger.info(f"  ❌ Failed: {method_name}")
                    
            except Exception as e:
                failed_methods.append(method_name)
                logger.error(f"  ❌ Error in {method_name}: {e}")
        
        return self._format_result(
            success=False,
            url=None,
            method='all_traditional_failed',
            time_taken=time.time() - start_time,
            failed_methods=failed_methods
        )
    
    async def _ai_assisted_bypass(
        self,
        url: str,
        failed_methods: list
    ) -> Dict[str, Any]:
        """
        Use AI to analyze and generate custom bypass strategy
        
        Args:
            url: Target URL
            failed_methods: Methods that already failed
        
        Returns:
            Bypass result
        """
        start_time = time.time()
        
        try:
            logger.info(f"🤖 AI Analysis Phase...")
            
            # Fetch page content
            html_content = await self._fetch_page_content(url)
            if not html_content:
                return self._format_result(
                    False, None, 'ai_fetch_failed',
                    time.time() - start_time,
                    error='Failed to fetch page content'
                )
            
            # AI analyzes the page
            logger.info(f"🧠 AI analyzing page structure...")
            analysis = await self.ai_agent.analyze_page_structure(url, html_content)
            
            if 'error' in analysis:
                return self._format_result(
                    False, None, 'ai_analysis_failed',
                    time.time() - start_time,
                    error=analysis['error']
                )
            
            logger.info(f"✅ AI detected: {analysis.get('protection_type', 'unknown')}")
            
            # AI generates custom bypass code
            logger.info(f"🔧 AI generating custom bypass strategy...")
            custom_code = await self.ai_agent.generate_bypass_code(analysis, url)
            
            if not custom_code:
                return self._format_result(
                    False, None, 'ai_code_generation_failed',
                    time.time() - start_time,
                    error='AI failed to generate bypass code'
                )
            
            # Execute AI-generated code (with safety measures)
            logger.info(f"⚡ Executing AI-generated strategy...")
            result = await self._execute_ai_code(custom_code, url)
            
            if result:
                logger.info(f"🎉 AI bypass succeeded!")
                return self._format_result(
                    success=True,
                    url=result,
                    method='ai_generated',
                    time_taken=time.time() - start_time,
                    analysis=analysis
                )
            else:
                return self._format_result(
                    False, None, 'ai_execution_failed',
                    time.time() - start_time,
                    error='AI-generated code failed to produce result',
                    analysis=analysis
                )
            
        except Exception as e:
            logger.error(f"❌ AI-assisted bypass error: {e}")
            return self._format_result(
                False, None, 'ai_bypass_error',
                time.time() - start_time,
                error=str(e)
            )
    
    async def _fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch page HTML content"""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    return await response.text()
        except Exception as e:
            logger.error(f"❌ Failed to fetch page: {e}")
            return None
    
    async def _execute_ai_code(self, code: str, url: str) -> Optional[str]:
        """
        Safely execute AI-generated code
        
        IMPORTANT: This should have security measures in production!
        Consider using sandboxing or restricted execution environment
        """
        try:
            # TODO: Add security sandboxing
            # For now, we'll use a simplified approach
            
            # Extract the function and execute it
            # This is a placeholder - implement proper execution
            logger.warning("⚠️ AI code execution not fully implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"❌ AI code execution error: {e}")
            return None
    
    async def _learn_from_success(
        self,
        url: str,
        method: str,
        execution_time: float
    ):
        """Learn from successful traditional bypass"""
        try:
            # Create simple analysis from traditional method
            analysis = {
                'protection_type': 'traditional',
                'method_used': method,
                'confidence': 80
            }
            
            await self.ai_agent.learn_from_success(
                url, method, analysis, execution_time
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to learn from success: {e}")
    
    async def _learn_from_ai_success(
        self,
        url: str,
        analysis: Dict[str, Any],
        method: str,
        execution_time: float
    ):
        """Learn from successful AI-assisted bypass"""
        try:
            await self.ai_agent.learn_from_success(
                url, method, analysis, execution_time
            )
        except Exception as e:
            logger.error(f"❌ Failed to learn from AI success: {e}")
    
    async def _update_pattern_success(self, domain: str):
        """Update success statistics for learned pattern"""
        try:
            from google.cloud import firestore
            pattern_ref = db.db.collection('learned_patterns').document(domain)
            pattern_ref.update({
                'successful_attempts': firestore.Increment(1),
                'total_attempts': firestore.Increment(1),
                'last_success': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"❌ Failed to update pattern success: {e}")
    
    def _format_result(
        self,
        success: bool,
        url: Optional[str],
        method: str,
        time_taken: float,
        error: str = None,
        from_cache: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Format bypass result"""
        result = {
            'success': success,
            'url': url,
            'method': method,
            'time_taken': round(time_taken, 2),
            'timestamp': datetime.utcnow().isoformat(),
            'from_cache': from_cache
        }
        
        if error:
            result['error'] = error
        
        # Add any additional data
        result.update(kwargs)
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        success_rate = (
            (self.successful_bypasses / self.total_attempts * 100)
            if self.total_attempts > 0 else 0
        )
        
        ai_usage_rate = (
            (self.ai_assisted_bypasses / self.total_attempts * 100)
            if self.total_attempts > 0 else 0
        )
        
        return {
            'total_attempts': self.total_attempts,
            'successful_bypasses': self.successful_bypasses,
            'success_rate': round(success_rate, 2),
            'cache_hits': self.cache_hits,
            'ai_assisted_bypasses': self.ai_assisted_bypasses,
            'ai_usage_rate': round(ai_usage_rate, 2),
            'ai_stats': self.ai_agent.get_statistics()
        }


# Create global intelligent bypass system
intelligent_bypasser = IntelligentBypassSystem()
