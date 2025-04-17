const express = require('express');
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');
const cluster = require('cluster');
const os = require('os');
const app = express();

// Get port from environment variable or use default
const port = process.env.PUPPETEER_FETCHER_PORT || 22229;

// Number of workers (use half of available CPUs)
const numWorkers = Math.max(1, Math.floor(os.cpus().length / 2));

// Browser instance cache
let browserInstance = null;
let lastBrowserUse = Date.now();
const BROWSER_IDLE_TIMEOUT = 5 * 60 * 1000; // 5 minutes

// Configure Express
app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '50mb' }));
app.use(express.json({ limit: '50mb' }));

// Enable compression
app.use(require('compression')());

// Add request timeout
app.use(require('connect-timeout')('120s'));

// Handle browser errors
process.on('unhandledRejection', (reason, p) => {
    console.error('Unhandled Rejection at:', p, 'reason:', reason);
});

// Get or create browser instance
async function getBrowser() {
    if (!browserInstance) {
        console.log('Creating new browser instance');
        // Read options from environment variables if available
        const launchOptions = {
            headless: 'new',
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-audio',
                '--disable-sync',
                '--disable-translate',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-web-security',
                '--no-first-run',
                '--no-zygote',
                '--disable-notifications',
                '--disable-background-timer-throttling',
                '--disable-breakpad',
                '--disable-component-update',
                '--disable-domain-reliability',
                '--disable-features=TranslateUI,BlinkGenPropertyTrees',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--mute-audio',
                '--window-size=1280,800'
            ],
            ignoreHTTPSErrors: true,
            pipe: true,
            userDataDir: './puppeteer_cache'
        };

        // Try to read config from environment
        try {
            if (process.env.PUPPETEER_ARGS) {
                const envArgs = JSON.parse(process.env.PUPPETEER_ARGS);
                if (Array.isArray(envArgs)) {
                    launchOptions.args = envArgs;
                }
            }
        } catch (e) {
            console.error('Error parsing PUPPETEER_ARGS:', e);
        }

        browserInstance = await puppeteer.launch(launchOptions);
    }
    lastBrowserUse = Date.now();
    return browserInstance;
}

// Check and close idle browser
setInterval(async () => {
    if (browserInstance && (Date.now() - lastBrowserUse > BROWSER_IDLE_TIMEOUT)) {
        console.log('Closing idle browser instance');
        await browserInstance.close().catch(err => console.error('Error closing browser:', err));
        browserInstance = null;
    }
}, 60000); // Check every minute

// Puppeteer fetch endpoint
app.post('/fetch', async (req, res) => {
    let browser = null;
    let page = null;

    try {
        // Get browser instance
        browser = await getBrowser();

        // Create new page
        page = await browser.newPage();

        // Set performance optimizations
        await page.setCacheEnabled(true);
        await page.setRequestInterception(true);

        // Intercept requests to block unnecessary resources
        page.on('request', (request) => {
            const resourceType = request.resourceType();
            if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
                request.abort();
            } else {
                request.continue();
            }
        });

        // Set default timeout
        page.setDefaultTimeout(req.body.timeout || 30000);

        // Set user agent if provided
        if (req.body.headers && req.body.headers['User-Agent']) {
            await page.setUserAgent(req.body.headers['User-Agent']);
        }

        // Set headers if provided
        if (req.body.headers) {
            await page.setExtraHTTPHeaders(req.body.headers);
        }

        // Set viewport
        await page.setViewport({
            width: req.body.js_viewport_width || 1280,
            height: req.body.js_viewport_height || 800
        });

        // Navigate to URL with optimized settings
        const response = await page.goto(req.body.url, {
            waitUntil: req.body.wait_until || 'domcontentloaded', // Faster than networkidle2
            timeout: req.body.timeout || 30000
        });

        // Execute script if provided
        let scriptResult = null;
        if (req.body.js_script) {
            scriptResult = await page.evaluate(req.body.js_script);
        }

        // Get page content
        const content = await page.content();

        // Get cookies
        const cookies = await page.cookies();
        const cookieObj = {};
        cookies.forEach(cookie => {
            cookieObj[cookie.name] = cookie.value;
        });

        // Get response headers
        const headers = response ? response.headers() : {};

        // Create result object
        const result = {
            orig_url: req.body.url,
            status_code: response ? response.status() : 599,
            error: null,
            content: content,
            headers: headers,
            url: page.url(),
            cookies: cookieObj,
            time: Date.now() / 1000,
            js_script_result: scriptResult,
            save: req.body.save
        };

        res.json(result);
    } catch (error) {
        console.error('Error during fetch:', error);
        res.json({
            orig_url: req.body.url,
            status_code: 599,
            error: error.toString(),
            content: '',
            headers: {},
            url: req.body.url,
            cookies: {},
            time: Date.now() / 1000,
            js_script_result: null,
            save: req.body.save
        });
    } finally {
        if (page) {
            await page.close().catch(err => console.error('Error closing page:', err));
        }
    }
});

// Health check endpoint
app.get('/status', (req, res) => {
    res.json({ status: 'ok' });
});

// Start server
app.listen(port, () => {
    console.log(`Server started on port ${port}`);
}).on('error', (err) => {
    console.error('Failed to start server:', err);
    process.exit(1);
});
