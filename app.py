import streamlit as st
import random
import datetime
import pandas as pd
from collections import Counter
import time

# ==========================================
# 页面配置 (让它看起来像 APP)
# ==========================================
st.set_page_config(
    page_title="福利彩票智能助手",
    page_icon="🎰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS，优化手机端显示
st.markdown("""
    <style>
    .main > div {padding-top: 2rem;}
    .stButton > button {width: 100%; background-color: #FF4B4B; color: white;}
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 核心逻辑类 (保持原有逻辑，适配 Streamlit)
# ==========================================
class LotterySystem:
    def __init__(self):
        self.history_data = []
        self.load_history_data()

    def load_history_data(self):
        """生成模拟数据 (实际可替换为 API)"""
        if not self.history_data:
            today = datetime.date.today()
            for i in range(100): # 生成100期数据用于分析
                date = today - datetime.timedelta(days=(i * 3))
                red_balls = sorted(random.sample(range(1, 34), 6))
                blue_ball = random.randint(1, 16)
                self.history_data.append({
                    "issue": f"2026{i+1:03d}",
                    "date": date.strftime("%Y-%m-%d"),
                    "red_balls": red_balls,
                    "blue_ball": blue_ball
                })

    def get_latest_results(self, count=5):
        return self.history_data[:count]

    def analyze_trend(self):
        all_reds = []
        all_blues = []
        for item in self.history_data:
            all_reds.extend(item['red_balls'])
            all_blues.append(item['blue_ball'])
        
        red_counter = Counter(all_reds)
        blue_counter = Counter(all_blues)
        
        # 转换为 DataFrame 方便绘图
        red_df = pd.DataFrame(list(red_counter.items()), columns=['Number', 'Count']).sort_values('Number')
        blue_df = pd.DataFrame(list(blue_counter.items()), columns=['Number', 'Count']).sort_values('Number')
        
        hot_reds = [num for num, count in red_counter.most_common(5)]
        cold_reds = [num for num, count in red_counter.most_common()[:-6:-1]]
        
        return red_df, blue_df, hot_reds, cold_reds

    def predict_numbers(self, strategy):
        stats = self.analyze_trend()
        hot_reds, cold_reds = stats[2], stats[3]
        
        selected_reds = set()
        
        if strategy == "平衡策略":
            # 2热 + 2冷 + 2随机
            pool = hot_reds[:2] + cold_reds[:2]
            while len(pool) < 10: pool.append(random.randint(1, 33))
            selected_reds = set(random.sample(pool, 6))
            while len(selected_reds) < 6: selected_reds.add(random.randint(1, 33))
        elif strategy == "追热策略":
            pool = hot_reds + list(range(1, 34))
            selected_reds = set(random.sample(pool, 6))
        elif strategy == "博冷策略":
            pool = cold_reds + list(range(1, 34))
            selected_reds = set(random.sample(pool, 6))
        else: # 纯随机
            selected_reds = set(random.sample(range(1, 34), 6))
            
        final_reds = sorted(list(selected_reds))[:6]
        selected_blue = random.randint(1, 16)
        
        return final_reds, selected_blue

# ==========================================
# 界面布局
# ==========================================
system = LotterySystem()

st.title("🎰 福利彩票智能助手")
st.caption("2026 版 | 数据仅供参考，理性购彩")

# 侧边栏或顶部导航 (使用 Tabs)
tab1, tab2, tab3 = st.tabs(["📊 走势分析", "🔮 智能预测", "📜 往期查询"])

# --- Tab 1: 走势分析 ---
with tab1:
    st.header("号码走势统计")
    red_df, blue_df, hot_reds, cold_reds = system.analyze_trend()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔥 最热红球", ", ".join(map(str, hot_reds)))
        st.bar_chart(red_df.set_index('Number'), color="#FF4B4B")
    with col2:
        st.metric("❄️ 最冷红球", ", ".join(map(str, cold_reds)))
        st.bar_chart(blue_df.set_index('Number'), color="#4B7BFF")
    
    st.info("💡 提示：热号代表近期出现频繁，冷号代表长期未出。")

# --- Tab 2: 智能预测 ---
with tab2:
    st.header("AI 智能选号")
    strategy = st.selectbox(
        "选择预测策略",
        ["平衡策略", "追热策略", "博冷策略", "纯随机策略"],
        help="平衡策略：结合冷热号与随机号，推荐首选"
    )
    
    if st.button("🚀 立即生成幸运号码", type="primary"):
        with st.spinner("正在分析历史数据..."):
            time.sleep(0.8) # 模拟计算过程
            reds, blue = system.predict_numbers(strategy)
            
            st.success("生成成功！")
            
            # 展示号码球效果
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write("❤️ 红球推荐:")
                cols = st.columns(6)
                for i, num in enumerate(reds):
                    cols[i].markdown(f"<div style='background-color:#FF4B4B;color:white;border-radius:50%;width:40px;height:40px;line-height:40px;text-align:center;font-weight:bold;margin:auto;'>{num:02d}</div>", unsafe_allow_html=True)
            with c2:
                st.write("💙 蓝球推荐:")
                st.markdown(f"<div style='background-color:#4B7BFF;color:white;border-radius:50%;width:40px;height:40px;line-height:40px;text-align:center;font-weight:bold;margin:auto;'>{blue:02d}</div>", unsafe_allow_html=True)
            
            st.warning("⚠️ 彩票是随机事件，本结果仅供娱乐参考，切勿沉迷！")

# --- Tab 3: 往期查询 ---
with tab3:
    st.header("最近开奖记录")
    data = system.get_latest_results(10)
    
    # 格式化数据用于表格显示
    df_list = []
    for item in data:
        red_str = " ".join(f"{n:02d}" for n in item['red_balls'])
        df_list.append({
            "期号": item['issue'],
            "日期": item['date'],
            "红球": red_str,
            "蓝球": f"{item['blue_ball']:02d}"
        })
    
    df = pd.DataFrame(df_list)
    st.table(df)

# 底部版权
st.markdown("---")
st.markdown("<center><small>Powered by AI & Streamlit | 2026</small></center>", unsafe_allow_html=True)
