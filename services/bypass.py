"""
Main Bypass Engine
Contains all 10 traditional bypass methods
"""

import logging
import asyncio
import aiohttp
from typing import Optional
from bs4 import BeautifulSoup
import re
import base64
from urllib.parse import unquote, urlparse
import cloudscraper

logger = logging.getLogger(__name__)


class BypassEngine:
    """
    Main bypass engine with 10 methods
    """
    
    def __init__(self):
        """Initialize bypass engine"""
        self.session = None
        self.scraper = cloudscraper.create_scraper()
        
    async def method_html_form(self, url: str) -> Optional[str]:
        """
        Method 1: HTML Form Bypass
        Handles sites with simple form submissions
        """
        try:
            logger.info("Method 1: HTML Form bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for common download link patterns
            patterns = [
                ('a', {'class': re.compile(r'download|btn-download|get-link')}),
                ('a', {'id': re.compile(r'download|get-link')}),
                ('form', {'action': re.compile(r'download|get')}),
            ]
            
            for tag, attrs in patterns:
                element = soup.find(tag, attrs)
                if element:
                    if tag == 'a':
                        href = element.get('href')
                        if href and href.startswith('http'):
                            return href
                    elif tag == 'form':
                        action = element.get('action')
                        if action:
                            # Submit form if needed
                            return await self._submit_form(url, element)
            
            return None
            
        except Exception as e:
            logger.error(f"Method 1 failed: {e}")
            return None
    
    async def method_css_hidden(self, url: str) -> Optional[str]:
        """
        Method 2: CSS Hidden Elements
        Finds links hidden with CSS display:none or visibility:hidden
        """
        try:
            logger.info("Method 2: CSS Hidden bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all links (including hidden ones)
            hidden_patterns = [
                {'style': re.compile(r'display:\s*none|visibility:\s*hidden')},
                {'class': re.compile(r'hidden|hide|invisible')}
            ]
            
            for pattern in hidden_patterns:
                links = soup.find_all('a', pattern)
                for link in links:
                    href = link.get('href')
                    if href and self._is_valid_download_link(href):
                        return href
            
            return None
            
        except Exception as e:
            logger.error(f"Method 2 failed: {e}")
            return None
    
    async def method_javascript(self, url: str) -> Optional[str]:
        """
        Method 3: JavaScript Execution
        Executes JavaScript to reveal hidden links
        """
        try:
            logger.info("Method 3: JavaScript bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
            
            # Look for JavaScript variables containing links
            patterns = [
                r'var\s+link\s*=\s*["\']([^"\']+)["\']',
                r'href\s*=\s*["\']([^"\']+)["\']',
                r'window\.location\s*=\s*["\']([^"\']+)["\']',
                r'url\s*:\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for match in matches:
                    if self._is_valid_download_link(match):
                        return match
            
            return None
            
        except Exception as e:
            logger.error(f"Method 3 failed: {e}")
            return None
    
    async def method_countdown(self, url: str) -> Optional[str]:
        """
        Method 4: Countdown Timer Bypass
        Waits for or skips countdown timers
        """
        try:
            logger.info("Method 4: Countdown timer bypass")
            
            async with aiohttp.ClientSession() as session:
                # First request
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
                    cookies = response.cookies
                
                # Check if countdown exists
                soup = BeautifulSoup(html, 'html.parser')
                countdown = soup.find(id=re.compile(r'countdown|timer|wait'))
                
                if countdown:
                    # Extract wait time (usually in seconds)
                    time_match = re.search(r'(\d+)\s*second', html.lower())
                    wait_time = int(time_match.group(1)) if time_match else 5
                    
                    logger.info(f"Waiting {wait_time} seconds for countdown...")
                    await asyncio.sleep(min(wait_time, 10))  # Max 10 seconds
                    
                    # Second request after waiting
                    async with session.get(url, cookies=cookies, timeout=30) as response2:
                        html2 = await response2.text()
                        soup2 = BeautifulSoup(html2, 'html.parser')
                        
                        # Find download link
                        link = soup2.find('a', {'class': re.compile(r'download|get-link')})
                        if link:
                            return link.get('href')
            
            return None
            
        except Exception as e:
            logger.error(f"Method 4 failed: {e}")
            return None
    
    async def method_dynamic(self, url: str) -> Optional[str]:
        """
        Method 5: Dynamic Content Loading
        Handles AJAX/fetch loaded content
        """
        try:
            logger.info("Method 5: Dynamic content bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
                    
                # Look for API endpoints in JavaScript
                api_patterns = [
                    r'fetch\(["\']([^"\']+)["\']',
                    r'ajax\(\{[^}]*url:\s*["\']([^"\']+)["\']',
                    r'\.get\(["\']([^"\']+)["\']'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, html)
                    for api_url in matches:
                        if '/api/' in api_url or '/get' in api_url:
                            try:
                                # Try API endpoint
                                full_url = api_url if api_url.startswith('http') else f"{urlparse(url).scheme}://{urlparse(url).netloc}{api_url}"
                                
                                async with session.get(full_url, timeout=20) as api_response:
                                    data = await api_response.json()
                                    
                                    # Look for link in JSON
                                    if isinstance(data, dict):
                                        for key in ['url', 'link', 'download', 'file']:
                                            if key in data:
                                                return data[key]
                            except:
                                continue
            
            return None
            
        except Exception as e:
            logger.error(f"Method 5 failed: {e}")
            return None
    
    async def method_cloudflare(self, url: str) -> Optional[str]:
        """
        Method 6: Cloudflare Bypass
        Uses cloudscraper to bypass Cloudflare protection
        """
        try:
            logger.info("Method 6: Cloudflare bypass")
            
            # Use cloudscraper (handles Cloudflare automatically)
            response = self.scraper.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find download link
            link = soup.find('a', href=re.compile(r'download|get|file'))
            if link:
                return link.get('href')
            
            # Look in scripts
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    match = re.search(r'https?://[^\s"\'<>]+', script.string)
                    if match and self._is_valid_download_link(match.group()):
                        return match.group()
            
            return None
            
        except Exception as e:
            logger.error(f"Method 6 failed: {e}")
            return None
    
    async def method_redirect(self, url: str) -> Optional[str]:
        """
        Method 7: Redirect Chain
        Follows multiple redirects to final URL
        """
        try:
            logger.info("Method 7: Redirect chain bypass")
            
            async with aiohttp.ClientSession() as session:
                current_url = url
                max_redirects = 10
                
                for i in range(max_redirects):
                    async with session.get(current_url, allow_redirects=False, timeout=20) as response:
                        # Check if this is a redirect
                        if response.status in [301, 302, 303, 307, 308]:
                            next_url = response.headers.get('Location')
                            if not next_url:
                                break
                            
                            # Make absolute URL if relative
                            if not next_url.startswith('http'):
                                next_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}{next_url}"
                            
                            logger.info(f"Redirect {i+1}: {next_url}")
                            current_url = next_url
                        else:
                            # Final URL reached
                            return current_url
            
            return current_url if current_url != url else None
            
        except Exception as e:
            logger.error(f"Method 7 failed: {e}")
            return None
    
    async def method_base64(self, url: str) -> Optional[str]:
        """
        Method 8: Base64 Decode
        Decodes Base64 encoded links
        """
        try:
            logger.info("Method 8: Base64 decode bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
            
            # Look for Base64 patterns
            patterns = [
                r'data-url="([A-Za-z0-9+/=]+)"',
                r'data-link="([A-Za-z0-9+/=]+)"',
                r'atob\(["\']([A-Za-z0-9+/=]+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for encoded in matches:
                    try:
                        decoded = base64.b64decode(encoded).decode('utf-8')
                        if decoded.startswith('http'):
                            return decoded
                    except:
                        continue
            
            return None
            
        except Exception as e:
            logger.error(f"Method 8 failed: {e}")
            return None
    
    async def method_url_decode(self, url: str) -> Optional[str]:
        """
        Method 9: URL Decode
        Decodes URL-encoded links
        """
        try:
            logger.info("Method 9: URL decode bypass")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    html = await response.text()
            
            # Look for URL-encoded patterns
            patterns = [
                r'url=([^&\s"\'<>]+)',
                r'link=([^&\s"\'<>]+)',
                r'redirect=([^&\s"\'<>]+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html)
                for encoded in matches:
                    decoded = unquote(encoded)
                    if decoded.startswith('http') and decoded != encoded:
                        return decoded
            
            return None
            
        except Exception as e:
            logger.error(f"Method 9 failed: {e}")
            return None
    
    async def method_browser_auto(self, url: str) -> Optional[str]:
        """
        Method 10: Browser Automation (Selenium/Playwright)
        Full browser simulation as last resort
        """
        try:
            logger.info("Method 10: Browser automation bypass")
            
            # This is a placeholder - full implementation would use Playwright
            # For now, return None (implement when needed)
            logger.warning("Browser automation not fully implemented yet")
            return None
            
        except Exception as e:
            logger.error(f"Method 10 failed: {e}")
            return None
    
    def _is_valid_download_link(self, url: str) -> bool:
        """Check if URL looks like a valid download link"""
        if not url or not url.startswith('http'):
            return False
        
        # Exclude common non-download domains
        exclude_domains = ['facebook.com', 'twitter.com', 'google.com', 'youtube.com']
        parsed = urlparse(url)
        
        if any(domain in parsed.netloc for domain in exclude_domains):
            return False
        
        # Look for download indicators
        download_indicators = ['download', 'file', 'get', '.pdf', '.zip', '.rar', '.mp4', '.mkv']
        return any(indicator in url.lower() for indicator in download_indicators)
    
    async def _submit_form(self, base_url: str, form) -> Optional[str]:
        """Submit form and return result URL"""
        try:
            action = form.get('action')
            method = form.get('method', 'get').lower()
            
            # Build form data
            form_data = {}
            inputs = form.find_all('input')
            for inp in inputs:
                name = inp.get('name')
                value = inp.get('value', '')
                if name:
                    form_data[name] = value
            
            # Submit form
            submit_url = action if action.startswith('http') else f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}{action}"
            
            async with aiohttp.ClientSession() as session:
                if method == 'post':
                    async with session.post(submit_url, data=form_data, timeout=20) as response:
                        return str(response.url)
                else:
                    async with session.get(submit_url, params=form_data, timeout=20) as response:
                        return str(response.url)
                        
        except Exception as e:
            logger.error(f"Form submission failed: {e}")
            return None


# Global bypass engine instance
bypass_engine = BypassEngine()
