import streamlit as st
import json
import os
from datetime import datetime, date
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib
matplotlib.use("Agg")

st.set_page_config(page_title="Hũ Chi Tiêu", page_icon="💰", layout="wide")

# ============================================================
#  CSS
# ============================================================
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.5rem !important; }
        .stMetric { padding: 6px 2px !important; }
        .stMetric label { font-size: 11px !important; }
        .stMetric [data-testid="stMetricValue"] { font-size: 15px !important; }
        .stNumberInput > div > div > input { font-size: 14px !important; }
    }
    div[data-testid="stDataFrame"] { overflow-x: auto; }
    .summary-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px; padding: 16px; text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .summary-card .label { font-size: 13px; color: #666; margin-bottom: 4px; }
    .summary-card .value { font-size: 22px; font-weight: 700; color: #1a1a2e; }
    .green { border-left: 4px solid #38ef7d; }
    .red { border-left: 4px solid #f45c43; }
    .purple { border-left: 4px solid #667eea; }
    .category-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 0; border-bottom: 1px solid #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  DATA
# ============================================================
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


def month_key(dt):
    return dt.strftime("%Y-%m")


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


def new_month():
    return {
        "income": {m: 0 for m in DEFAULT_DATA["members"]},
        "extra_income": {},
        "expenses": {c: 0 for c in DEFAULT_DATA["categories"]}
    }


def load_data():
    path = "family_data.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    data = dict(DEFAULT_DATA)
    data["months"][month_key(date.today())] = new_month()
    return data


def save(data):
    with open("family_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if "data" not in st.session_state:
    st.session_state.data = load_data()
data = st.session_state.data

# ============================================================
#  SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Quản lý")

    # Import / Export
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

    st.download_button("📥 Export JSON",
                       json.dumps(data, ensure_ascii=False, indent=2),
                       file_name="family_data.json", mime="application/json")

    st.divider()

    # Chọn / thêm tháng
    st.markdown("#### 📅 Tháng")
    all_months = sorted(data["months"].keys(), reverse=True)
    selected = st.selectbox("Chọn tháng", all_months,
                            format_func=month_label, label_visibility="collapsed")

    with st.expander("➕ Thêm tháng mới"):
        new_y = st.number_input("Năm", value=date.today().year, min_value=2020, max_value=2030, step=1, key="new_y")
        new_m = st.number_input("Tháng", value=date.today().month, min_value=1, max_value=12, step=1, key="new_m")
        mk_new = f"{new_y}-{new_m:02d}"
        if st.button("Tạo tháng", use_container_width=True, type="primary"):
            if mk_new not in data["months"]:
                data["months"][mk_new] = new_month()
                save(data)
                st.success(f"Đã tạo {month_label(mk_new)}")
                st.rerun()
            else:
                st.warning("Tháng đã tồn tại!")

    if len(all_months) > 1:
        del_month = st.selectbox("Xóa tháng", all_months,
                                 format_func=month_label, key="del_month_sel")
        if st.button("🗑️ Xóa tháng này", type="secondary"):
            if f"confirm_del_{del_month}" not in st.session_state:
                st.session_state[f"confirm_del_{del_month}"] = True
            else:
                del data["months"][del_month]
                save(data)
                del st.session_state[f"confirm_del_{del_month}"]
                st.rerun()

        if st.session_state.get(f"confirm_del_{del_month}"):
            st.warning(f"Xóa {month_label(del_month)}? Nhấn lại để xác nhận.")
            if st.button("Xác nhận xóa", type="primary"):
                del data["months"][del_month]
                save(data)
                del st.session_state[f"confirm_del_{del_month}"]
                st.rerun()

    st.divider()
    st.caption("Hũ Chi Tiêu v1.0")

# ============================================================
#  HEADER
# ============================================================
st.markdown("""
<style>
    .hdr {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 16px 24px; border-radius: 12px; margin-bottom: 16px;
        display: flex; align-items: center; gap: 12px;
    }
    .hdr h1 { color: white; margin: 0; font-size: 20px; font-weight: 600; }
    .hdr .sub { color: rgba(255,255,255,0.8); font-size: 13px; }
</style>
<div class="hdr">
    <div>
        <h1>💰 HŨ CHI TIÊU GIA ĐÌNH</h1>
        <div class="sub"> """ + month_label(selected) + """</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
#  TABS
# ============================================================
tab_inc, tab_exp, tab_bal = st.tabs(["💵 Thu nhập", "🛒 Chi phí", "💰 Tiết kiệm"])

md = data["months"].setdefault(selected, new_month())
total_inc = sum(md["income"].values()) + sum(md.get("extra_income", {}).values())
total_exp = sum(md["expenses"].values())
balance = total_inc - total_exp

# ============================================================
#  TAB 1 — THU NHẬP
# ============================================================
with tab_inc:
    st.subheader("💵 Thu nhập")

    # Thu nhập chính — mỗi người 1 hàng
    for member in data["members"]:
        val = st.number_input(
            f"💼 {member}",
            value=int(md["income"].get(member, 0)),
            min_value=0, step=100000, format="%d",
            key=f"inc_{member}_{selected}",
            help="Thu nhập cố định hàng tháng")
        if val != md["income"].get(member, 0):
            md["income"][member] = val
            save(data)

    st.divider()

    # Thu nhập phát sinh
    st.markdown("#### 📌 Thu nhập phát sinh")
    extra = md.get("extra_income", {})

    with st.form("add_extra", clear_on_submit=True):
        c1, c2 = st.columns([3, 2])
        with c1:
            ex_name = st.text_input("Nguồn", placeholder="VD: Thưởng, bán hàng...")
        with c2:
            ex_amt = st.number_input("Số tiền (VNĐ)", min_value=0, step=100000, format="%d")
        if st.form_submit_button("➕ Thêm", use_container_width=True, type="primary"):
            if ex_name and ex_amt > 0:
                md.setdefault("extra_income", {})[ex_name] = ex_amt
                save(data)
                st.rerun()

    if extra:
        for name, amt in extra.items():
            c1, c2, c3 = st.columns([4, 3, 1])
            c1.write(f"📌 {name}")
            c2.write(f"**{fmt(amt)}**")
            if c3.button("🗑️", key=f"del_ex_{name}_{selected}"):
                del md["extra_income"][name]
                save(data)
                st.rerun()
    else:
        st.caption("Chưa có thu nhập phát sinh")

    st.divider()

    # Tổng kết
    st.markdown(f"""
    <div class="summary-card green">
        <div class="label">TỔNG THU NHẬP</div>
        <div class="value">{fmt(total_inc)}</div>
    </div>
    """, unsafe_allow_html=True)

    # Biểu đồ
    inc_data = {k: v for k, v in md["income"].items() if v > 0}
    extra_data = {k: v for k, v in md.get("extra_income", {}).items() if v > 0}
    all_inc = {**inc_data, **extra_data}
    if all_inc:
        st.divider()
        fig, ax = plt.subplots(figsize=(7, 3.5), dpi=150)
        colors = ["#38ef7d", "#43e97b", "#00f2fe", "#667eea", "#764ba2"]
        bars = ax.bar(list(all_inc.keys()), list(all_inc.values()),
                      color=colors[:len(all_inc)], alpha=0.85, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, all_inc.values()):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height(),
                    fmt_short(val), ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax.set_ylabel("VNĐ")
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

    for cat in data["categories"]:
        val = st.number_input(
            cat,
            value=int(md["expenses"].get(cat, 0)),
            min_value=0, step=100000, format="%d",
            key=f"exp_{cat}_{selected}")
        if val != md["expenses"].get(cat, 0):
            md["expenses"][cat] = val
            save(data)

    st.divider()

    # Tổng kết
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="summary-card red">
            <div class="label">TỔNG CHI TIÊU</div>
            <div class="value">{fmt(total_exp)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="summary-card green">
            <div class="label">THU NHẬP</div>
            <div class="value">{fmt(total_inc)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        cls = "green" if balance >= 0 else "red"
        st.markdown(f"""
        <div class="summary-card {cls}">
            <div class="label">CÒN LẠI</div>
            <div class="value">{fmt(balance)}</div>
        </div>
        """, unsafe_allow_html=True)

    # Biểu đồ chi tiêu
    exp_data = {k: v for k, v in md["expenses"].items() if v > 0}
    if exp_data:
        st.divider()
        sorted_exp = dict(sorted(exp_data.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
        colors = ["#f45c43", "#f093fb", "#667eea", "#4facfe", "#43e97b", "#fa709a"]
        bars = ax.barh(list(sorted_exp.keys()), list(sorted_exp.values()),
                       color=colors[:len(sorted_exp)], alpha=0.85, edgecolor="white", linewidth=0.5)
        max_val = max(sorted_exp.values()) if sorted_exp else 1
        for bar, val in zip(bars, sorted_exp.values()):
            pct = val / total_exp * 100 if total_exp > 0 else 0
            ax.text(bar.get_width() + max_val * 0.01,
                    bar.get_y() + bar.get_height() / 2.,
                    f"{fmt(val)} ({pct:.0f}%)", ha="left", va="center", fontsize=9, fontweight="bold")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: fmt_short(v)))
        ax.set_xlabel("VNĐ")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Pie chart
        fig2, ax2 = plt.subplots(figsize=(5, 5), dpi=150)
        colors2 = ["#f45c43", "#f093fb", "#667eea", "#4facfe", "#43e97b", "#fa709a"]
        wedges, texts, autotexts = ax2.pie(
            sorted_exp.values(), labels=None,
            autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
            colors=colors2[:len(sorted_exp)], startangle=90,
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

    # Summary cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="summary-card green">
            <div class="label">THU NHẬP</div>
            <div class="value">{fmt(total_inc)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="summary-card red">
            <div class="label">CHI TIÊU</div>
            <div class="value">{fmt(total_exp)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        rate = (balance / total_inc * 100) if total_inc > 0 else 0
        cls = "green" if balance >= 0 else "red"
        st.markdown(f"""
        <div class="summary-card purple">
            <div class="label">TIẾT KIỆM ({rate:.1f}%)</div>
            <div class="value">{fmt(balance)}</div>
        </div>
        """, unsafe_allow_html=True)

    sorted_months = sorted(data["months"].keys())
    labels = [month_short(m) for m in sorted_months]

    inc_list, exp_list, bal_list = [], [], []
    for mk in sorted_months:
        m = data["months"][mk]
        inc = sum(m["income"].values()) + sum(m.get("extra_income", {}).values())
        exp = sum(m["expenses"].values())
        inc_list.append(inc)
        exp_list.append(exp)
        bal_list.append(inc - exp)

    # Biểu đồ xu hướng
    st.divider()
    if len(sorted_months) >= 2:
        st.markdown("#### 📈 Xu hướng qua các tháng")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)

        # Bar chart
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

        # Line chart xu hướng
        ax2.plot(labels, bal_list, marker="o", color="#667eea", linewidth=2.5, markersize=6, label="Tiết kiệm")
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
    else:
        fig, ax = plt.subplots(figsize=(5, 3.5), dpi=150)
        if total_inc > 0:
            sizes = [total_exp, balance] if balance > 0 else [total_exp]
            labels_pie = ["Chi tiêu", "Tiết kiệm"] if balance > 0 else ["Chi tiêu"]
            colors_pie = ["#f45c43", "#38ef7d"] if balance > 0 else ["#f45c43"]
            ax.pie(sizes, labels=labels_pie, colors=colors_pie,
                   autopct=lambda p: fmt_short(p / 100 * total_inc),
                   startangle=90, textprops={"fontsize": 10, "fontweight": "bold"})
            ax.set_title("Chi tiêu vs Tiết kiệm", fontsize=12, fontweight="bold")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Bảng lịch sử số dư
    st.divider()
    st.markdown("#### 📋 Lịch sử số dư các tháng")
    rows = []
    cum_balance = 0
    for mk in sorted_months:
        m = data["months"][mk]
        inc = sum(m["income"].values()) + sum(m.get("extra_income", {}).values())
        exp = sum(m["expenses"].values())
        bal = inc - exp
        cum_balance += bal
        rows.append({
            "Tháng": month_short(mk),
            "Thu nhập": fmt(inc),
            "Chi tiêu": fmt(exp),
            "Dư tháng": fmt(bal),
            "Lũy kế": fmt(cum_balance)
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
