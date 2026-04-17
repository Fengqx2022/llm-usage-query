#!/usr/bin/env python3
"""
移动云大模型使用量查询工具
API: POST https://ecloud.10086.cn/api/web/maas/console/studio/query
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "config.json"

def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """保存配置文件"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def query_ecloud_usage(pool_id="CIDC-RP-48", token=None):
    """
    查询移动云大模型使用量
    
    Args:
        pool_id: 资源池ID，默认 CIDC-RP-48（华北-呼和浩特）
        token: CMECLOUDTOKEN，如果为None则从配置文件读取
    
    Returns:
        dict: 使用量数据
    """
    # 从配置文件读取token
    config = load_config()
    if token is None:
        token = config.get('ecloud_token')
    
    if not token:
        print("错误：未设置 CMECLOUDTOKEN")
        print("请运行: python ecloud_usage.py --set-token YOUR_TOKEN")
        return None
    
    url = "https://ecloud.10086.cn/api/web/maas/console/studio/query"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Cookie": f"CMECLOUDTOKEN={token}",
        "pool_id": pool_id,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "startTime": "",
        "endTime": "",
        "pageNo": 1,
        "pageSize": 10,
        "keyword": "",
        "chaGroupType": "5",
        "feeType": "MONTH",
        "sortParams": [{"fieldName": "", "sortOrder": "ASC"}]
    }
    
    response = None
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # 检查是否返回了有效数据
        if 'dataRows' not in data:
            print("错误：API返回数据格式异常，可能是Token已过期")
            if response:
                print(f"响应内容: {response.text[:200]}")
            return None
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        if response:
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容前200字符: {response.text[:200]}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON解析失败，可能是Token已过期或网络问题")
        if response:
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容前200字符: {response.text[:200]}")
        return None

def format_usage(data):
    """格式化使用量数据"""
    if not data or 'dataRows' not in data:
        return "无数据"
    
    result = []
    result.append("=" * 60)
    result.append("移动云大模型使用量")
    result.append("=" * 60)
    
    for row in data['dataRows']:
        if row.get('ordered'):  # 只显示已订购的套餐
            result.append(f"\n套餐: {row.get('chaGroupName', '未知')}")
            result.append(f"资源池: {row.get('poolName', '未知')}")
            result.append(f"状态: {row.get('resourceStatus', '未知')}")
            result.append(f"到期时间: {row.get('expireTime', '未知')}")
            
            # 日使用量
            day_used = row.get('dayUsedCount', 0)
            day_total = row.get('dayInitCount', 0)
            if day_total > 0:
                day_percent = (day_used / day_total) * 100
                result.append(f"\n近5小时用量: {day_used}/{day_total} ({day_percent:.1f}%)")
            
            # 周使用量
            week_used = row.get('weekUsedCount', 0)
            week_total = row.get('weekInitCount', 0)
            if week_total > 0:
                week_percent = (week_used / week_total) * 100
                result.append(f"近1周用量: {week_used}/{week_total} ({week_percent:.1f}%)")
            
            # 月使用量
            month_used = row.get('monthUsedCount', 0)
            month_total = row.get('monthInitCount', 0)
            if month_total > 0:
                month_percent = (month_used / month_total) * 100
                result.append(f"近1月用量: {month_used}/{month_total} ({month_percent:.1f}%)")
            
            result.append("-" * 60)
    
    return "\n".join(result)

def set_token(token):
    """设置Token"""
    config = load_config()
    config['ecloud_token'] = token
    save_config(config)
    print(f"Token已保存到: {CONFIG_FILE}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--set-token' and len(sys.argv) > 2:
            set_token(sys.argv[2])
            return
        elif sys.argv[1] == '--help':
            print("用法:")
            print("  python ecloud_usage.py                 # 查询使用量")
            print("  python ecloud_usage.py --set-token XXX # 设置Token")
            print("  python ecloud_usage.py --help          # 显示帮助")
            return
    
    # 查询使用量
    data = query_ecloud_usage()
    if data:
        print(format_usage(data))

if __name__ == "__main__":
    main()
