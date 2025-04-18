#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Trae AI
# Created on 2025-04-18

import os
import json
from flask import jsonify, render_template
from .app import app

@app.route('/products/view', methods=['GET'])
def view_products():
    """
    製品データを表示するHTMLページ
    """
    return render_template('products.html')

@app.route('/products', methods=['GET'])
def get_products():
    """
    製品データをJSONフォーマットで返すAPIエンドポイント
    """
    try:
        # プロジェクトルートからJSONファイルのパスを取得
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                'amazon_products_20250415.json')
        
        # JSONファイルが存在するか確認
        if not os.path.exists(json_path):
            return jsonify({
                'status': 'error',
                'message': 'Products data file not found'
            }), 404
            
        # JSONファイルを読み込む
        with open(json_path, 'r', encoding='utf-8') as f:
            # 単一のJSONオブジェクトの場合
            product_data = json.load(f)
            
            # 配列に変換して返す
            if isinstance(product_data, dict):
                products = [product_data]
            else:
                products = product_data
                
            return jsonify({
                'status': 'success',
                'data': products
            })
            
    except Exception as e:
        app.logger.error(f'Error loading products data: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': f'Error loading products data: {str(e)}'
        }), 500