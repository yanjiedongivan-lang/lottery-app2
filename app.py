import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import time
import random

# ==========================================
# 页面配置 (保持原样)
# ==========================================
st.set_page_config(
    page_title="双色球2026智能预测系统",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS (保持原样)
st.markdown("""
    <style>
    .main {background-color: #f0f2f6;}
    .stButton > button {width: 100%; border-radius: 8px; font-weight: bold; height: 50px; font-size: 18px; background-color: #FF4B4B; color: white;}
    .prediction-card {
        background: white; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
        margin-bottom: 20px;
        border-left: 5px solid #ccc;
    }
    .ball-red {
        display: inline-block; width: 38px; height: 38px; line-height: 38px; 
        text-align: center; border-radius: 50%; background: #FF4B4B; color: white; 
        font-weight: bold; margin: 0 3px; font-size: 18px;
    }
    .ball-blue {
        display: inline-block; width: 38px; height: 38px; line-height: 38px; 
        text-align: center; border-radius: 50%; background: #2E86C1; color: white; 
        font-weight: bold; margin: 0 3px; font-size: 18px;
    }
    .score-badge {
        background: #27ae60; color: white; padding: 5px 12px; 
        border-radius: 20px; font-size: 15px; font-weight: bold;
    }
    .rule-tag {
        background: #e8f4fd; color: #2980b9; padding: 3px 8px; 
        border-radius: 4px; font-size: 12px; margin-left: 5px;
    }
    h1 {color: #2c3e50; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 数据与算法核心
# ==========================================
@st.cache_data(ttl=3600)
def fetch_and_analyze():
    """生成并分析模拟的500期历史数据 (保持原样)"""
    # 【修改点1】固定种子，确保历史数据源稳定
    np.random.seed(2026) 
    
    data = []
    today = datetime.now()
    
    for i in range(500):
        date = today - timedelta(days=i*3)
        target_sum = int(np.random.normal(102, 15))
        reds = sorted(np.random.choice(range(1, 34), 6, replace=False))
        while sum(reds) < 70 or sum(reds) > 140:
            reds = sorted(np.random.choice(range(1, 34), 6, replace=False))
        blue = np.random.randint(1, 17)
        data.append({
            "期号": f"{date.year}{str(i%150+1).zfill(3)}",
            "日期": date.strftime("%Y-%m-%d"),
            "红球": reds,
            "蓝球": blue,
            "和值": sum(reds),
            "红球_字符串": " ".join(f"{r:02d}" for r in reds),
            "蓝球_字符串": f"{blue:02d}"
        })
    
    df = pd.DataFrame(data)
    
    # 统计分析
    all_reds = [r for row in df['红球'] for r in row]
    red_counts = Counter(all_reds)
    
    # 计算遗漏
    omission = {}
    recent_50 = df.head(50)
    for num in range(1, 34):
        count = 0
        found = False
        for _, row in recent_50.iterrows():
            if num in row['红球']:
                found = True
                break
            count += 1
        omission[num] = count
        
    return df, red_counts, omission

def calculate_score_2026(reds, blue, red_counts, omission, avg_sum, std_sum):
    """评分逻辑保持原样"""
    score = 40
    
    hit_hot = len(set(reds) & set([k for k, v in red_counts.most_common(10)]))
    hit_cold = len(set(reds) & set([k for k, v in red_counts.most_common()[:-11:-1]]))
    
    if hit_hot >= 2 and hit_cold >= 1:
        score += 15
        
    s = sum(reds)
    diff = abs(s - avg_sum)
    if diff < 10: score += 10
    elif diff < 20: score += 5
    
    consecutives = sum(1 for i in range(len(reds)-1) if reds[i+1] == reds[i] + 1)
    if consecutives == 1: score += 5
    
    odd_count = sum(1 for x in reds if x % 2 != 0)
    if odd_count in [2, 3, 4]: score += 5
    
    if 3 <= hit_hot + hit_cold <= 5:
        score += 10
        
    return max(0, min(99, score))

def generate_top_5_fixed(red_counts, omission, avg_sum, std_sum):
    """
    【核心修改】
    不再随机生成5组，而是生成10000组，只取分数最高的前5组。
    使用固定种子，确保结果恒定。
    """
    # 【修改点2】固定种子，确保每次运行结果一致
    np.random.seed(20260317) 
    
    candidates = []
    pool = list(range(1, 34))
    
    # 预计算权重 (保持原有策略逻辑)
    weights = []
    for num in pool:
        freq = red_counts.get(num, 0)
        miss = omission.get(num, 0)
        w = 1.0
        # 混合策略权重
        if 5 <= miss <= 15: w = 2.5
        elif miss > 20: w = 1.2
        w += (freq * 0.1)
        weights.append(w)
    
    probabilities = np.array(weights) / sum(weights)
    
    # 模拟生成 10,000 组候选
    for _ in range(10000):
        selected_reds = sorted(np.random.choice(pool, 6, replace=False, p=probabilities))
        selected_blue = np.random.randint(1, 17)
        
        score = calculate_score_2026(selected_reds, selected_blue, red_counts, omission, avg_sum, std_sum)
        
        candidates.append({
            "reds": selected_reds,
            "blue": selected_blue,
            "score": score,
            "sum": sum(selected_reds),
            "odd_even": f"{sum(1 for x in selected_reds if x%2!=0)}:{sum(1 for x in selected_reds if x%2==0)}"
        })
    
    # 排序取前5
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    top_5 = []
    seen = set()
    
    for item in candidates:
        key = (tuple(item['reds']), item['blue'])
        if key not in seen and item['score'] >= 55:
            seen.add(key)
            
            # 赋予策略名称 (保持原有风格)
            if item['score'] > 85: strategy = "平衡稳健 (冲福运)"
            elif item['score'] > 80: strategy = "热号追踪 (搏大奖)"
            elif item['score'] > 75: strategy = "冷号回补 (博反弹)"
            elif item['score'] > 70: strategy = "大号防守 (避拥挤)"
            else: strategy = "奇偶均衡"
            
            potential_prize = "六等奖 (5元)"
            if item['score'] > 85: potential_prize = "一等奖/二等奖 (浮动)"
            elif item['score'] > 75: potential_prize = "三/四等奖 (200-3000元)"
            elif item['score'] > 65: potential_prize = "福运奖/五等奖 (5-10元)"
            
            top_5.append({
                "reds": item['reds'],
                "blue": item['blue'],
                "score": item['score'],
                "strategy": strategy,
                "sum": item['sum'],
                "odd_even": item['odd_even'],
                "potential": potential_prize
            })
            
            if len(top_5) >= 5:
                break
                
    return top_5

# ==========================================
# 主界面逻辑 (保持原样)
# ==========================================

# 初始化数据
if 'data_loaded' not in st.session_state:
    with st.spinner('正在加载2026最新规则模型...'):
        df_history, red_counts, omission = fetch_and_analyze()
        st.session_state['data'] = (df_history, red_counts, omission)
        st.session_state['predictions'] = None
        st.session_state['data_loaded'] = True

df_history, red_counts, omission = st.session_state['data']
avg_sum = df_history['和值'].mean()
std_sum = df_history['和值'].std()

# 主标题
st.title("🎰 双色球2026智能预测系统")
st.markdown("<p style='text-align:center; color:#666;'>适配2月1日新规 | 新增福运奖检测 | 包含历史开奖查询</p>", unsafe_allow_html=True)

# 选项卡布局
tab_pred, tab_history = st.tabs(["🔮 智能预测", "📋 往期开奖"])

# --- Tab 1: 智能预测 ---
with tab_pred:
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🚀 生成5组新规优选号码", type="primary", use_container_width=True):
            with st.spinner('AI 正在计算福运奖概率...'):
                time.sleep(1.5)
                # 【修改点3】调用新的固定筛选函数
                preds = generate_top_5_fixed(red_counts, omission, avg_sum, std_sum)
                st.session_state['predictions'] = preds
                st.rerun()

    if st.session_state['predictions']:
        st.subheader("💡 本期推荐方案 (按推荐指数排序)")
        st.caption("✨ 注：此为基于10,000次模拟筛选出的最高分组合，结果已固定。")
        
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
                <div style="font-size:13px; color:#7f8c8d; display:flex; gap:15px; align-items:center;">
                    <span>和值：{p['sum']}</span>
                    <span>奇偶：{p['odd_even']}</span>
                    <span style="background:#fff3cd; color:#856404; padding:2px 6px; border-radius:4px;">🎯 潜力：{p['potential']}</span>
                </div>
                <div style="margin-top:8px; font-size:12px; color:#95a5a6;">
                    ℹ️ 新规提示：若中3红0蓝且奖池≥15亿，可中<span style="color:#27ae60; font-weight:bold;">福运奖</span>！
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            reds_str = " ".join(f"{r:02d}" for r in p['reds'])
            results_text += f"方案{i+1} ({p['strategy']}): {reds_str} + {p['blue']:02d} [潜力:{p['potential']}]\n"

        st.code(results_text, language="text")
        st.caption("💡 长按代码块可复制所有号码。")

    else:
        st.info("👆 点击上方按钮开始生成预测")

# --- Tab 2: 往期开奖 (保持原样) ---
with tab_history:
    st.subheader("📋 最近 20 期开奖数据")
    st.caption("数据基于模拟生成，仅用于功能展示。实际使用时应接入真实API。")
    
    # 显示最近20期
    df_recent = df_history.head(20)[['期号', '日期', '红球_字符串', '蓝球_字符串', '和值']].copy()
    df_recent.columns = ['期号', '日期', '红球', '蓝球', '和值']
    st.dataframe(df_recent, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # 统计图表
    col1, col2 = st.columns(2)
    with col1:
        st.write("**🔥 红球历史频次 Top 10**")
        all_reds_flat = [r for row in df_history['红球'] for r in row]
        red_freq = Counter(all_reds_flat)
        df_freq = pd.DataFrame(list(red_freq.items()), columns=['号码', '出现次数']).sort_values('出现次数', ascending=False).head(10)
        st.bar_chart(df_freq.set_index('号码'))
    with col2:
        st.write("**❄️ 红球当前遗漏值 Top 10**")
        df_omit = pd.DataFrame(list(omission.items()), columns=['号码', '遗漏期数']).sort_values('遗漏期数', ascending=False).head(10)
        st.bar_chart(df_omit.set_index('号码'))

# 底部声明
st.markdown("---")
st.caption("免责声明：彩票具有随机性，本系统基于2026年最新规则和历史数据统计规律生成，仅供参考娱乐，不保证中奖。请理性购彩。")
