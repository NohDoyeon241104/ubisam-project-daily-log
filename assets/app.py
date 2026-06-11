"""
프로젝트 일일 기록 — 프롬프트 생성기 + 대시보드 + 엑셀 내보내기
실행: streamlit run app.py
"""
import json
import os
import io
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# 설정 / 상수
# ----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
PROJECTS_JSON = APP_DIR / "projects.json"

STATUS_PROJECT = ["예정", "진행중", "완료"]      # 프로젝트 전체 상태
STATUS_DAILY = ["정상", "지연", "이슈"]          # 그날 하루 상태
DEFAULT_COLORS = {"예정": "#EF9F27", "진행중": "#639922", "완료": "#888780"}

st.set_page_config(page_title="프로젝트 일일 기록", layout="wide")


# ----------------------------------------------------------------------------
# 데이터 로드 / 저장
# ----------------------------------------------------------------------------
def load_config():
    if PROJECTS_JSON.exists():
        with open(PROJECTS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"log_root": "", "status_colors": DEFAULT_COLORS, "projects": []}


def save_config(cfg):
    with open(PROJECTS_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def to_folder_id(name: str) -> str:
    return name.strip().replace(" ", "_")


# ----------------------------------------------------------------------------
# 마크다운 로그 파싱 (대시보드/엑셀용)
# ----------------------------------------------------------------------------
def parse_log_md(text: str) -> dict:
    """YAML 머리말 + 본문 섹션을 dict로 파싱."""
    meta, body = {}, text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2]

    sections, current = {}, None
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            current = s[3:].strip()
            sections[current] = []
        elif s.startswith("- ") and current:
            sections[current].append(s[2:].strip())
    meta["_sections"] = sections
    return meta


def scan_logs(log_root: str, projects: list) -> pd.DataFrame:
    rows = []
    root = Path(log_root)
    if not root.exists():
        return pd.DataFrame()
    valid_ids = {p["id"] for p in projects}
    for proj_dir in root.iterdir():
        if not proj_dir.is_dir() or proj_dir.name not in valid_ids:
            continue
        for md in proj_dir.glob("*.md"):
            try:
                meta = parse_log_md(md.read_text(encoding="utf-8"))
            except Exception:
                continue
            sec = meta.get("_sections", {})
            rows.append({
                "프로젝트": meta.get("project", proj_dir.name),
                "날짜": meta.get("date", md.stem),
                "작성자": meta.get("author", ""),
                "진행률": meta.get("progress", ""),
                "상태": meta.get("status", ""),
                "오늘 한 일": " / ".join(sec.get("오늘 한 일", [])),
                "이슈": " / ".join(sec.get("이슈 / 블로커", [])),
                "내일 할 일": " / ".join(sec.get("내일 할 일", [])),
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["프로젝트", "날짜"]).reset_index(drop=True)
    return df


# ----------------------------------------------------------------------------
# 프롬프트 생성
# ----------------------------------------------------------------------------
def build_prompt(log_root, proj_id, the_date, author, status, work_text) -> str:
    path = f"{log_root}/{proj_id}/{the_date}.md".replace("\\", "/")
    template_path = f"{log_root}/_templates/daily_log_template.md".replace("\\", "/")
    return (
        f"반드시 {template_path} 를 읽고, 아래 작업 내용을 "
        f"체크리스트로 정리해서 {path} 로 저장해줘.\n\n"
        f"project: {proj_id}\n"
        f"date: {the_date}\n"
        f"author: {author}\n"
        f"status: {status}\n\n"
        f"[작업 내용]\n{work_text.strip()}\n\n"
        f"오늘 한 일 / 이슈·블로커 / 내일 할 일 로 분류하고, "
        f"이모지·볼드체 남발 금지, status 는 정상/지연/이슈 중 하나만 사용."
    )


# ----------------------------------------------------------------------------
# 메인
# ----------------------------------------------------------------------------
cfg = load_config()
if "cfg" not in st.session_state:
    st.session_state.cfg = cfg
cfg = st.session_state.cfg

st.title("프로젝트 일일 기록 — 프롬프트 생성기")

# 기록 루트
col_root, col_btn = st.columns([4, 1])
with col_root:
    cfg["log_root"] = st.text_input("기록 루트 경로", value=cfg.get("log_root", ""))
with col_btn:
    st.write("")
    st.write("")
    if st.button("저장", use_container_width=True):
        save_config(cfg)
        st.success("저장됨")

tab_input, tab_projects, tab_dashboard = st.tabs(
    ["기록 입력", "프로젝트 관리", "대시보드 / 내보내기"]
)

# ── 탭1: 기록 입력 + 프롬프트 생성 ───────────────────────────────────────────
with tab_input:
    projects = cfg.get("projects", [])
    if not projects:
        st.info("먼저 '프로젝트 관리' 탭에서 프로젝트를 추가하세요.")
    else:
        names = [p["name"] for p in projects]
        sel = st.selectbox("프로젝트", names)
        proj = next(p for p in projects if p["name"] == sel)

        c1, c2 = st.columns(2)
        with c1:
            the_date = st.date_input("날짜", value=date.today())
        with c2:
            daily_status = st.selectbox("상태 (그날)", STATUS_DAILY)

        default_author = ", ".join(proj.get("members", []))
        author = st.text_input("담당자 / 협업자 ( , 로 구분 )", value=default_author)
        work_text = st.text_area(
            "작업한 내용 ( 자유롭게 적으면 AI가 체크리스트로 정리 )", height=160
        )

        col_gen, col_up = st.columns([3, 2])
        with col_gen:
            gen = st.button("1. 프롬프트 생성", type="primary", use_container_width=True)
        with col_up:
            uploaded = st.file_uploader("또는 파일 업로드", type=["txt", "md"])

        if uploaded and not work_text:
            work_text = uploaded.read().decode("utf-8")

        if gen or uploaded:
            prompt = build_prompt(
                cfg["log_root"], proj["id"], the_date.isoformat(),
                author, daily_status, work_text or "(작업 내용 없음)",
            )
            st.text_area("생성된 프롬프트 (Claude에 붙여넣기)", value=prompt, height=220)
            st.caption("위 내용을 복사해 Claude(또는 Claude Code)에 붙여넣으면 "
                       "체크리스트 .md 가 지정 경로에 저장됩니다.")

# ── 탭2: 프로젝트 관리 (CRUD) ────────────────────────────────────────────────
with tab_projects:
    st.subheader("프로젝트 목록")
    for i, p in enumerate(cfg["projects"]):
        color = cfg.get("status_colors", DEFAULT_COLORS).get(p["status"], "#888780")
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.markdown(
            f"<span style='display:inline-block;width:10px;height:10px;"
            f"border-radius:50%;background:{color};margin-right:6px'></span>"
            f"<b>{p['name']}</b>", unsafe_allow_html=True,
        )
        c2.write(f"{p.get('start','')} ~ {p.get('end','') or '미정'}")
        c3.write(p["status"])
        if c4.button("삭제", key=f"del_{i}"):
            cfg["projects"].pop(i)
            save_config(cfg)
            st.rerun()

    st.divider()
    st.subheader("프로젝트 추가 / 편집")
    with st.form("proj_form"):
        name = st.text_input("프로젝트명")
        c1, c2 = st.columns(2)
        start = c1.text_input("시작일 (YYYY-MM-DD)")
        end = c2.text_input("종료일 (미정 가능)")
        status = st.selectbox("상태", STATUS_PROJECT, index=1)
        members = st.text_input("기본 담당자 ( , 로 구분 )")
        submitted = st.form_submit_button("저장", type="primary")
        if submitted and name:
            pid = to_folder_id(name)
            new = {
                "id": pid, "name": name, "start": start, "end": end,
                "status": status,
                "members": [m.strip() for m in members.split(",") if m.strip()],
            }
            existing = next((p for p in cfg["projects"] if p["id"] == pid), None)
            if existing:
                existing.update(new)
            else:
                cfg["projects"].append(new)
            save_config(cfg)
            st.success(f"'{name}' 저장됨 (폴더 ID: {pid})")
            st.rerun()

# ── 탭3: 대시보드 + 엑셀 내보내기 ────────────────────────────────────────────
with tab_dashboard:
    df = scan_logs(cfg.get("log_root", ""), cfg.get("projects", []))
    if df.empty:
        st.info("기록 루트에 일일 로그(.md)가 쌓이면 여기에 표시됩니다.")
    else:
        proj_filter = st.multiselect(
            "프로젝트 필터", sorted(df["프로젝트"].unique()),
            default=sorted(df["프로젝트"].unique()),
        )
        c1, c2 = st.columns(2)
        d_from = c1.text_input("시작일 (YYYY-MM-DD, 비우면 전체)")
        d_to = c2.text_input("종료일 (YYYY-MM-DD, 비우면 전체)")

        view = df[df["프로젝트"].isin(proj_filter)].copy()
        if d_from:
            view = view[view["날짜"] >= d_from]
        if d_to:
            view = view[view["날짜"] <= d_to]

        # 프로젝트별 최신 카드
        st.subheader("프로젝트 현황")
        cols = st.columns(min(len(proj_filter), 4) or 1)
        for idx, pname in enumerate(proj_filter):
            sub = view[view["프로젝트"] == pname]
            if sub.empty:
                continue
            latest = sub.iloc[-1]
            with cols[idx % len(cols)]:
                st.metric(pname, f"{latest['진행률']}%",
                          f"{latest['상태']} · {latest['날짜']}")

        st.subheader("기록 목록")
        st.dataframe(view, use_container_width=True, hide_index=True)

        # 엑셀 내보내기
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            view.to_excel(writer, index=False, sheet_name="ProjectLogs")
        st.download_button(
            "엑셀로 내보내기 (.xlsx)",
            data=buf.getvalue(),
            file_name=f"project_logs_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
