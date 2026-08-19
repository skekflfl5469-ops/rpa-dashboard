# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

# 서버 위치와 무관하게 항상 한국 시간 기준으로 동작
def now_kst():
    return datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)
import base64
import os

# ==========================================
# 1. 페이지 설정 및 디자인
# ==========================================
st.set_page_config(page_title="RPA DashBorad", layout="wide")

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except: return ""

logo_base64 = get_base64_image("logo.png")

# 메인 대시보드용 스타일
st.markdown(f"""
    <style>
    div[data-testid="stAppViewBlockContainer"] {{
        max-width: 1500px !important; 
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
    }}
    [data-testid="stMetricValue"] {{ 
        font-size: 26px !important; 
        font-weight: 800 !important; 
        line-height: 1.2 !important; 
        color: #1E2732;
    }}
    [data-testid="stMetricLabel"] {{ 
        font-size: 14px !important; 
        margin-bottom: 2px !important; 
        color: #555;
    }}
    .header-wrapper {{
        display: flex;
        align-items: center;
        gap: 20px;
    }}
    hr {{ margin: 15px 0 !important; opacity: 0.5; }}
    .agg-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed; }}
    .agg-table th, .agg-table td {{ 
        text-align: center !important; border: 1px solid #dee2e6; padding: 10px !important; font-size: 14px !important;
    }}
    .agg-table th {{ background-color: #f8f9fa; font-weight: bold; color: #444; }}
    .left-text {{ text-align: left !important; padding-left: 15px !important; }}
    .error-red {{ color: #d32f2f; font-weight: 600; text-align: left !important; font-size: 14px; }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. 로그인 세션 관리 및 로그인 화면
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""

def login():
    ALLOWED_USERS = {
        "pulmuone": "rpa1234",
        "yhwoo": "dudgns23!",
        "guest": "1234"
    }

    st.markdown("""
        <style>
        div[data-testid="stAppViewBlockContainer"] { padding-top: 8rem !important; }
        .login-box-with-logo, .header-wrapper, .agg-table { display: none !important; }
        .login-wrapper { max-width: 400px; margin: 0 auto; text-align: center; }
        [data-testid="stVerticalBlock"] { background-color: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
        st.markdown("""
            <div style="margin-bottom: 40px;">
                <h1 style="color: #1E2732; font-size: 36px; font-weight: 900; letter-spacing: -1px; margin-bottom:0;">
                    RPA <span style="color: #4A90E2;">DASHBOARD</span>
                </h1>
                <p style="color: #888; font-size: 14px; font-weight: 700; text-transform: uppercase; margin-top:0;">
                    Real-time Process Monitoring
                </p>
            </div>
        """, unsafe_allow_html=True)

        user_input = st.text_input("아이디", placeholder="ID를 입력하세요", key="login_id")
        pass_input = st.text_input("비밀번호", type="password", placeholder="Password를 입력하세요", key="login_pw")
        
        if st.button("로그인", width="stretch"):
            if user_input in ALLOWED_USERS and ALLOWED_USERS[user_input] == pass_input:
                st.session_state.logged_in = True
                st.session_state.user_id = user_input
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    login()
    st.stop()

# ==========================================
# 3. 데이터 생성 로직 (7일 조회 무오류 반영)
# ==========================================
@st.cache_data(ttl=60)
def load_rpa_complete_data(start_date, end_date, seed_val=42):
    np.random.seed(seed_val)
    error_types = ["WebAutomation.LaunchEdgeError", "Excel.OpenWorkbookError", "Outlook.SendMailError", "File.NotFoundError", "Network.ConnectionTimeout"]
    now = now_kst()
    curr_today = now.date()

    raw_data = [
        {"업무명": "EAM 계측기 검교정 미완료 현황 메일링", "시간": "06:00:00", "수행시간": "01일", "주기": "1회/월(01일)", "부서": "DSF기획팀"},
        {"업무명": "EAM 주간고장(2시간)현황 메일링", "시간": "09:00:00", "수행시간": "2,4주차 월", "주기": "2회/월(2,4주차 월요일)", "부서": "DSF기획팀", "오픈일": "2026-08-10"},
        {"업무명": "함안홈플러스 본품 ERP 주문내역 조회/수신", "시간": "09:10:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀", "오픈일": "2026-08-07"},
        {"업무명": "함안홈플러스 증정 ERP 주문내역 조회/수신", "시간": "09:15:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀", "오픈일": "2026-08-07"},
        {"업무명": "함안홈플러스 본품 발주서 주문내역 조회/수신", "시간": "09:20:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀", "오픈일": "2026-08-07"},
        {"업무명": "EAM 고장 접수 미 완료 및 비계획 고장 미 등록 관련", "시간": "09:30:00", "수행시간": "매일", "주기": "5회/주(월~금)", "부서": "DSF기획팀"},
        {"업무명": "SE시식/증정 ERP 주문내역 메일링", "시간": "09:30:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀"},
        {"업무명": "[유틸리티일상점검이탈 알림] 일상점검 이탈 사유 등록 요청의 건", "시간": "09:40:00", "수행시간": "매일", "주기": "5회/주(월~금)", "부서": "DSF기획팀"},
        {"업무명": "[설비고장 사유등록 알림] MES 설비 고장 사유 등록 요청의 건", "시간": "09:50:00", "수행시간": "매일", "주기": "5회/주(월~금)", "부서": "DSF기획팀"},
        {"업무명": "[설비정기점검 알림] [공] 설비 정기점검 현황", "시간": "10:00:00", "수행시간": "매일", "주기": "2회/월(2,4주차 월요일)", "부서": "DSF기획팀"},
        {"업무명": "EAM월간 고장현황 메일링", "시간": "10:10:00", "수행시간": "10일", "주기": "1회/월(10일)", "부서": "DSF기획팀"},
        {"업무명": "MRO 부품구매내역 EAM 업로드 양식 가공 및 메일링", "시간": "10:20:00", "수행시간": "10일", "주기": "1회/월(10일)", "부서": "DSF기획팀"},
        {"업무명": "음성물류 소터운영 현황보고 작성 메일링", "시간": "13:30:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀"},
        {"업무명": "롯데마트 주문수량 메일 자동 다운로드", "시간": "15:00:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀"},
        {"업무명": "일단위 B2B 생산성 실적보고", "시간": "15:10:00", "수행시간": "매일", "주기": "5회/주(월~금)", "부서": "양지센터운영팀", "오픈일": "2026-06-25", "제외일": ["2026-07-21"]},
        {"업무명": "업체미입고 백업본 Share point 생성", "시간": "22:00:00", "수행시간": "매일", "주기": "7회/주(월~일)", "부서": "음성센터운영팀"}
    ]
    
    # [수정] 오류는 월별 1~2건만 발생 (월 시드 고정으로 조회 시마다 동일한 결과)
    daily_items = [(it['업무명'], datetime.strptime(it['오픈일'], "%Y-%m-%d").date() if "오픈일" in it else None)
                   for it in raw_data if "7회/주" in it['주기']]
    error_events = {}
    m_cursor = date(start_date.year, start_date.month, 1)
    while m_cursor <= end_date:
        rng = np.random.RandomState(seed_val + m_cursor.year * 100 + m_cursor.month)
        for _ in range(int(rng.randint(1, 3))):  # 한 달에 1~2건
            err_date = date(m_cursor.year, m_cursor.month, int(rng.randint(1, 29)))
            candidates = [name for name, opened in daily_items if opened is None or opened <= err_date]
            if not candidates: continue
            err_task = candidates[int(rng.randint(0, len(candidates)))]
            error_events[(err_date, err_task)] = str(rng.choice(error_types))
        m_cursor = date(m_cursor.year + (m_cursor.month == 12), m_cursor.month % 12 + 1, 1)

    generated_data = []
    for i in range((end_date - start_date).days + 1):
        curr_date = start_date + timedelta(days=i)
        for item in raw_data:
            run_time_obj = datetime.strptime(item['시간'], '%H:%M:%S').time()
            start_t = datetime.combine(curr_date, run_time_obj)
            
            if curr_date > curr_today: continue
            if curr_date == curr_today and start_t > now: continue

            # 오픈일 이전에는 구동 이력 생성 안 함
            if "오픈일" in item and curr_date < datetime.strptime(item["오픈일"], "%Y-%m-%d").date():
                continue

            # 특정 날짜만 미수행 처리 (제외일)
            if curr_date.strftime("%Y-%m-%d") in item.get("제외일", []):
                continue

            is_run = True
            if "1회/월(10일)" in item['주기'] and curr_date.day != 10: is_run = False
            elif "1회/월(01일)" in item['주기'] and curr_date.day != 1: is_run = False
            elif "5회/주(월~금)" in item['주기'] and curr_date.weekday() >= 5: is_run = False
            elif "2,4주차 월요일" in item['주기'] and not (curr_date.weekday() == 0 and (8 <= curr_date.day <= 14 or 22 <= curr_date.day <= 28)): is_run = False
            
            if is_run:
                dur_min, dur_max = item.get("구동범위", (60, 120))
                
                if curr_date != curr_today and (curr_date, item['업무명']) in error_events:
                    generated_data.append({
                        "RPA명": item['업무명'], "실행주기": item['주기'], "수행시간": item['시간'][:5], "주관부서": item['부서'],
                        "날짜": curr_date, "상태": "오류", "구동시간": np.random.randint(5, min(30, dur_max)),
                        "에러내용": error_events[(curr_date, item['업무명'])], "hour": start_t.hour, "날짜_표시": curr_date.strftime('%m월 %d일')
                    })
                    retry_t = start_t + timedelta(minutes=5)
                    generated_data.append({
                        "RPA명": item['업무명'], "실행주기": item['주기'], "수행시간": retry_t.strftime('%H:%M'), "주관부서": item['부서'],
                        "날짜": curr_date, "상태": "성공", "구동시간": np.random.randint(dur_min, dur_max),
                        "에러내용": "-", "hour": retry_t.hour, "날짜_표시": curr_date.strftime('%m월 %d일')
                    })
                else:
                    generated_data.append({
                        "RPA명": item['업무명'], "실행주기": item['주기'], "수행시간": item['시간'][:5], "주관부서": item['부서'],
                        "날짜": curr_date, "상태": "성공", "구동시간": np.random.randint(dur_min, dur_max),
                        "에러내용": "-", "hour": start_t.hour, "날짜_표시": curr_date.strftime('%m월 %d일')
                    })
    return pd.DataFrame(generated_data)

# ==========================================
# 3-1. NAS(WebDAV) 실데이터 로드
#  - Streamlit Secrets에 [nas] 설정이 있으면 NAS의 로그 CSV를 읽어옴
#  - 없거나 실패하면 기존 시뮬레이션 데이터로 동작
# ==========================================
@st.cache_data(ttl=60)
def load_rpa_log_from_nas(start_date, end_date):
    import requests, io
    cfg = st.secrets["nas"]
    r = requests.get(cfg["url"], auth=(cfg["user"], cfg["password"]), timeout=15)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")))

    # 규격: 날짜,수행시간,RPA명,실행주기,주관부서,상태,구동시간(초),에러내용
    df = df.rename(columns={'구동시간(초)': '구동시간'})
    df['날짜'] = pd.to_datetime(df['날짜']).dt.date
    df = df[(df['날짜'] >= start_date) & (df['날짜'] <= end_date)].copy()
    df['수행시간'] = df['수행시간'].astype(str).str.strip().str.slice(0, 5)
    df['hour'] = df['수행시간'].str.slice(0, 2).astype(int)
    df['날짜_표시'] = pd.to_datetime(df['날짜'].astype(str)).dt.strftime('%m월 %d일')
    df['에러내용'] = df['에러내용'].fillna('-')
    df['구동시간'] = pd.to_numeric(df['구동시간'], errors='coerce').fillna(0).astype(int)
    return df.sort_values(['날짜', '수행시간']).reset_index(drop=True)

# ==========================================
# 4. 메인 로직 및 대시보드 구성
# ==========================================
today = now_kst().date()
if 's_date' not in st.session_state: st.session_state.s_date = today - timedelta(days=6)
if 'e_date' not in st.session_state: st.session_state.e_date = today

def nas_configured():
    """Secrets에 [nas] 설정이 있는지 확인 (secrets 파일이 아예 없는 로컬 환경도 안전하게 처리)"""
    try:
        return "nas" in st.secrets
    except Exception:
        return False

data_source = "시뮬레이션"
if nas_configured():
    try:
        nas_df = load_rpa_log_from_nas(st.session_state.s_date, st.session_state.e_date)
        real_tasks = list(st.secrets["nas"].get("real_tasks", []))

        if real_tasks:
            # 혼합 모드: 지정 업무만 NAS 실데이터, 나머지는 시뮬레이션 유지
            nas_df = nas_df[nas_df['RPA명'].isin(real_tasks)]
            sim_df = load_rpa_complete_data(st.session_state.s_date, st.session_state.e_date)
            sim_df = sim_df[~sim_df['RPA명'].isin(real_tasks)]
            f_df = pd.concat([nas_df, sim_df], ignore_index=True).sort_values(['날짜', '수행시간']).reset_index(drop=True)
            data_source = f"혼합 (실데이터 {len(real_tasks)}개 업무 + 시뮬레이션)"
        else:
            # 전체 실데이터 모드
            f_df = nas_df
            data_source = "NAS 실데이터"
    except Exception as ex:
        st.warning(f"NAS 로그를 불러오지 못해 시뮬레이션 데이터로 표시합니다. ({type(ex).__name__})")
        f_df = load_rpa_complete_data(st.session_state.s_date, st.session_state.e_date)
else:
    f_df = load_rpa_complete_data(st.session_state.s_date, st.session_state.e_date)

col_left, col_right = st.columns([1, 1], vertical_alignment="center")

with col_left:
    st.markdown(f"""
        <div class="header-wrapper">
            <img src="data:image/png;base64,{logo_base64}" width="200">
            <div style="background-color: #4A90E2; width: 4px; height: 38px; border-radius: 2px;"></div>
            <div>
                <h1 style="margin: 0; font-size: 38px; font-weight: 900; color: #1E2732; line-height:1;">
                    RPA <span style="color: #4A90E2;">DASHBOARD</span>
                </h1>
                <p style="margin: 0; font-size: 13px; color: #888; font-weight: 700;">접속 계정: {st.session_state.user_id.upper()}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    btn_col = st.columns([1, 1, 1, 1, 4.5])
    if btn_col[0].button("오늘"): 
        st.session_state.s_date, st.session_state.e_date = today, today
        st.rerun()
    if btn_col[1].button("7일"): 
        st.session_state.s_date, st.session_state.e_date = today - timedelta(days=6), today
        st.rerun()
    if btn_col[2].button("30일"): 
        st.session_state.s_date, st.session_state.e_date = today - timedelta(days=29), today
        st.rerun()
    if btn_col[3].button("로그아웃"): 
        st.session_state.logged_in = False
        st.rerun()
    
    with btn_col[4]:
        sub_col1, sub_col2, sub_col3 = st.columns([3, 1, 1])
        picked = sub_col1.date_input("날짜", [st.session_state.s_date, st.session_state.e_date], label_visibility="collapsed", key="date_picker_input")
        if sub_col2.button("조회"):
            if isinstance(picked, (list, tuple)) and len(picked) == 2:
                st.session_state.s_date, st.session_state.e_date = picked[0], picked[1]
                st.rerun()
        if sub_col3.button("새로고침", help="로그아웃 없이 최신 로그를 다시 불러옵니다"):
            st.cache_data.clear()
            st.rerun()

    total_succ = len(f_df[f_df['상태'] == '성공'])
    total_fail = len(f_df[f_df['상태'] == '오류'])
    m_col = st.columns([1, 1, 1])
    m_col[0].metric("실행 업무", f"{f_df['RPA명'].nunique()}개")
    m_col[1].metric("총 성공 건수", f"{total_succ}건")
    m_col[2].metric("총 실패 건수", f"{total_fail}건")

st.markdown("<hr>", unsafe_allow_html=True)

title_col, dl_col = st.columns([5, 1], vertical_alignment="center")
title_col.write(f"#### 📋 항목별 구동 현황 ({st.session_state.s_date} ~ {st.session_state.e_date})")

# 조회 기간의 건별 실행 이력을 로그 파일로 다운로드
if not f_df.empty:
    log_df = f_df.copy()
    log_df['날짜'] = log_df['날짜'].astype(str)
    log_df = log_df.sort_values(['날짜', '수행시간'])[['날짜', '수행시간', 'RPA명', '실행주기', '주관부서', '상태', '구동시간', '에러내용']]
    log_df = log_df.rename(columns={'구동시간': '구동시간(초)'})
    log_csv = log_df.to_csv(index=False).encode('utf-8-sig')
    dl_col.download_button(
        "📥 로그 다운로드",
        data=log_csv,
        file_name=f"rpa_log_{st.session_state.s_date}_{st.session_state.e_date}.csv",
        mime="text/csv"
    )

def get_agg_row(group):
    succ_count = len(group[group['상태'] == '성공'])
    fail_count = len(group[group['상태'] == '오류'])
    error_list = group[group['상태'] == '오류']['에러내용'].unique()
    err_txt = error_list[0] if len(error_list) > 0 else "-"
    avg_time = int(group['구동시간'].mean()) if len(group) > 0 else 0
    
    return pd.Series({
        'RPA명_html': f"<div class='left-text'>{group.name}</div>",
        '실행주기': group['실행주기'].iloc[0],
        '수행시간': group['수행시간'].iloc[0],
        '상태_html': f"<span style='color:#28a745; font-weight:bold;'>성공({succ_count})</span>, <span style='color:#dc3545; font-weight:bold;'>실패({fail_count})</span>",
        '평균': f"{avg_time}초",
        '에러_html': f"<div class='error-red'>{err_txt}</div>",
        '주관부서': group['주관부서'].iloc[0]
    })

if f_df.empty:
    st.info("조회 기간에 실행 이력이 없습니다.")
else:
    agg_df = f_df.groupby('RPA명', sort=False).apply(get_agg_row, include_groups=False).reset_index()
    agg_df = agg_df.sort_values('수행시간').reset_index(drop=True)
    agg_df.insert(0, '순번', range(1, len(agg_df) + 1))

    table_html = f"""
<table class='agg-table'>
    <thead>
        <tr>
            <th style='width: 50px;'>순번</th>
            <th style='width: 320px;'>RPA명</th>
            <th style='width: 100px;'>실행주기</th>
            <th style='width: 80px;'>수행시간</th>
            <th style='width: 160px;'>상태 (기간 합산)</th>
            <th style='width: 100px;'>평균구동시간</th>
            <th style='width: 380px;'>에러내용</th>
            <th style='width: 120px;'>주관부서</th>
        </tr>
    </thead>
    <tbody>
"""
    for _, row in agg_df.iterrows():
        table_html += f"""<tr>
        <td>{row['순번']}</td>
        <td>{row['RPA명_html']}</td>
        <td>{row['실행주기']}</td>
        <td>{row['수행시간']}</td>
        <td>{row['상태_html']}</td>
        <td>{row['평균']}</td>
        <td>{row['에러_html']}</td>
        <td><b>{row['주관부서']}</b></td>
    </tr>"""
    table_html += "</tbody></table>"
    st.write(table_html, unsafe_allow_html=True)

    # ==========================================
    # 상세 내역: 업무 선택 시 건별 실행 이력 표시
    # ==========================================
    with st.expander("🔍 RPA 상세 내역 보기 (업무별 실행 이력)"):
        rpa_options = agg_df['RPA명'].tolist()
        sel_rpa = st.selectbox("업무 선택", rpa_options)
        detail = f_df[f_df['RPA명'] == sel_rpa].sort_values(['날짜', '수행시간']).reset_index(drop=True)

        d_succ = len(detail[detail['상태'] == '성공'])
        d_fail = len(detail[detail['상태'] == '오류'])
        d_avg = int(detail[detail['상태'] == '성공']['구동시간'].mean()) if d_succ > 0 else 0

        dm = st.columns(4)
        dm[0].metric("총 실행", f"{len(detail)}건")
        dm[1].metric("성공", f"{d_succ}건")
        dm[2].metric("실패", f"{d_fail}건")
        dm[3].metric("평균 구동시간", f"{d_avg}초")

        # 날짜별 성공/실패 추이 라인
        if detail['날짜'].nunique() > 1:
            d_trend = detail.groupby('날짜_표시').apply(
                lambda x: pd.Series({'성공': len(x[x['상태'] == '성공']), '실패': len(x[x['상태'] == '오류'])}),
                include_groups=False).reset_index()
            fig_detail = go.Figure()
            fig_detail.add_trace(go.Scatter(x=d_trend['날짜_표시'], y=d_trend['성공'], name='성공', mode='lines+markers', line=dict(color='#28a745')))
            fig_detail.add_trace(go.Scatter(x=d_trend['날짜_표시'], y=d_trend['실패'], name='실패', mode='lines+markers', line=dict(color='#dc3545')))
            fig_detail.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=10), hovermode="x unified",
                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                                     yaxis=dict(dtick=1))
            st.plotly_chart(fig_detail, width="stretch")

        # 건별 실행 이력 테이블
        detail_html = """
<table class='agg-table'>
    <thead>
        <tr>
            <th style='width: 100px;'>날짜</th>
            <th style='width: 80px;'>수행시간</th>
            <th style='width: 80px;'>상태</th>
            <th style='width: 100px;'>구동시간</th>
            <th>에러내용</th>
        </tr>
    </thead>
    <tbody>
"""
        for _, r in detail.iterrows():
            if r['상태'] == '성공':
                stat_html = "<span style='color:#28a745; font-weight:bold;'>성공</span>"
                err_html = "-"
            else:
                stat_html = "<span style='color:#dc3545; font-weight:bold;'>실패</span>"
                err_html = f"<span class='error-red'>{r['에러내용']}</span>"
            detail_html += f"""<tr>
        <td>{r['날짜']}</td>
        <td>{r['수행시간']}</td>
        <td>{stat_html}</td>
        <td>{r['구동시간']}초</td>
        <td class='left-text'>{err_html}</td>
    </tr>"""
        detail_html += "</tbody></table>"
        st.write(detail_html, unsafe_allow_html=True)

c1, c2 = st.columns([1.5, 1])
with c1:
    st.write("#### 📊 날짜별 실행 및 오류 추세")
    if not f_df.empty:
        trend = f_df.groupby('날짜_표시').apply(lambda x: pd.Series({'실행': len(x[x['상태']=='성공']), '오류': len(x[x['상태']=='오류'])}), include_groups=False).reset_index()
        fig_mix = go.Figure()
        fig_mix.add_trace(go.Bar(x=trend['날짜_표시'], y=trend['실행'], name='성공(실행)', marker_color='#4A90E2', width=0.3))
        fig_mix.add_trace(go.Scatter(x=trend['날짜_표시'], y=trend['오류'], name='오류건수', mode='lines+markers', line=dict(color='#D0021B')))
        fig_mix.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=10), hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
        st.plotly_chart(fig_mix, width="stretch")

with c2:
    st.write("#### 🍩 상태 비중(전체 수행횟수(성공+오류))")
    if not f_df.empty:
        status_cnt = f_df['상태'].value_counts()
        fig_pie = go.Figure(data=[go.Pie(labels=status_cnt.index, values=status_cnt.values, hole=0.6, marker=dict(colors=['#28a745', '#dc3545']))])
        fig_pie.update_layout(height=320, margin=dict(t=30, b=0, l=0, r=0), showlegend=False, annotations=[dict(text=f"<b>{len(f_df)}</b>", x=0.5, y=0.5, font=dict(size=30), showarrow=False)])
        st.plotly_chart(fig_pie, width="stretch")

st.markdown("---")
st.write("#### ⏰ 시간대별 실행 현황 ")

hr_detail = f_df.groupby(['hour', 'RPA명']).size().reset_index(name='count')

def get_hover_text(hour, df):
    sub = df[df['hour'] == hour]
    if sub.empty: return f"<b>{hour}시</b><br>실행 내역 없음"
    lines = [f"• {row['RPA명']}: {row['count']}건" for _, row in sub.iterrows()]
    total = sub['count'].sum()
    return f"<b>{hour}시 (총 {total}건)</b><br>" + "<br>".join(lines)

hr_list = range(24)
hover_texts = [get_hover_text(h, hr_detail) for h in hr_list]
total_counts = [hr_detail[hr_detail['hour'] == h]['count'].sum() if h in hr_detail['hour'].values else 0 for h in hr_list]

fig_hr = go.Figure(data=[go.Bar(x=list(hr_list), y=total_counts, hovertext=hover_texts, hoverinfo="text", marker_color='#4A90E2')])
fig_hr.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=10), xaxis=dict(dtick=1, title="시간(Hour)"), yaxis=dict(title="실행 건수"))
st.plotly_chart(fig_hr, width="stretch")
