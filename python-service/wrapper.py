#!/usr/bin/env python3
import sys
import json
import base64
import traceback
import os
from parse_order_lambda import lambda_handler

if __name__ == '__main__':
    try:
        if len(sys.argv) != 3:
            print(json.dumps({
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'ファイル形式が正しくありません。'
                })
            }))
            sys.exit(1)

        file_bytes = base64.b64decode(sys.argv[1])
        filename = sys.argv[2]

        event = {
            'file_bytes': base64.b64encode(file_bytes).decode('utf-8'),
            'filename': filename
        }
        
        result = lambda_handler(event, None)
        if not result or 'statusCode' not in result:
            print(json.dumps({
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'データの解析に失敗しました。'
                })
            }))
            sys.exit(1)
            
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'statusCode': 500,
            'body': json.dumps({
                'error': f'ファイルの解析中にエラーが発生しました: {str(e)}'
            })
        }))
        traceback.print_exc()
