#!/usr/bin/env python3
"""
大模型使用量监控 - Streamlit Web界面
运行: streamlit run app.py
"""

import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go

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
    """查询移动云大模型使用量"""
    config = load_config()
    if token is None:
        token = config.get('ecloud_token')
    
    if not token:
        return None, "未设置Token"
    
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'dataRows' not in data:
            return None, "Token已过期或无效"
        
        return data, None
        
    except Exception as e:
        return None, f"请求失败: {str(e)}"

def query_qianfan_usage(cookie=None):
    """查询千帆大模型使用量"""
    config = load_config()
    if cookie is None:
        cookie = config.get('qianfan_cookie')
    
    if not cookie:
        return None, "未设置Cookie"
    
    url = "https://console.bce.baidu.com/api/qianfan/charge/codingPlan/resourceList"
    
    # 从完整Cookie中提取关键字段
    cookie_dict = {}
    for item in cookie.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            cookie_dict[key] = value
    
    # 提取必要的字段
    bce_user_info = cookie_dict.get('bce-user-info', '')
    
    headers = {
        "Accept": "application/json;charset=UTF-8",
        "Content-Type": "application/json",
        "Cookie": cookie,
        "csrftoken": bce_user_info,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://console.bce.baidu.com/qianfan/resource/subscribe"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            return None, "请求失败或Cookie已过期"
        
        return data.get('result', {}), None
        
    except Exception as e:
        return None, f"请求失败: {str(e)}"

def create_progress_chart(used, total, title, color='#FF4B4B'):
    """创建环形进度图"""
    percent = (used / total * 100) if total > 0 else 0
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = percent,
        title = {'text': title, 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#E8F5E9'},
                {'range': [50, 80], 'color': '#FFF3E0'},
                {'range': [80, 100], 'color': '#FFEBEE'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        },
        number = {'suffix': '%', 'font': {'size': 24}}
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

def generate_suggestions(ecloud_summary, qianfan_summary):
    """生成使用建议"""
    suggestions = []
    
    # 移动云建议
    if ecloud_summary:
        month_rate = ecloud_summary['month_used'] / ecloud_summary['month_total'] if ecloud_summary['month_total'] > 0 else 0
        five_hour_rate = ecloud_summary['five_hour_used'] / ecloud_summary['five_hour_total'] if ecloud_summary['five_hour_total'] > 0 else 0
        days_to_expire = ecloud_summary.get('days_to_expire', 999)
        
        # 月使用率预警
        if month_rate > 0.9:
            remaining = ecloud_summary['month_total'] - ecloud_summary['month_used']
            suggestions.append(f"🔴 移动云本月仅剩 {remaining:,} 次（{100-month_rate*100:.0f}%），请节约使用")
        elif month_rate > 0.7:
            suggestions.append(f"🟡 移动云本月已用 {month_rate*100:.0f}%，建议关注")
        
        # 5小时预警
        if five_hour_rate > 0.8:
            suggestions.append(f"🔴 移动云近5小时仅剩 {(1-five_hour_rate)*100:.0f}%")
        
        # 到期预警
        if days_to_expire <= 3:
            suggestions.append(f"🔴 移动云即将到期（{days_to_expire}天后），请及时续费")
    
    # 千帆建议
    if qianfan_summary:
        month_rate = qianfan_summary['month_used'] / qianfan_summary['month_total'] if qianfan_summary['month_total'] > 0 else 0
        five_hour_rate = qianfan_summary['five_hour_used'] / qianfan_summary['five_hour_total'] if qianfan_summary['five_hour_total'] > 0 else 0
        days_to_expire = qianfan_summary.get('days_to_expire', 999)
        
        if month_rate > 0.9:
            remaining = qianfan_summary['month_total'] - qianfan_summary['month_used']
            suggestions.append(f"🔴 千帆本月仅剩 {remaining:,} 次（{100-month_rate*100:.0f}%），请节约使用")
        elif month_rate > 0.7:
            suggestions.append(f"🟡 千帆本月已用 {month_rate*100:.0f}%，建议关注")
        
        if five_hour_rate > 0.8:
            suggestions.append(f"🔴 千帆近5小时仅剩 {(1-five_hour_rate)*100:.0f}%")
        
        if days_to_expire <= 3:
            suggestions.append(f"🔴 千帆即将到期（{days_to_expire}天后），请及时续费")
    
    # 跨平台建议
    if ecloud_summary and qianfan_summary:
        ecloud_rate = ecloud_summary['month_used'] / ecloud_summary['month_total'] if ecloud_summary['month_total'] > 0 else 0
        qianfan_rate = qianfan_summary['month_used'] / qianfan_summary['month_total'] if qianfan_summary['month_total'] > 0 else 0
        
        if abs(ecloud_rate - qianfan_rate) > 0.4:
            target = "千帆" if ecloud_rate > qianfan_rate else "移动云"
            suggestions.append(f"💡 建议将任务迁移到{target}（使用率更低）")
    
    return suggestions

def main():
    st.set_page_config(
        page_title="大模型使用量监控",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 标题
    st.title("📊 大模型使用量监控")
    st.markdown("---")
    
    # 侧边栏 - Token设置
    with st.sidebar:
        st.header("⚙️ 设置")
        
        config = load_config()
        
        # 移动云Token
        st.markdown("#### 📱 移动云")
        current_ecloud_token = config.get('ecloud_token', '')
        new_ecloud_token = st.text_input(
            "移动云Token",
            value=current_ecloud_token,
            type="password",
            key="ecloud_token_input",
            help="从浏览器Cookie中获取CMECLOUDTOKEN"
        )
        
        # 千帆Cookie
        st.markdown("#### 🔍 百度千帆")
        current_qianfan_cookie = config.get('qianfan_cookie', '')
        new_qianfan_cookie = st.text_area(
            "千帆Cookie",
            value=current_qianfan_cookie,
            height=100,
            key="qianfan_cookie_input",
            help="从浏览器Request Headers中复制完整Cookie"
        )
        
        if st.button("💾 保存配置"):
            config['ecloud_token'] = new_ecloud_token
            config['qianfan_cookie'] = new_qianfan_cookie
            save_config(config)
            st.success("配置已保存！")
        
        st.markdown("---")
        st.markdown("### 📖 使用说明")
        with st.expander("移动云Token获取方法"):
            st.markdown("""
            1. 登录移动云控制台
            2. F12打开开发者工具
            3. Network标签找任意请求
            4. 复制Cookie中的CMECLOUDTOKEN
            5. 粘贴到上方输入框并保存
            """)
        
        with st.expander("千帆Cookie获取方法"):
            st.markdown("""
            1. 登录千帆控制台
            2. F12打开开发者工具
            3. Network标签找resourceList请求
            4. 点击请求，查看Request Headers
            5. 复制完整的Cookie值
            6. 粘贴到上方输入框并保存
            """)
    
    # 主区域 - 总刷新按钮
    if st.button("🔄 刷新全部", use_container_width=True):
        st.session_state.ecloud_data = None
        st.session_state.qianfan_data = None
        st.rerun()
    
    # 初始化session_state
    if 'ecloud_data' not in st.session_state:
        st.session_state.ecloud_data = None
    if 'qianfan_data' not in st.session_state:
        st.session_state.qianfan_data = None
    
    # 初始化摘要
    ecloud_summary = None
    qianfan_summary = None
    
    # 查询移动云数据
    if st.session_state.ecloud_data is None:
        with st.spinner("查询移动云..."):
            data, error = query_ecloud_usage()
            st.session_state.ecloud_data = {'data': data, 'error': error}
    
    ecloud_data = st.session_state.ecloud_data['data']
    ecloud_error = st.session_state.ecloud_data['error']
    
    # 提取移动云摘要
    if not ecloud_error and ecloud_data and ecloud_data.get('dataRows'):
        for row in ecloud_data['dataRows']:
            if row.get('ordered'):
                expire_time = row.get('expireTime', '')
                days_to_expire = 999
                if expire_time:
                    expire_dt = datetime.strptime(expire_time, "%Y-%m-%d %H:%M:%S")
                    days_to_expire = (expire_dt - datetime.now()).days
                
                ecloud_summary = {
                    'five_hour_used': row.get('dayUsedCount', 0),
                    'five_hour_total': row.get('dayInitCount', 0),
                    'week_used': row.get('weekUsedCount', 0),
                    'week_total': row.get('weekInitCount', 0),
                    'month_used': row.get('monthUsedCount', 0),
                    'month_total': row.get('monthInitCount', 0),
                    'days_to_expire': days_to_expire,
                    'plan_name': row.get('chaGroupName', '未知套餐')
                }
                break
    
    # 查询千帆数据
    if st.session_state.qianfan_data is None:
        with st.spinner("查询千帆..."):
            result, error = query_qianfan_usage()
            st.session_state.qianfan_data = {'data': result, 'error': error}
    
    qianfan_data = st.session_state.qianfan_data['data']
    qianfan_error = st.session_state.qianfan_data['error']
    
    # 提取千帆摘要
    if not qianfan_error and qianfan_data and qianfan_data.get('items'):
        for item in qianfan_data['items']:
            quota = item.get('quota', {})
            expire_time = item.get('expiresAt', '')
            days_to_expire = 999
            if expire_time:
                expire_dt = datetime.fromisoformat(expire_time.replace('+08:00', ''))
                days_to_expire = (expire_dt - datetime.now()).days
            
            qianfan_summary = {
                'five_hour_used': quota.get('fiveHour', {}).get('used', 0),
                'five_hour_total': quota.get('fiveHour', {}).get('limit', 0),
                'week_used': quota.get('week', {}).get('used', 0),
                'week_total': quota.get('week', {}).get('limit', 0),
                'month_used': quota.get('month', {}).get('used', 0),
                'month_total': quota.get('month', {}).get('limit', 0),
                'days_to_expire': days_to_expire,
                'plan_name': item.get('planType', '未知套餐')
            }
            break
    
    # 显示建议区
    suggestions = generate_suggestions(ecloud_summary, qianfan_summary)
    if suggestions:
        st.markdown("### 💡 使用建议")
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")
        st.markdown("---")
    
    # 并排显示两个平台
    col_ecloud, col_qianfan = st.columns(2)
    
    # 移动云数据
    with col_ecloud:
        # 标题行（紧凑：平台名 + 套餐 + 状态 + 到期 + 刷新按钮）
        if not ecloud_error and ecloud_data and ecloud_data.get('dataRows'):
            for row in ecloud_data['dataRows']:
                if row.get('ordered'):
                    plan_name = row.get('chaGroupName', '未知套餐')
                    status = row.get('resourceStatus', '未知')
                    
                    expire_time = row.get('expireTime', '')
                    expire_info = ""
                    if expire_time:
                        expire_dt = datetime.strptime(expire_time, "%Y-%m-%d %H:%M:%S")
                        days_left = (expire_dt - datetime.now()).days
                        expire_info = f"{days_left}天后到期" if days_left > 0 else "已过期"
                    
                    st.markdown(f"## 📱 移动云 · {plan_name} · {status} · {expire_info}")
                    break
        else:
            st.markdown("## 📱 移动云")
        
        if st.button("🔄 刷新", key="refresh_ecloud"):
            st.session_state.ecloud_data = None
            st.rerun()
        
        if ecloud_error:
            st.error(f"❌ {ecloud_error}")
            st.info("请在左侧设置移动云Token")
        elif not ecloud_data or not ecloud_data.get('dataRows'):
            st.warning("暂无数据")
        else:
            # 显示数据（紧凑表格形式）
            for row in ecloud_data['dataRows']:
                if not row.get('ordered'):
                    continue
                
                # 使用量表格
                day_used = row.get('dayUsedCount', 0)
                day_total = row.get('dayInitCount', 0)
                week_used = row.get('weekUsedCount', 0)
                week_total = row.get('weekInitCount', 0)
                month_used = row.get('monthUsedCount', 0)
                month_total = row.get('monthInitCount', 0)
                
                # 每个时间维度独立显示（横向布局）
                # 近5小时
                if day_total > 0:
                    st.markdown("**近 5 小时**")
                    st.markdown(f"**{day_used/day_total*100:.1f}%**")
                    st.progress(day_used/day_total)
                    st.caption(f"{day_used:,}/{day_total:,}")
                
                # 近1周
                if week_total > 0:
                    st.markdown("**近 1 周**")
                    st.markdown(f"**{week_used/week_total*100:.1f}%**")
                    st.progress(week_used/week_total)
                    st.caption(f"{week_used:,}/{week_total:,}")
                
                # 近1月
                if month_total > 0:
                    st.markdown("**近 1 月**")
                    st.markdown(f"**{month_used/month_total*100:.1f}%**")
                    st.progress(month_used/month_total)
                    st.caption(f"{month_used:,}/{month_total:,}")
    
    # 千帆数据
    with col_qianfan:
        # 标题行（紧凑：平台名 + 套餐 + 状态 + 到期 + 刷新按钮）
        if not qianfan_error and qianfan_data and qianfan_data.get('items'):
            item = qianfan_data['items'][0]
            plan_name = item.get('planType', '未知套餐')
            status = item.get('resourceStatus', '未知')
            
            expire_time = item.get('expiresAt', '')
            expire_info = ""
            if expire_time:
                expire_dt = datetime.fromisoformat(expire_time.replace('+08:00', ''))
                days_left = (expire_dt - datetime.now()).days
                expire_info = f"{days_left}天后到期" if days_left > 0 else "已过期"
            
            st.markdown(f"## 🔍 百度千帆 · {plan_name} · {status} · {expire_info}")
        else:
            st.markdown("## 🔍 百度千帆")
        
        if st.button("🔄 刷新", key="refresh_qianfan"):
            st.session_state.qianfan_data = None
            st.rerun()
        
        if qianfan_error:
            st.error(f"❌ {qianfan_error}")
            st.info("请在左侧设置千帆Cookie")
        elif not qianfan_data or not qianfan_data.get('items'):
            st.warning("暂无数据")
        else:
            # 显示数据（紧凑表格形式）
            for item in qianfan_data['items']:
                # 使用量
                quota = item.get('quota', {})
                five_hour_used = quota.get('fiveHour', {}).get('used', 0)
                five_hour_total = quota.get('fiveHour', {}).get('limit', 0)
                five_hour_reset = quota.get('fiveHour', {}).get('resetAt', '')
                week_used = quota.get('week', {}).get('used', 0)
                week_total = quota.get('week', {}).get('limit', 0)
                week_reset = quota.get('week', {}).get('resetAt', '')
                month_used = quota.get('month', {}).get('used', 0)
                month_total = quota.get('month', {}).get('limit', 0)
                month_reset = quota.get('month', {}).get('resetAt', '')
                
                # 每个时间维度独立显示（横向布局）
                # 近5小时
                if five_hour_total > 0:
                    st.markdown("**近 5 小时**")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**{five_hour_used/five_hour_total*100:.1f}%**")
                    with c2:
                        if five_hour_reset:
                            reset_dt = datetime.fromisoformat(five_hour_reset.replace('+08:00', ''))
                            st.caption(f"重置时间：{reset_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.progress(five_hour_used/five_hour_total)
                    st.caption(f"{five_hour_used:,}/{five_hour_total:,}")
                
                # 近1周
                if week_total > 0:
                    st.markdown("**近 1 周**")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**{week_used/week_total*100:.1f}%**")
                    with c2:
                        if week_reset:
                            reset_dt = datetime.fromisoformat(week_reset.replace('+08:00', ''))
                            st.caption(f"重置时间：{reset_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.progress(week_used/week_total)
                    st.caption(f"{week_used:,}/{week_total:,}")
                
                # 近1月
                if month_total > 0:
                    st.markdown("**近 1 月**")
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.markdown(f"**{month_used/month_total*100:.1f}%**")
                    with c2:
                        if month_reset:
                            reset_dt = datetime.fromisoformat(month_reset.replace('+08:00', ''))
                            st.caption(f"重置时间：{reset_dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.progress(month_used/month_total)
                    st.caption(f"{month_used:,}/{month_total:,}")

if __name__ == "__main__":
    main()
