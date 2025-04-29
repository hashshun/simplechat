import json
import os
import urllib.request
import re
from botocore.exceptions import ClientError

# 推論APIのURL
INFERENCE_API_URL = os.environ.get("INFERENCE_API_URL", "https://3307-35-199-44-38.ngrok-free.app/")

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        
        print("Processing message:", message)
        
        # 推論APIへのリクエストペイロード
        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        print("Calling inference API with payload:", json.dumps(request_payload))
        
        # リクエストデータの準備
        data = json.dumps(request_payload).encode('utf-8')
        
        # リクエストオブジェクトの作成
        req = urllib.request.Request(
            INFERENCE_API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'Content-Length': len(data)
            },
            method='POST'
        )
        
        try:
            # APIリクエストの送信と応答の取得
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                # アシスタントの応答を取得
                assistant_response = response_data['generated_text']
                response_time = response_data['response_time']
                
                print(f"Response time: {response_time} seconds")
                
        except urllib.error.HTTPError as e:
            error_response = e.read().decode('utf-8')
            print(f"API returned status code {e.code}: {error_response}")
            raise Exception(f"API returned status code {e.code}: {error_response}")
        except urllib.error.URLError as e:
            print(f"Failed to reach the server: {str(e)}")
            raise Exception(f"Failed to reach the server: {str(e)}")
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "response_time": response_time
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }