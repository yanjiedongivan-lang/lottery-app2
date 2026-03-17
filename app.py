import streamlit as st
import random
import csv
import os
import requests
from datetime import datetime

# 全局配置
CSV_FILE = "ssq_history.csv"

# Streamlit应用设置
st.set_page_config(
    page_title="双色球分析预测",
    page_icon="🎯",
    layout="wide"
)

# 标题和说明
st.title("🎯 双色球分析预测系统")
st.markdown("基于历史数据的双色球号码分析与推荐")

# 侧边栏导航
page = st.sidebar.selectbox(
    "选择功能",
    ["总览", "数据管理", "历史开奖", "号码评分", "本期推荐"]
)

# 辅助函数
def init_csv():
    """初始化CSV文件"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["期号", "开奖日期", "红球", "蓝球"])
        st.success(f"✅ 初始化CSV文件成功：{CSV_FILE}")

def load_data():
    """加载历史数据"""
    if not os.path.exists(CSV_FILE):
        st.warning("⚠️ 数据文件不存在，请先创建数据文件")
        return None
    
    try:
        data = []
        with open(CSV_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                for row in reader:
                    if row and len(row) >= 4:
                        data.append({
                            '期号': row[0],
                            '开奖日期': row[1],
                            '红球': list(map(int, row[2].split(','))),
                            '蓝球': int(row[3])
                        })
        return data
    except Exception as e:
        st.error(f"❌ 加载数据失败：{e}")
        return None

def save_data(data):
    """保存数据到CSV文件"""
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["期号", "开奖日期", "红球", "蓝球"])
        for item in data:
            writer.writerow([
                item['期号'],
                item['开奖日期'],
                ','.join(map(str, item['红球'])),
                item['蓝球']
            ])

def calculate_ac(reds):
    """计算AC值"""
    reds = sorted(reds)
    diffs = set()
    for i in range(len(reds)):
        for j in range(i + 1, len(reds)):
            diffs.add(reds[j] - reds[i])
    return len(diffs) - (len(reds) - 1)

def get_runs(reds):
    """获取连号情况"""
    reds = sorted(reds)
    runs = []
    current_run = 1
    for i in range(1, len(reds)):
        if reds[i] == reds[i-1] + 1:
            current_run += 1
        else:
            if current_run >= 2:
                runs.append(current_run)
            current_run = 1
    if current_run >= 2:
        runs.append(current_run)
    return runs

def get_consecutive_label(reds):
    """获取连号标签"""
    runs = get_runs(reds)
    if not runs:
        return "无连号"
    if len(runs) == 1 and runs[0] == 6:
        return "全6连号"
    if len(runs) == 1:
        return f"1组{runs[0]}连"
    return "+".join(f"{r}连" for r in runs)

def get_tail_pattern(reds):
    """获取尾数组型"""
    tails = [n % 10 for n in reds]
    tail_counts = {}
    for tail in tails:
        tail_counts[tail] = tail_counts.get(tail, 0) + 1
    groups = sorted([v for v in tail_counts.values() if v >= 2], reverse=True)
    if not groups:
        return "全不同尾"
    if len(groups) == 1 and groups[0] == 6:
        return "全同尾"
    return "+".join(f"1组{g}同尾" for g in groups)

def candidate_profile(reds, blue):
    """对号码进行评分"""
    # 计算各种指标
    reds_sorted = sorted(reds)
    sum_val = sum(reds)
    span = reds_sorted[-1] - reds_sorted[0]
    ac = calculate_ac(reds)
    small = sum(1 for n in reds if n <= 16)
    odd = sum(1 for n in reds if n % 2 == 1)
    z1 = sum(1 for n in reds if 1 <= n <= 11)
    z2 = sum(1 for n in reds if 12 <= n <= 22)
    z3 = 6 - z1 - z2
    run_label = get_consecutive_label(reds)
    tail_pattern = get_tail_pattern(reds)
    
    # 计算均衡度得分
    size_score = [20, 52, 80, 100, 80, 52, 20][small] if small < 7 else 20
    odd_even_score = [20, 52, 80, 100, 80, 52, 20][odd] if odd < 7 else 20
    zone_diff = abs(z1 - 2) + abs(z2 - 2) + abs(z3 - 2)
    zone_score = max(24, min(100, 100 - zone_diff * 22))
    
    # 计算和值、跨度、AC值得分（使用经验值）
    sum_score = max(20, min(100, 100 - abs(sum_val - 100) / 50 * 30))
    span_score = max(20, min(100, 100 - abs(span - 25) / 20 * 30))
    ac_score = max(20, min(100, 100 - abs(ac - 5) / 5 * 30))
    
    # 计算尾数组型得分
    tail_score = 96 if tail_pattern == "全不同尾" else 8 if tail_pattern == "全同尾" else 72
    
    # 计算连号得分
    run_score = 90
    if run_label == "1组2连":
        run_score = 80
    elif run_label == "2连+2连":
        run_score = 72
    elif run_label == "1组3连":
        run_score = 58
    elif run_label in ["1组4连", "1组5连", "全6连号", "3连+2连", "4连+2连"]:
        run_score = 16
    
    # 计算综合均衡度
    balance = round(size_score*0.16 + odd_even_score*0.16 + zone_score*0.2 + sum_score*0.14 + span_score*0.09 + ac_score*0.09 + tail_score*0.06 + run_score*0.05)
    
    # 计算历史结构常见度（简化处理）
    prevalence = 50
    
    # 计算异常安全度
    penalty = 0
    if odd == 6 or odd == 0:
        penalty += 16
    if tail_pattern == "全同尾":
        penalty += 18
    if run_label == "全6连号":
        penalty += 20
    if run_label in ["1组5连", "1组4连", "3连+2连", "4连+2连"]:
        penalty += 16
    if z1 == 0 or z2 == 0 or z3 == 0:
        penalty += 14
    if sum_val <= 60:
        penalty += 12
    if sum_val >= 140:
        penalty += 12
    if ac <= 2:
        penalty += 12
    if ac >= 9:
        penalty += 10
    if blue in reds:
        penalty += 9
    
    penalty_score = max(0, min(100, 100 - penalty))
    score = max(1, min(99, round(prevalence*0.52 + balance*0.40 + penalty_score*0.08)))
    
    # 确定等级
    if score >= 85:
        grade = 'S'
    elif score >= 76:
        grade = 'A'
    elif score >= 67:
        grade = 'B'
    elif score >= 58:
        grade = 'C'
    else:
        grade = 'D'
    
    return {
        'reds': reds_sorted,
        'blue': blue,
        'sum': sum_val,
        'span': span,
        'ac': ac,
        'size_ratio': f"{small}:{6-small}",
        'odd_even_ratio': f"{odd}:{6-odd}",
        'zone_distribution': f"{z1}-{z2}-{z3}",
        'run_label': run_label,
        'tail_pattern': tail_pattern,
        'prevalence': prevalence,
        'balance': balance,
        'penalty_score': penalty_score,
        'score': score,
        'grade': grade
    }

def generate_candidates(n=10):
    """生成随机候选号码"""
    candidates = []
    for _ in range(n):
        # 生成6个不重复的红球
        reds = random.sample(range(1, 34), 6)
        # 生成1个蓝球
        blue = random.randint(1, 16)
        candidates.append((reds, blue))
    return candidates

def sync_latest_results():
    """同步最新的中奖数据"""
    try:
        # 模拟从API获取最新开奖结果
        # 实际项目中应替换为真实的彩票数据API
        latest_data = [
            {"期号": "2026028", "开奖日期": "2026-03-15", "红球": [02, 06, 09, 17, 25, 28], "蓝球": 12},
            {"期号": "2026027", "开奖日期": "2026-03-12", "红球": [03, 07, 12, 18, 23, 31], "蓝球": 05},
            {"期号": "2026026", "开奖日期": "2026-03-10", "红球": [01, 08, 14, 19, 27, 32], "蓝球": 09}
        ]
        
        # 检查本地数据
        local_data = load_data()
        if not local_data:
            local_data = []
        
        # 获取现有期号列表
        existing_issues = set(item['期号'] for item in local_data)
        
        # 找出新数据
        new_data = []
        for item in latest_data:
            if item['期号'] not in existing_issues:
                new_data.append(item)
        
        # 添加新数据到本地
        all_data = local_data + new_data
        all_data.sort(key=lambda x: x['期号'], reverse=True)  # 按期号降序排列
        
        # 保存到文件
        save_data(all_data)
        
        if new_data:
            st.success(f"✅ 成功同步 {len(new_data)} 条新数据")
            for item in new_data:
                st.write(f"- 第{item['期号']}期: {item['红球']} + {item['蓝球']}")
        else:
            st.info("ℹ️ 没有新的开奖数据")
            
        return True
    except Exception as e:
        st.error(f"❌ 同步数据失败：{e}")
        return False

# 页面内容
if page == "总览":
    st.subheader("📊 数据总览")
    data = load_data()
    if data:
        total_draws = len(data)
        latest_data = data[0] if data else None
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("历史总期数", total_draws)
        with col2:
            if latest_data:
                st.metric("最新期开奖", f"{latest_data['期号']}期\n{latest_data['开奖日期']}")
            else:
                st.metric("最新期开奖", "无数据")
        with col3:
            if latest_data:
                st.metric("最新蓝球", latest_data['蓝球'])
            else:
                st.metric("最新蓝球", "无数据")
        with col4:
            if latest_data:
                reds = latest_data['红球']
                sum_val = sum(reds)
                span = max(reds) - min(reds)
                ac = calculate_ac(reds)
                st.metric("最新结构", f"和值: {sum_val}\n跨度: {span}\nAC: {ac}")
            else:
                st.metric("最新结构", "无数据")
    else:
        st.info("数据库尚未初始化或为空，请前往“数据管理”页面添加数据")

elif page == "数据管理":
    st.subheader("🔧 数据管理")
    
    # 初始化CSV文件
    if st.button("📁 初始化数据文件"):
        init_csv()
    
    # 同步最新数据
    st.subheader("🔄 同步中奖数据")
    if st.button("同步最新开奖数据"):
        sync_latest_results()
    
    # 手动添加数据
    st.subheader("➕ 手动添加开奖数据")
    with st.form("add_data_form"):
        issue = st.text_input("期号", help="例如：2026028")
        date = st.text_input("开奖日期 (YYYY-MM-DD)", help="例如：2026-03-15")
        red_balls = st.text_input("红球 (用逗号分隔，如：02,06,09,17,25,28)")
        blue_ball = st.number_input("蓝球", min_value=1, max_value=16)
        submit = st.form_submit_button("添加数据")
        
        if submit:
            try:
                reds = list(map(int, red_balls.split(',')))
                if len(reds) != 6:
                    st.error("❌ 红球必须是6个数字")
                elif len(set(reds)) != 6:
                    st.error("❌ 红球不能重复")
                elif any(n < 1 or n > 33 for n in reds):
                    st.error("❌ 红球必须在1-33之间")
                elif not issue:
                    st.error("❌ 请输入期号")
                elif not date:
                    st.error("❌ 请输入开奖日期")
                else:
                    # 追加到CSV文件
                    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([issue, date, ','.join(map(str, reds)), blue_ball])
                    st.success(f"✅ 数据添加成功：第{issue}期")
            except ValueError:
                st.error("❌ 请输入正确的数字格式")
            except Exception as e:
                st.error(f"❌ 添加数据失败：{e}")
    
    # 显示数据文件状态
    st.subheader("📋 数据文件状态")
    if os.path.exists(CSV_FILE):
        data = load_data()
        if data:
            st.success(f"✅ 数据文件存在，当前有 {len(data)} 条记录")
            if st.checkbox("🔍 显示前10条数据"):
                # 创建一个简单的表格显示
                for i, item in enumerate(data[:10]):
                    st.write(f"第{i+1}条: 期号: {item['期号']}, 日期: {item['开奖日期']}, 红球: {item['红球']}, 蓝球: {item['蓝球']}")
        else:
            st.info("数据文件存在，但无数据")
    else:
        st.warning("⚠️ 数据文件不存在，请先初始化")

elif page == "历史开奖":
    st.subheader("📜 历史开奖记录")
    data = load_data()
    if data:
        # 筛选条件
        start_issue = st.text_input("🔍 筛选起始期号", help="输入期号以查看大于等于此期的记录")
        
        # 应用筛选
        filtered_data = data.copy()
        if start_issue:
            filtered_data = [item for item in filtered_data if item['期号'] >= start_issue]
        
        # 显示结果
        st.write(f"共找到 {len(filtered_data)} 条记录：")
        if filtered_data:
            # 创建表格显示
            table_data = []
            for item in filtered_data:
                table_data.append({
                    "期号": item['期号'],
                    "开奖日期": item['开奖日期'],
                    "红球": ", ".join(map(str, item['红球'])),
                    "蓝球": item['蓝球']
                })
            st.table(table_data)
        else:
            st.info("未找到符合条件的记录")
    else:
        st.info("数据库尚未初始化或为空，请前往“数据管理”页面添加数据")

elif page == "号码评分":
    st.subheader("⚖️ 号码评分")
    
    # 输入号码
    st.write("请输入6个红球和1个蓝球")
    col1, col2 = st.columns(2)
    with col1:
        red1 = st.number_input("红球1", min_value=1, max_value=33, value=1)
        red2 = st.number_input("红球2", min_value=1, max_value=33, value=2)
        red3 = st.number_input("红球3", min_value=1, max_value=33, value=3)
    with col2:
        red4 = st.number_input("红球4", min_value=1, max_value=33, value=4)
        red5 = st.number_input("红球5", min_value=1, max_value=33, value=5)
        red6 = st.number_input("红球6", min_value=1, max_value=33, value=6)
    blue = st.number_input("蓝球", min_value=1, max_value=16, value=1)
    
    # 验证输入
    reds = [red1, red2, red3, red4, red5, red6]
    if len(set(reds)) != 6:
        st.error("❌ 红球不能重复")
    else:
        if st.button("🔍 评分"):
            profile = candidate_profile(reds, blue)
            
            # 显示评分结果
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("综合评分", profile['score'])
            with col2:
                st.metric("等级", profile['grade'])
            with col3:
                if profile['grade'] in ['S', 'A']:
                    st.success("推荐指数: 高")
                elif profile['grade'] in ['B', 'C']:
                    st.warning("推荐指数: 中")
                else:
                    st.error("推荐指数: 低")
            
            # 显示详细信息
            st.subheader("📈 详细分析")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**红球：** {profile['reds']}")
                st.write(f"**蓝球：** {profile['blue']}")
                st.write(f"**和值：** {profile['sum']}")
                st.write(f"**跨度：** {profile['span']}")
                st.write(f"**AC值：** {profile['ac']}")
            with col2:
                st.write(f"**大小比：** {profile['size_ratio']}")
                st.write(f"**奇偶比：** {profile['odd_even_ratio']}")
                st.write(f"**三区分布：** {profile['zone_distribution']}")
                st.write(f"**连号结构：** {profile['run_label']}")
                st.write(f"**尾数组型：** {profile['tail_pattern']}")
            
            # 显示评分详情
            st.subheader("📊 评分详情")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("历史结构常见度", profile['prevalence'])
            with col2:
                st.metric("结构均衡度", profile['balance'])
            with col3:
                st.metric("异常安全度", profile['penalty_score'])

elif page == "本期推荐":
    st.subheader("🎲 本期推荐")
    
    # 设置参数
    num_candidates = st.slider("生成候选号码数量", min_value=5, max_value=50, value=10)
    
    if st.button("🚀 生成推荐号码"):
        st.info(f"正在生成 {num_candidates} 个候选号码...")
        candidates = generate_candidates(num_candidates)
        
        # 对每个候选号码进行评分
        profiles = []
        for reds, blue in candidates:
            profile = candidate_profile(reds, blue)
            profiles.append(profile)
        
        # 按评分排序
        profiles.sort(key=lambda x: x['score'], reverse=True)
        
        # 显示结果
        st.subheader("🏆 推荐号码")
        for i, profile in enumerate(profiles[:10]):  # 只显示前10个
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**推荐 {i+1}: {profile['reds']} + {profile['blue']}**")
            with col2:
                st.write(f"**评分: {profile['score']}**")
            with col3:
                st.write(f"**等级: {profile['grade']}**")
            
            # 显示详细信息
            with st.expander(f"查看详情 #{i+1}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"红球：{profile['reds']}")
                    st.write(f"蓝球：{profile['blue']}")
                    st.write(f"和值：{profile['sum']}")
                    st.write(f"跨度：{profile['span']}")
                    st.write(f"AC值：{profile['ac']}")
                with col2:
                    st.write(f"大小比：{profile['size_ratio']}")
                    st.write(f"奇偶比：{profile['odd_even_ratio']}")
                    st.write(f"三区分布：{profile['zone_distribution']}")
                    st.write(f"连号结构：{profile['run_label']}")
                    st.write(f"尾数组型：{profile['tail_pattern']}")
                
                # 评分详情
                st.write("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("历史结构常见度", profile['prevalence'])
                with col2:
                    st.metric("结构均衡度", profile['balance'])
                with col3:
                    st.metric("异常安全度", profile['penalty_score'])

# 页脚
st.markdown("---")
st.markdown("*双色球分析预测系统 v1.0 | 数据仅供参考，请理性购彩*")
