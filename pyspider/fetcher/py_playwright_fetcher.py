import asyncio
import json
import time
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, Response
import logging

logger = logging.getLogger('fetcher')

class PyPlaywrightFetcher:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.playwright = None

    async def init(self):
        """Initialize playwright and browser"""
        if not self.playwright:
            self.playwright = await async_playwright().start()
            browser_options = {
                'args': [
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--ignore-certificate-errors',
                    '--ignore-ssl-errors'
                ]
            }
            self.browser = await self.playwright.chromium.launch(**browser_options)
            logger.info("Browser initialized successfully")

    async def close(self):
        """Close browser and playwright"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def fetch(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch a URL using playwright"""
        start_time = time.time()
        
        try:
            await self.init()
            context = await self.browser.new_context(
                ignore_https_errors=True
            )
            page = await context.new_page()

            # Configure viewport
            await page.set_viewport_size({
                'width': task.get('js_viewport_width', 1024),
                'height': task.get('js_viewport_height', 768 * 3)
            })

            # Set headers
            if task.get('headers'):
                await page.set_extra_http_headers(task['headers'])

            # Handle image loading
            if task.get('load_images') == "false":
                await page.route("**/*", lambda route: route.abort() 
                    if route.request.resource_type == "image" 
                    else route.continue_())

            # Navigate to page
            response: Response = await page.goto(
                task['url'],
                timeout=task.get('timeout', 20) * 1000,
                wait_until='networkidle'
            )

            # Execute custom JavaScript
            script_result = None
            if task.get('js_script'):
                logger.info('Executing custom JavaScript')
                script_result = await page.evaluate(task['js_script'])

            # Take screenshot if requested
            if task.get('screenshot_path'):
                await page.screenshot(path=task['screenshot_path'])

            # Get cookies
            cookies = {}
            raw_cookies = await context.cookies()
            for cookie in raw_cookies:
                cookies[cookie['name']] = cookie['value']

            # Prepare result
            result = {
                'orig_url': task['url'],
                'status_code': response.status if response else 599,
                'error': None,
                'content': await page.content(),
                'headers': dict(response.headers) if response else {},
                'url': page.url,
                'cookies': cookies,
                'time': time.time() - start_time,
                'js_script_result': script_result,
                'save': task.get('save')
            }

            await context.close()
            return result

        except Exception as e:
            logger.error(f"Error during fetch: {str(e)}")
            return {
                'orig_url': task['url'],
                'status_code': 599,
                'error': str(e),
                'content': None,
                'headers': {},
                'url': task['url'],
                'cookies': {},
                'time': time.time() - start_time,
                'js_script_result': None,
                'save': task.get('save')
            }

async def create_fetcher():
    """Create and initialize a new PyPlaywrightFetcher instance"""
    fetcher = PyPlaywrightFetcher()
    await fetcher.init()
    return fetcher

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, HTTPException
    
    app = FastAPI()
    fetcher: Optional[PyPlaywrightFetcher] = None

    @app.on_event("startup")
    async def startup():
        global fetcher
        fetcher = await create_fetcher()

    @app.on_event("shutdown")
    async def shutdown():
        if fetcher:
            await fetcher.close()

    @app.post("/fetch")
    async def fetch(task: Dict[str, Any]):
        if not fetcher:
            raise HTTPException(status_code=500, detail="Fetcher not initialized")
        return await fetcher.fetch(task)

    uvicorn.run(app, host="0.0.0.0", port=22223)