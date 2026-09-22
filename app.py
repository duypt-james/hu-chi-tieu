import streamlit as st
import json
import os
import requests
from datetime import datetime, date

st.set_page_config(page_title="Hũ Chi Tiêu", page_icon="favicon.ico", layout="wide")

# ============================================================
#  PWA META + CSS
# ============================================================
st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Hũ Chi Tiêu">
<link rel="apple-touch-icon" href="icon.png">
<meta name="theme-color" content="#667eea">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.5rem !important; }
        .stMetric { padding: 6px 2px !important; }
        .stMetric label { font-size: 11px !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 15px !important; }
        .stNumberInput > div > div > input { font-size: 14px !important; }
        .stColumns > div { padding: 0 2px !important; }
    }
    div[data-testid="stDataFrame"] { overflow-x: auto; }
    .summary-card {
        border-radius: 12px; padding: 14px 16px; text-align: center;
        border: 1px solid rgba(0,0,0,0.06);
    }
    .card-green { background: linear-gradient(135deg, #e8f5e9, #c8e6c9); border-left: 4px solid #38ef7d; }
    .card-red { background: linear-gradient(135deg, #fce4ec, #f8bbd0); border-left: 4px solid #f45c43; }
    .card-purple { background: linear-gradient(135deg, #ede7f6, #d1c4e9); border-left: 4px solid #667eea; }
    .card-gray { background: linear-gradient(135deg, #f5f7fa, #c3cfe2); border-left: 4px solid #90a4ae; }
    .summary-card .label { font-size: 11px; color: #666; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px; }
    .summary-card .value { font-size: 20px; font-weight: 700; color: #1a1a2e; }
    .summary-card .sub { font-size: 11px; color: #888; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  DATA LAYER — GitHub Gist
# ============================================================
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

GIST_FILENAME = "hu_chitieu_data.json"

DEFAULT_DATA = {
    "members": ["Duy", "Hà"],
    "categories": [
        "Cơm nước", "DV chung cư", "Điện nước",
        "Giáo dục + y tế", "Bỉm sửa + bánh kẹo", "Khác"
    ],
    "months": {}
}


def fmt(v):
    return f"{abs(v):,.0f}".replace(",", ".") + "đ"


def fmt_short(v):
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    elif abs(v) >= 1_000:
        return f"{v / 1_000:.0f}K"
    return str(v)


def fmt_delta(v):
    sign = "+" if v >= 0 else ""
    return f"{sign}{fmt_short(v)}"


def month_label(mk):
    try:
        return datetime.strptime(mk, "%Y-%m").strftime("Tháng %m/%Y")
    except:
        return mk


def month_short(mk):
    try:
        return datetime.strptime(mk, "%Y-%m").strftime("%m/%Y")
    except:
        return mk


def prev_month_key(mk):
    dt = datetime.strptime(mk, "%Y-%m")
    return f"{dt.year - 1}-12" if dt.month == 1 else f"{dt.year}-{dt.month - 1:02d}"


def new_month(copy_from=None):
    if copy_from:
        return json.loads(json.dumps(copy_from))
    return {
        "income": {m: 0 for m in DEFAULT_DATA["members"]},
        "extra_income": {},
        "expenses": {c: 0 for c in DEFAULT_DATA["categories"]},
        "notes": ""
    }


def calc_month_total(m):
    inc = sum(m["income"].values()) + sum(m.get("extra_income", {}).values())
    exp = sum(m["expenses"].values())
    return inc, exp, inc - exp


def get_gist_config():
    token = st.secrets.get("GITHUB_TOKEN", "")
    gist_id = st.secrets.get("GIST_ID", "")
    return token, gist_id


def load_data():
    token, gist_id = get_gist_config()

    # Try loading from Gist
    if token and gist_id:
        try:
            headers = {"Authorization": f"token {token}"}
            resp = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                gist = resp.json()
                if GIST_FILENAME in gist.get("files", {}):
                    content = gist["files"][GIST_FILENAME]["content"]
                    d = json.loads(content)
                    for mk in d.get("months", {}):
                        d["months"][mk].setdefault("notes", "")
                        d["months"][mk].setdefault("extra_income", {})
                    return d
        except Exception as e:
            st.warning(f"Không đọc được Gist: {e}")

    # Fallback: local file
    path = "family_data.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        for mk in d.get("months", {}):
            d["months"][mk].setdefault("notes", "")
            d["months"][mk].setdefault("extra_income", {})
        return d

    data = dict(DEFAULT_DATA)
    data["months"][datetime.today().strftime("%Y-%m")] = new_month()
    return data


def save(data):
    token, gist_id = get_gist_config()
    content = json.dumps(data, ensure_ascii=False, indent=2)

    # Save to Gist
    if token and gist_id:
        try:
            headers = {"Authorization": f"token {token}", "Content-Type": "application/json"}
            payload = {"files": {GIST_FILENAME: {"content": content}}}
            resp = requests.patch(f"https://api.github.com/gists/{gist_id}",
                                  headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                return
        except Exception as e:
            st.warning(f"Lưu Gist thất bại: {e}")

    # Fallback: local file
    with open("family_data.json", "w", encoding="utf-8") as f:
        f.write(content)


if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Quản lý")

    st.download_button("📥 Export JSON",
                       json.dumps(data, ensure_ascii=False, indent=2),
                       file_name="family_data.json", mime="application/json")

    uploaded = st.file_uploader("Import JSON", type=["json"])
    if uploaded:
        try:
            imported = json.load(uploaded)
            if "months" in imported:
                st.session_state.data = imported
                data = imported
                save(data)
                st.success("Import thành công!")
                st.rerun()
            else:
                st.error("File không hợp lệ!")
        except Exception as e:
            st.error(f"Lỗi: {e}")

    st.divider()
    st.markdown("#### 📅 Chọn tháng")
    all_months = sorted(data["months"].keys(), reverse=True)
    selected = st.selectbox("Tháng", all_months,
                            format_func=month_label, label_visibility="collapsed",
                            key="month_select")

    with st.expander("➕ Thêm tháng mới"):
        new_y = st.number_input("Năm", value=date.today().year,
                                min_value=2020, max_value=2030, step=1, key="new_y")
        new_m = st.number_input("Tháng", value=date.today().month,
                                min_value=1, max_value=12, step=1, key="new_m")
        mk_new = f"{new_y}-{new_m:02d}"
        copy_prev = st.checkbox("Copy dữ liệu tháng trước", value=True, key="copy_prev")
        if st.button("Tạo tháng", use_container_width=True, type="primary"):
            if mk_new not in data["months"]:
                if copy_prev and all_months:
                    prev = prev_month_key(mk_new)
                    if prev in data["months"]:
                        data["months"][mk_new] = new_month(copy_from=data["months"][prev])
                    else:
                        data["months"][mk_new] = new_month()
                else:
                    data["months"][mk_new] = new_month()
                save(data)
                st.success(f"Đã tạo {month_label(mk_new)}")
                st.rerun()
            else:
                st.warning("Tháng đã tồn tại!")

    if len(all_months) > 1:
        with st.expander("🗑️ Xóa tháng"):
            del_sel = st.selectbox("Chọn tháng xóa", all_months,
                                   format_func=month_label, key="del_month_sel")
            del_key = f"confirm_del_{del_sel}"
            if st.button("Xóa", key="del_btn"):
                st.session_state[del_key] = True
            if st.session_state.get(del_key):
                st.warning(f"Xác nhận xóa {month_label(del_sel)}?")
                c1, c2 = st.columns(2)
                if c1.button("✅ Có, xóa", type="primary", key="yes_del"):
                    del data["months"][del_sel]
                    save(data)
                    del st.session_state[del_key]
                    st.rerun()
                if c2.button("❌ Hủy", key="no_del"):
                    del st.session_state[del_key]
                    st.rerun()

    st.divider()
    token, gist_id = get_gist_config()
    if token and gist_id:
        st.caption("☁️ Đang dùng GitHub Gist")
    else:
        st.caption("💾 Đang dùng file local")
    st.caption("Hũ Chi Tiêu v1.0")

# ============================================================
#  HEADER
# ============================================================
md = data["months"].setdefault(selected, new_month())
total_inc, total_exp, balance = calc_month_total(md)

prev_mk = prev_month_key(selected)
prev_data = data["months"].get(prev_mk)
prev_inc, prev_exp, prev_bal = (0, 0, 0)
if prev_data:
    prev_inc, prev_exp, prev_bal = calc_month_total(prev_data)

delta_inc = total_inc - prev_inc
delta_exp = total_exp - prev_exp
delta_bal = balance - prev_bal

st.markdown(f"""
<style>
    .hdr {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 16px 20px; border-radius: 12px; margin-bottom: 12px;
    }}
    .hdr h1 {{ color: white; margin: 0; font-size: 20px; font-weight: 600; }}
    .hdr .sub {{ color: rgba(255,255,255,0.75); font-size: 13px; margin-top: 2px; }}
</style>
<div class="hdr">
    <div>
        <h1>💰 HŨ CHI TIÊU GIA ĐÌNH</h1>
        <div class="sub">{month_label(selected)} — Dư: {fmt(balance)}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
#  TABS
# ============================================================
tab_inc, tab_exp, tab_bal = st.tabs(["💵 Thu nhập", "🛒 Chi phí", "💰 Tiết kiệm"])

# ============================================================
#  TAB 1 — THU NHẬP
# ============================================================
with tab_inc:
    st.subheader("💵 Thu nhập")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="summary-card card-green">
            <div class="label">Tổng thu nhập</div>
            <div class="value">{fmt(total_inc)}</div>
            <div class="sub">{fmt_delta(delta_inc)} so tháng trước</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="summary-card card-gray">
            <div class="label">Chi tiêu</div>
            <div class="value">{fmt(total_exp)}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="summary-card {'card-green' if balance >= 0 else 'card-red'}">
            <div class="label">Tiết kiệm</div>
            <div class="value">{fmt(balance)}</div>
            <div class="sub">{fmt_delta(delta_bal)} so tháng trước</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown("**Thu nhập cố định**")
    for member in data["members"]:
        val = st.number_input(
            f"💼 {member}",
            value=int(md["income"].get(member, 0)),
            min_value=0, step=100000, format="%d",
            key=f"inc_{member}_{selected}")
        if val != md["income"].get(member, 0):
            md["income"][member] = val
            save(data)

    st.divider()
    st.markdown("**Thu nhập phát sinh**")
    extra = md.get("extra_income", {})

    with st.form("add_extra", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            ex_name = st.text_input("Nguồn", placeholder="Thưởng, lãi, bán hàng...")
        with c2:
            ex_amt = st.number_input("Số tiền", min_value=0, step=100000, format="%d")
        if st.form_submit_button("➕ Thêm", use_container_width=True, type="primary"):
            if ex_name and ex_amt > 0:
                md.setdefault("extra_income", {})[ex_name] = ex_amt
                save(data)
                st.rerun()

    if extra:
        for name, amt in extra.items():
            c1, c2, c3 = st.columns([5, 3, 1])
            c1.write(f"📌 {name}")
            c2.write(f"**{fmt(amt)}**")
            if c3.button("🗑️", key=f"del_ex_{name}_{selected}"):
                del md["extra_income"][name]
                save(data)
                st.rerun()
    else:
        st.caption("Chưa có thu nhập phát sinh")

    inc_data = {k: v for k, v in md["income"].items() if v > 0}
    extra_data = {k: v for k, v in md.get("extra_income", {}).items() if v > 0}
    all_inc = {**inc_data, **extra_data}
    if all_inc:
        st.divider()
        fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)
        colors = ["#38ef7d", "#43e97b", "#00f2fe", "#667eea", "#764ba2"]
        bars = ax.bar(list(all_inc.keys()), list(all_inc.values()),
                      color=colors[:len(all_inc)], alpha=0.85, edgecolor="white")
        for bar, val in zip(bars, all_inc.values()):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                    fmt_short(val), ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

# ============================================================
#  TAB 2 — CHI PHÍ
# ============================================================
with tab_exp:
    st.subheader("🛒 Chi tiêu")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="summary-card card-red">
            <div class="label">Tổng chi tiêu</div>
            <div class="value">{fmt(total_exp)}</div>
            <div class="sub">{fmt_delta(delta_exp)} so tháng trước</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="summary-card card-green">
            <div class="label">Thu nhập</div>
            <div class="value">{fmt(total_inc)}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="summary-card {'card-green' if balance >= 0 else 'card-red'}">
            <div class="label">Còn lại</div>
            <div class="value">{fmt(balance)}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    for cat in data["categories"]:
        val = st.number_input(
            cat,
            value=int(md["expenses"].get(cat, 0)),
            min_value=0, step=100000, format="%d",
            key=f"exp_{cat}_{selected}")
        if val != md["expenses"].get(cat, 0):
            md["expenses"][cat] = val
            save(data)

    exp_data = {k: v for k, v in md["expenses"].items() if v > 0}
    if exp_data:
        st.divider()
        sorted_exp = dict(sorted(exp_data.items(), key=lambda x: x[1], reverse=True))

        fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
        colors = ["#f45c43", "#f093fb", "#667eea", "#4facfe", "#43e97b", "#fa709a"]
        bars = ax.barh(list(sorted_exp.keys()), list(sorted_exp.values()),
                       color=colors[:len(sorted_exp)], alpha=0.85, edgecolor="white")
        max_val = max(sorted_exp.values()) if sorted_exp else 1
        for bar, val in zip(bars, sorted_exp.values()):
            pct = val / total_exp * 100 if total_exp > 0 else 0
            ax.text(bar.get_width() + max_val * 0.01,
                    bar.get_y() + bar.get_height() / 2.,
                    f"{fmt(val)} ({pct:.0f}%)", ha="left", va="center", fontsize=9, fontweight="bold")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        fig2, ax2 = plt.subplots(figsize=(5, 5), dpi=150)
        wedges, texts, autotexts = ax2.pie(
            sorted_exp.values(), labels=None,
            autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
            colors=colors[:len(sorted_exp)], startangle=90,
            pctdistance=0.8, wedgeprops=dict(width=0.5, edgecolor="white"))
        for t in autotexts:
            t.set_fontsize(9)
            t.set_fontweight("bold")
        ax2.legend(sorted_exp.keys(), loc="center left", bbox_to_anchor=(1, 0.5), fontsize=10)
        ax2.set_title("Phân bổ chi tiêu", fontsize=13, fontweight="bold", pad=10)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

# ============================================================
#  TAB 3 — TIẾT KIỆM
# ============================================================
with tab_bal:
    st.subheader("💰 Tiết kiệm")

    rate = (balance / total_inc * 100) if total_inc > 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="summary-card card-green">
            <div class="label">Thu nhập</div>
            <div class="value">{fmt(total_inc)}</div>
            <div class="sub">{fmt_delta(delta_inc)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="summary-card card-red">
            <div class="label">Chi tiêu</div>
            <div class="value">{fmt(total_exp)}</div>
            <div class="sub">{fmt_delta(delta_exp)}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="summary-card card-purple">
            <div class="label">Tiết kiệm ({rate:.1f}%)</div>
            <div class="value">{fmt(balance)}</div>
            <div class="sub">{fmt_delta(delta_bal)}</div>
        </div>""", unsafe_allow_html=True)

    with st.expander("📝 Ghi chú tháng này", expanded=False):
        notes = st.text_area("Ghi chú", value=md.get("notes", ""),
                             key=f"notes_{selected}", height=80,
                             placeholder="Ghi chú chi tiêu tháng này...")
        if notes != md.get("notes", ""):
            md["notes"] = notes
            save(data)

    sorted_months = sorted(data["months"].keys())
    labels = [month_short(m) for m in sorted_months]
    inc_list, exp_list, bal_list = [], [], []
    for mk in sorted_months:
        m = data["months"][mk]
        inc, exp, bal = calc_month_total(m)
        inc_list.append(inc)
        exp_list.append(exp)
        bal_list.append(bal)

    st.divider()
    if len(sorted_months) >= 2:
        st.markdown("#### 📈 Xu hướng")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)

        x = range(len(labels))
        w = 0.25
        ax1.bar([i - w for i in x], inc_list, width=w, label="Thu nhập", color="#38ef7d", alpha=0.85)
        ax1.bar(x, exp_list, width=w, label="Chi tiêu", color="#f45c43", alpha=0.85)
        ax1.bar([i + w for i in x], bal_list, width=w, label="Tiết kiệm", color="#667eea", alpha=0.85)
        ax1.set_xticks(list(x))
        ax1.set_xticklabels(labels, rotation=45, fontsize=9)
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax1.legend(fontsize=9)
        ax1.set_title("So sánh thu - chi - tiết kiệm", fontsize=12, fontweight="bold")
        ax1.spines["top"].set_visible(False)
        ax1.spines["right"].set_visible(False)
        ax1.grid(axis="y", alpha=0.3)

        ax2.plot(labels, bal_list, marker="o", color="#667eea", linewidth=2.5, markersize=6)
        ax2.fill_between(labels, bal_list, alpha=0.15, color="#667eea")
        for i, v in enumerate(bal_list):
            ax2.annotate(fmt_short(v), (labels[i], v), textcoords="offset points",
                         xytext=(0, 10), ha="center", fontsize=8, fontweight="bold",
                         color="#38ef7d" if v >= 0 else "#f45c43")
        ax2.axhline(y=0, color="#999", linewidth=0.8, linestyle="--")
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax2.set_title("Xu hướng tiết kiệm", fontsize=12, fontweight="bold")
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.markdown("#### 📊 Chi tiêu theo nhóm")
        cat_data = {c: [] for c in data["categories"]}
        for mk in sorted_months:
            m = data["months"][mk]
            for c in data["categories"]:
                cat_data[c].append(m["expenses"].get(c, 0))
        active_cats = [c for c in data["categories"] if any(v > 0 for v in cat_data[c])]
        if active_cats:
            fig, ax = plt.subplots(figsize=(10, 4.5), dpi=150)
            x = range(len(labels))
            colors = ["#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe", "#00f2fe", "#43e97b", "#fa709a"]
            bottom = [0] * len(labels)
            for i, cat in enumerate(active_cats):
                vals = cat_data[cat]
                ax.bar(x, vals, bottom=bottom, label=cat, color=colors[i % len(colors)], alpha=0.85)
                bottom = [b + v for b, v in zip(bottom, vals)]
            ax.set_xticks(list(x))
            ax.set_xticklabels(labels, rotation=45, fontsize=9)
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
            ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1, 1))
            ax.set_title("Chi tiêu tích lũy theo nhóm", fontsize=12, fontweight="bold")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    else:
        if total_inc > 0:
            fig, ax = plt.subplots(figsize=(5, 3.5), dpi=150)
            sizes = [total_exp, max(balance, 0)] if balance > 0 else [total_exp]
            labels_pie = ["Chi tiêu", "Tiết kiệm"] if balance > 0 else ["Chi tiêu"]
            colors_pie = ["#f45c43", "#38ef7d"] if balance > 0 else ["#f45c43"]
            ax.pie(sizes, labels=labels_pie, colors=colors_pie,
                   autopct=lambda p: fmt_short(p / 100 * total_inc),
                   startangle=90, textprops={"fontsize": 10, "fontweight": "bold"})
            ax.set_title("Chi tiêu vs Tiết kiệm", fontsize=12, fontweight="bold")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    st.divider()
    st.markdown("#### 📋 Lịch sử số dư")
    rows = []
    cum = 0
    for i, mk in enumerate(sorted_months):
        m = data["months"][mk]
        inc, exp, bal = calc_month_total(m)
        cum += bal
        prev_b = bal_list[i - 1] if i > 0 else 0
        chg = bal - prev_b if i > 0 else 0
        notes_txt = m.get("notes", "")
        if notes_txt and len(notes_txt) > 30:
            notes_txt = notes_txt[:30] + "..."
        rows.append({
            "Tháng": month_short(mk),
            "Thu nhập": fmt(inc),
            "Chi tiêu": fmt(exp),
            "Dư": fmt(bal),
            "Thay đổi": fmt(chg) if i > 0 else "--",
            "Lũy kế": fmt(cum),
            "Ghi chú": notes_txt
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
