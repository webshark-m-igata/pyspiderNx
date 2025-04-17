#!/bin/bash

# Navigate to the webui/static directory
cd pyspider/webui/static

# Run webpack to build the assets
npx webpack --config webpack.config.js

echo "WebUI assets built successfully!"
