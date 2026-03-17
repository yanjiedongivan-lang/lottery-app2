import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
import time

# ==========================================
# 页面配置
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
    .stButton > button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 50px; 
        font-size: 18px; 
        background-color: #FF4B4B; 
        color: white;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > b
