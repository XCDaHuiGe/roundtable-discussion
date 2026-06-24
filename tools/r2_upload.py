#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2上传工具 - 使用SigV4签名上传图片到Cloudflare R2"""

import json
import os
import hashlib
import hmac
import datetime
import base64
import requests
from urllib.parse import quote

def load_r2_config():
    """加载R2配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', '.r2_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def sign(key, msg):
    """HMAC-SHA256签名"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def get_signature_key(key, date_stamp, region, service):
    """生成签名密钥"""
    k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
    return k_signing

def upload_to_r2(local_path, remote_key=None):
    """
    上传文件到R2
    
    Args:
        local_path: 本地文件路径
        remote_key: R2中的文件名（可选，默认使用roundtable/前缀+本地文件名）
    
    Returns:
        上传后的URL
    """
    config = load_r2_config()
    
    if not remote_key:
        filename = os.path.basename(local_path)
        remote_key = f'roundtable/{filename}'
    
    # 读取文件
    with open(local_path, 'rb') as f:
        content = f.read()
    
    # 计算哈希
    payload_hash = hashlib.sha256(content).hexdigest()
    
    # 生成时间
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')
    
    # AWS参数
    service = 's3'
    region = 'auto'
    host = config['endpoint'].replace('https://', '')
    
    # 构建请求
    request_uri = f'/{config["bucket"]}/{remote_key}'
    canonical_uri = quote(request_uri, safe='/')
    
    # 规范请求
    canonical_querystring = ''
    canonical_headers = f'host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n'
    signed_headers = 'host;x-amz-content-sha256;x-amz-date'
    
    canonical_request = f'PUT\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
    
    # 字符串签名
    credential_scope = f'{date_stamp}/{region}/{service}/aws4_request'
    string_to_sign = f'AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
    
    # 计算签名
    signing_key = get_signature_key(config['secret_key'], date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 构建Authorization
    authorization_header = f'AWS4-HMAC-SHA256 Credential={config["access_key"]}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
    
    # 上传
    headers = {
        'Host': host,
        'x-amz-date': amz_date,
        'x-amz-content-sha256': payload_hash,
        'Authorization': authorization_header,
        'Content-Type': 'image/png'
    }
    
    # 禁用代理
    session = requests.Session()
    session.trust_env = False
    
    response = session.put(config['endpoint'] + request_uri, data=content, headers=headers)
    
    if response.status_code in [200, 201]:
        public_url = f'{config["public_url"]}/{remote_key}'
        print(f'Uploaded: {local_path} -> {public_url}')
        return public_url
    else:
        print(f'Upload failed: {response.status_code} {response.text[:200]}')
        return None

def upload_directory(local_dir, prefix='roundtable'):
    """上传整个目录到R2"""
    results = []
    
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, local_dir)
                remote_key = f'{prefix}/{relative_path}'.replace('\', '/')
                
                url = upload_to_r2(local_path, remote_key)
                if url:
                    results.append({
                        'local': local_path,
                        'remote': remote_key,
                        'url': url
                    })
    
    return results

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python r2_upload.py <file_or_directory> [remote_key]")
        sys.exit(1)
    
    path = sys.argv[1]
    remote_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    if os.path.isdir(path):
        results = upload_directory(path)
        print(f"\nUploaded {len(results)} files")
    else:
        upload_to_r2(path, remote_key)
