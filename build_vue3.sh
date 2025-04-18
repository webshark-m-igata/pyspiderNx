#!/bin/bash

# Vue.js 3用のJavaScriptをビルドするスクリプト
echo "Building Vue.js 3 JavaScript files..."

# index.vue3.jsをindex.vue3.min.jsにコピー
cp pyspider/webui/static/src/index.vue3.js pyspider/webui/static/index.vue3.min.js

echo "Build completed!"
