#!/bin/bash

# ポート番号の定義
PHANTOMJS_PORT=25559
PUPPETEER_PORT=22227
WEBUI_PORT=5000
SCHEDULER_PORT=23334
FETCHER_PORT=24445

# 各ポートを使用しているプロセスを終了
for port in $PHANTOMJS_PORT $PUPPETEER_PORT $WEBUI_PORT $SCHEDULER_PORT $FETCHER_PORT; do
    pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        echo "ポート $port を使用しているプロセス $pid を終了します"
        kill -9 $pid
    fi
done
a
# pyspiderプロセスを終了
pyspider_pids=$(pgrep -f "pyspider")
if [ ! -z "$pyspider_pids" ]; then
    echo "pyspiderプロセスを終了します"
    kill -9 $pyspider_pids
fi

echo "すべてのプロセスを終了しました" 