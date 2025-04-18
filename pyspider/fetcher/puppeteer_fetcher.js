const express = require('express');
const app = express();

// Get port from environment variable or use default
const port = process.env.PUPPETEER_FETCHER_PORT || 22222;

app.listen(port, () => {
    console.log(`Server started on port ${port}`);
}).on('error', (err) => {
    console.error('Failed to start server:', err);
    process.exit(1);
});
