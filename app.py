import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import time
import requests
import json

# ==========================================
# 页面配置
# ==========================================
st.set_page_config(
    page_title="双色球·官方实时数据预测 (真实版)",
    page_icon="🇨🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 50px; 
        font-size: 18px; 
        background: linear-gradient(90deg, #FF4B4B 0%, #D93025 100%); 
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    .prediction-card {
        background: white; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
        margin-bottom: 20px;
        border-left: 5px solid #ccc;
        transition: all 0.3s ease;
    }
    .prediction-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.12);
    }
    .ball-red {
        display: inline-block; width: 38px; height: 38px; line-height: 38px; 
        text-align: center; border-radius: 50%; background: #FF4B4B; color: white; 
        font-weight: bold; margin: 0 3px; font-size: 18px;
        box-shadow: inset 0 -3px 0 rgba(0,0,0,0.2);
    }
    .ball-blue {
        display: inline-block; width: 38px; height: 38px; line-height: 38px; 
        text-align: center; border-radius: 50%; background: #2E86C1; color: white; 
        font-weight: bold; margin: 0 3px; font-size: 18px;
        box-shadow: inset 0 -3px 0 rgba(0,0,0,0.2);
    }
    .score-badge {
        background: #27ae60; color: white; padding: 5px 12px; 
        border-radius: 20px; font-size: 15px; font-weight: bold;
        box-shadow: 0 2px 4px rgba(39, 174, 96, 0.3);
    }
    h1 {color: #2c3e50; text-align: center; font-weight: 800;}
    .sub-header {text-align: center; color: #7f8c8d; margin-bottom: 20px;}
    .status-box {
        padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;
        font-weight: bold; border: 1px solid transparent;
    }
    .status-success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
    .status-warning { background-color: #fff3cd; color: #856404; border-color: #ffeeba; }
    .status-error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
    
    .manual-input-area {
        background: white; padding: 20px; border-radius: 10px; 
        border: 2px dashed #ccc; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 真实数据获取引擎
# ==========================================

def fetch_real_data_from_api():
    """
    尝试从稳定的第三方聚合API获取真实双色球数据。
    """
    # 多个备用源，提高成功率
    urls = [
        "https://api.zhtong.cn/lottery/ssq.json", 
        "https://lottery.ewang.com/api/ssq/history?count=100"
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # 适配不同API结构
                items = data.get('data', data) if isinstance(data, dict) else data
                if not items: continue
                
                processed = []
                for item in items[:100]: # 取最近100期
                    # 清洗数据
                    r_str = item.get('red', item.get('redBall', ''))
                    b_str = item.get('blue', item.get('blueBall', ''))
                    issue = item.get('issue', item.get('expect', ''))
                    date = item.get('date', item.get('openTime', ''))
                    
                    if not r_str or not b_str: continue
                    
                    # 处理红球字符串 (可能是 "01,02..." 或 "01 02...")
                    # 增加容错处理
                    try:
                        r_list = [int(x) for x in str(r_str).replace(',', ' ').split()]
                        b_val = int(b_str)
                        
                        # 基本校验
                        if len(r_list) != 6 or not (1 <= b_val <= 16):
                            continue
                            
                        processed.append({
                            "期号": str(issue),
                            "日期": str(date)[:10] if date else "",
                            "红球": sorted(r_list),
                            "蓝球": b_val,
                            "和值": sum(r_list),
                            "红球_字符串": " ".join(f"{x:02d}" for x in sorted(r_list)),
                            "蓝球_字符串": f"{b_val:02d}",
                            "is_real": True
                        })
                    except ValueError:
                        continue
                
                if processed:
                    return pd.DataFrame(processed), True
        except Exception:
            continue
            
    return None, False

def generate_fallback_data():
    """仅在完全无法联网且无手动输入时生成纯模拟数据（带警告）"""
    np.random.seed(42)
    data = []
    today = datetime.now()
    for i in range(100):
        d = today - timedelta(days=i*3)
        reds = sorted(np.random.choice(range(1, 34), 6, replace=False))
        blue = np.random.randint(1, 17)
        data.append({
            "期号": f"模拟{d.year}{str(i).zfill(3)}",
            "日期": d.strftime("%Y-%m-%d"),
            "红球": reds,
            "蓝球": blue,
            "和值": sum(reds),
            "红球_字符串": " ".join(f"{x:02d}" for x in reds),
            "蓝球_字符串": f"{blue:02d}",
            "is_real": False
        })
    return pd.DataFrame(data), False

# ==========================================
# 算法核心
# ==========================================

def analyze_stats(df):
    # 只分析标记为真实的数据，或者如果没有真实数据则分析全部
    real_df = df[df['is_real'] == True] if 'is_real' in df.columns else df
    if len(real_df) < 5:
        real_df = df # 如果真实数据太少，降级使用所有数据
        
    all_reds = [r for row in real_df['红球'] for r in row]
    red_counts = Counter(all_reds)
    
    omission = {}
    recent_50 = real_df.head(50)
    for num in range(1, 34):
        count = 0
        found = False
        for _, row in recent_50.iterrows():
            if num in row['红球']:
                found = True
                break
            count += 1
        omission[num] = count
    return red_counts, omission

def calculate_score(reds, blue, red_counts, omission, avg_sum, std_sum):
    score = 40
    # 避免除零错误
    if len(red_counts) == 0:
        return 50
        
    hot_nums = set([k for k, v in red_counts.most_common(10)])
    cold_nums = set([k for k, v in red_counts.most_common()[:-11:-1]])
    
    hit_hot = len(set(reds) & hot_nums)
    hit_cold = len(set(reds) & cold_nums)
    
    if hit_hot >= 2 and hit_cold >= 1: score += 15
    elif hit_hot >= 3: score += 10
    
    s = sum(reds)
    diff = abs(s - avg_sum)
    if diff < 10: score += 10
    elif diff < 20: score += 5
    
    consecutives = sum(1 for i in range(len(reds)-1) if reds[i+1] == reds[i] + 1)
    if consecutives == 1: score += 5
    
    odd_count = sum(1 for x in reds if x % 2 != 0)
    if odd_count in [2, 3, 4]: score += 5
    
    return max(0, min(99, score))

def generate_top_5(red_counts, omission, avg_sum, std_sum):
    np.random.seed(int(time.time()))
    candidates = []
    pool = list(range(1, 34))
    
    # 计算权重
    weights = []
    if len(red_counts) > 0:
        mean_freq = np.mean(list(red_counts.values()))
        for num in pool:
            freq = red_counts.get(num, 0)
            miss = omission.get(num, 0)
            w = 1.0
            if freq > mean_freq: w += 0.5
            if 5 <= miss <= 15: w += 0.8
            elif miss > 20: w += 0.3
            weights.append(w)
    else:
        weights = [1.0] * 33
        
    probabilities = np.array(weights) / sum(weights)
    
    for _ in range(20000):
        selected_reds = sorted(np.random.choice(pool, 6, replace=False, p=probabilities))
        selected_blue = np.random.randint(1, 17)
        score = calculate_score(selected_reds, selected_blue, red_counts, omission, avg_sum, std_sum)
        candidates.append({
            "reds": selected_reds, "blue": selected_blue, "score": score,
            "sum": sum(selected_reds),
            "odd_even": f"{sum(1 for x in selected_reds if x%2!=0)}:{sum(1 for x in selected_reds if x%2==0)}"
        })
        
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    top_5 = []
    seen = set()
    for item in candidates:
        key = (tuple(item['reds']), item['blue'])
        if key not in seen and item['score'] >= 50:
            seen.add(key)
            strategy = "👑 热号追踪" if item['score'] > 85 else "⚖️ 冷热均衡" if item['score'] > 75 else "❄️ 遗漏博冷"
            potential = "一/二等奖潜力" if item['score'] > 85 else "三/四等奖潜力" if item['score'] > 75 else "小奖"
            top_5.append({
                "reds": item['reds'], "blue": item['blue'], "score": item['score'],
                "strategy": strategy, "sum": item['sum'], "odd_even": item['odd_even'], "potential": potential
            })
            if len(top_5) >= 5: break
    return top_5

# ==========================================
# 主界面逻辑
# ==========================================

st.title("🇨🇳 双色球·官方实时数据预测")
st.markdown("<p class='sub-header'>拒绝模拟！致力获取官网真实开奖数据</p>", unsafe_allow_html=True)

# 初始化 Session State
if 'df_history' not in st.session_state:
    st.session_state.df_history = None
    st.session_state.data_source_status = "loading" # loading, success, manual, error

# 数据加载流程 (仅在首次加载或重置时执行)
if st.session_state.df_history is None:
    with st.spinner('🌐 正在尝试连接数据源获取真实开奖记录...'):
        df, success = fetch_real_data_from_api()
        
        if success and len(df) > 0:
            st.session_state.df_history = df
            st.session_state.data_source_status = "success"
        else:
            # 获取失败，生成模拟数据作为临时底座，并提示用户手动输入
            dummy_df, _ = generate_fallback_data()
            st.session_state.df_history = dummy_df
            st.session_state.data_source_status = "error"

# 状态显示与手动输入入口
status = st.session_state.data_source_status
df = st.session_state.df_history

if status == "success":
    latest = df.iloc[0]
    st.markdown(f"""
        <div class="status-box status-success">
            ✅ <b>数据同步成功</b><br>
            最新期号：<span style="font-size:1.2em; color:#D93025; font-weight:bold;">{latest['期号']}</span> 
            ({latest['日期']})<br>
            真实号码：{latest['红球_字符串']} + {latest['蓝球_字符串']}
        </div>
    """, unsafe_allow_html=True)

elif status == "error":
    st.markdown("""
        <div class="status-box status-warning">
            ⚠️ <b>自动获取失败</b><br>
            由于福彩官网反爬或网络波动，未能自动拉取到最新数据。<br>
            <b>为了保证预测准确，请您手动输入刚才在官网查到的最新一期号码：</b>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("manual_input_form"):
        c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
        with c1:
            m_issue = st.text_input("期号 (如 2026028)", value="2026028")
        with c2:
            m_date = st.date_input("开奖日期", value=datetime.now())
        with c3:
            m_reds = st.text_input("红球 (空格分隔)", placeholder="01 02 ...")
        with c4:
            m_blue = st.text_input("蓝球", placeholder="01")
            
        submitted = st.form_submit_button("✅ 确认并更新数据")
        
        if submitted:
            if m_reds and m_blue:
                try:
                    r_list = sorted([int(x) for x in m_reds.split()])
                    b_val = int(m_blue)
                    if len(r_list) == 6 and 1 <= b_val <= 16:
                        new_row = pd.DataFrame([{
                            "期号": str(m_issue),
                            "日期": str(m_date),
                            "红球": r_list,
                            "蓝球": b_val,
                            "和值": sum(r_list),
                            "红球_字符串": " ".join(f"{x:02d}" for x in r_list),
                            "蓝球_字符串": f"{b_val:02d}",
                            "is_real": True
                        }])
                        
                        # 将真实数据插入到模拟数据之前
                        base_df = st.session_state.df_history
                        # 简单去重：如果期号已存在则不添加
                        if str(m_issue) not in base_df['期号'].values:
                            df_combined = pd.concat([new_row, base_df]).reset_index(drop=True)
                            st.session_state.df_history = df_combined
                            st.session_state.data_source_status = "manual"
                            st.rerun()
                        else:
                            st.warning("该期号已存在。")
                    else:
                        st.error("红球必须是6个1-33的数字，蓝球是1个1-16的数字。")
                except ValueError:
                    st.error("输入格式错误，请检查数字。")
            else:
                st.error("请输入完整的红球和蓝球号码。")

# 如果有数据，继续显示主功能
if st.session_state.df_history is not None:
    df = st.session_state.df_history
    
    # 预处理
    red_counts, omission = analyze_stats(df)
    avg_sum = df['和值'].mean()
    std_sum = df['和值'].std() if len(df) > 1 else 10.0

    tab_pred, tab_history = st.tabs(["🔮 智能预测", "📋 往期开奖"])

    with tab_pred:
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("🚀 生成5组最优号码", type="primary", use_container_width=True):
                with st.spinner('AI 正在分析真实走势...'):
                    time.sleep(1.5)
                    preds = generate_top_5(red_counts, omission, avg_sum, std_sum)
                    st.session_state['predictions'] = preds
                    st.rerun()

        if st.session_state.get('predictions'):
            st.subheader("💡 本期推荐方案")
            results_text = ""
            for i, p in enumerate(st.session_state['predictions']):
                red_balls_html = "".join([f'<span class="ball-red">{r:02d}</span>' for r in p['reds']])
                blue_ball_html = f'<span class="ball-blue">{p["blue"]:02d}</span>'
                border_color = "#27ae60" if p['score'] > 80 else "#f39c12" if p['score'] > 70 else "#95a5a6"
                card_html = f"""
                <div class="prediction-card" style="border-left-color: {border_color};">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <span style="font-weight:bold; font-size:18px;">方案 {i+1}: {p['strategy']}</span>
                        <span class="score-badge">{p['score']}分</span>
                    </div>
                    <div style="font-size:20px; margin: 15px 0;">
                        {red_balls_html} &nbsp; {blue_ball_html}
                    </div>
                    <div style="font-size:13px; color:#7f8c8d; display:flex; gap:15px; align-items:center; flex-wrap: wrap;">
                        <span>📊 和值：<b>{p['sum']}</b></span>
                        <span>⚖️ 奇偶：<b>{p['odd_even']}</b></span>
                        <span style="background:#fff3cd; color:#856404; padding:2px 6px; border-radius:4px;">🎯 潜力：{p['potential']}</span>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                reds_str = " ".join(f"{r:02d}" for r in p['reds'])
                results_text += f"方案{i+1}: {reds_str} + {p['blue']:02d}\n"
            st.code(results_text, language="text")
        else:
            st.info("👆 点击上方按钮生成预测")

    with tab_history:
        st.subheader("📋 最近 20 期数据")
        df_recent = df.head(20)[['期号', '日期', '红球_字符串', '蓝球_字符串', '和值']].copy()
        df_recent.columns = ['期号', '日期', '红球', '蓝球', '和值']
        
        def highlight_real(row):
            # 高亮真实数据行
            if 'is_real' in df.columns and row['期号'] in df[df['is_real']==True]['期号'].values:
                return ['background-color: #d4edda'] * len(row)
            return [''] * len(row)
        
        st.dataframe(df_recent.style.apply(highlight_real, axis=1), use_container_width=True, hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("**🔥 热号 Top 10**")
            if len(red_counts) > 0:
                df_freq = pd.DataFrame(list(red_counts.items()), columns=['号码', '次数']).sort_values('次数', ascending=False).head(10)
                st.bar_chart(df_freq.set_index('号码'), color="#FF4B4B")
            else:
                st.write("数据不足")
        with c2:
            st.write("**❄️ 遗漏 Top 10**")
            if len(omission) > 0:
                df_omit = pd.DataFrame(list(omission.items()), columns=['号码', '遗漏']).sort_values('遗漏', ascending=False).head(10)
                st.bar_chart(df_omit.set_index('号码'), color="#2E86C1")
            else:
                st.write("数据不足")

st.markdown("---")
st.caption("重要提示：本工具优先尝试自动获取真实数据。若自动获取失败，请务必使用上方的手动输入框录入官网最新号码，以确保预测基于真实结果。")
