const express = require('express');
const app = express();

// Get port from environment variable, command line argument, or use default
const port = process.env.PUPPETEER_FETCHER_PORT || process.argv[2] || 22222;

app.listen(port, () => {
    console.log(`Server started on port ${port}`);
}).on('error', (err) => {
    console.error('Failed to start server:', err);
    process.exit(1);
});
