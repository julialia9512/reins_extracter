# app.py
import re
import io
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import streamlit as st

st.set_page_config(page_title="REINS Extractor", layout="wide")

# =========================
# 共通：クレンジング系
# =========================
def _get_today_yyyymmdd():
    """Returns today's date as YYYYMMDD string"""
    return datetime.now().strftime("%Y%m%d")

def _text_or_none(el):
    if not el:
        return None
    t = " ".join(el.get_text(" ", strip=True).split())
    return t or None

def _clean_price_million_yen(s: str):
    # "10,980万円" -> 10980
    if not s:
        return None
    s = str(s)
    # よくある「万」や「円」混在の吸収
    if "万円" in s:
        s = s.replace("万円", "")
        s = re.sub(r"[^\d.]", "", s)
        return float(s) if s else None
    # 「円」表記なら万円換算
    if "円" in s:
        yen = re.sub(r"[^\d.]", "", s)
        return float(yen) / 10000 if yen else None
    # ただの数字ならそのまま
    s = re.sub(r"[^\d.]", "", s)
    return float(s) if s else None

def _clean_area_sqm(s: str):
    # "82.04㎡" -> 82.04
    if not s:
        return None
    m = re.search(r"([\d.]+)\s*㎡", s)
    if not m:
        m = re.search(r"([\d.]+)", str(s))
    return float(m.group(1)) if m else None

def _clean_tsubo(sqm):
    # 1坪 = 3.305785 m²
    if sqm is None:
        return None
    try:
        return float(sqm) / 3.305785
    except:
        return None

def _clean_minutes(s: str):
    # "徒歩 5 分" / "徒歩　5分" / "5分" -> 5
    if not s:
        return None
    digits = re.sub(r"\D", "", str(s))
    return int(digits) if digits else None

def _clean_yyyymm_from_jp(s: str):
    # "2026年（令和 8年） 2月" -> "2026-02"
    if not s:
        return None
    y = re.search(r"(\d{4})\s*年", s)
    m = re.search(r"(\d{1,2})\s*月", s)
    if y and m:
        return f"{int(y.group(1)):04d}-{int(m.group(1)):02d}"
    return None

def _clean_fee_yen_month(s: str):
    # "1万2,000円/月" -> 12000
    if not s:
        return None
    txt = str(s)
    # 「万」を含む場合
    if "万" in txt:
        # 例: 1.2万円, 1万2,000円
        man = re.search(r"(\d+(?:\.\d+)?)\s*万", txt)
        sen = re.search(r"万\s*([\d,]+)", txt)
        yen = 0.0
        if man:
            yen += float(man.group(1)) * 10000
        if sen:
            yen += float(re.sub(r"[^\d.]", "", sen.group(1)))
        if yen == 0:
            # フォールバック
            nums = re.findall(r"[\d.]+", txt)
            return float("".join(nums)) if nums else None
        return float(yen)
    # 純粋な円表記
    nums = re.sub(r"[^\d.]", "", txt)
    return float(nums) if nums else None

# =========================
# 共通：グリッドテーブル解析
# =========================
_grid_re = {
    "col_range": re.compile(r"grid-column:\s*(\d+)\s*/\s*span\s*(\d+)"),
    "col_start": re.compile(r"grid-column-start:\s*(\d+)"),
    "row_range": re.compile(r"grid-row:\s*(\d+)\s*/\s*span\s*(\d+)"),
    "row_start": re.compile(r"grid-row-start:\s*(\d+)"),
}

def _parse_grid_position(style: str):
    """Returns (row_start, row_end, col_start, col_end) 1-based inclusive."""
    row_start = 1; row_span = 1; col_start = 1; col_span = 1
    style = style or ""
    m = _grid_re["row_range"].search(style)
    if m:
        row_start = int(m.group(1)); row_span = int(m.group(2))
    else:
        m = _grid_re["row_start"].search(style)
        if m:
            row_start = int(m.group(1))
    m = _grid_re["col_range"].search(style)
    if m:
        col_start = int(m.group(1)); col_span = int(m.group(2))
    else:
        m = _grid_re["col_start"].search(style)
        if m:
            col_start = int(m.group(1))
    return (row_start, row_start + row_span - 1, col_start, col_start + col_span - 1)

def _build_header_cells(header_root):
    items = []
    for h in header_root.select(".p-table-header-item"):
        txt = _text_or_none(h)
        r1, r2, c1, c2 = _parse_grid_position(h.get("style", ""))
        items.append({"text": txt, "r1": r1, "r2": r2, "c1": c1, "c2": c2})
    return items

def _label_for_cell(cell_row_start, cell_col_start, header_cells):
    # ヘッダ範囲に含まれる候補から、最も深い（r1が大きい）ものを採用
    candidates = []
    for hd in header_cells:
        if hd["r1"] <= cell_row_start <= hd["r2"] and hd["c1"] <= cell_col_start <= hd["c2"]:
            if hd["text"]:
                candidates.append(hd)
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x["r1"], -(x["c2"] - x["c1"])), reverse=True)
    return candidates[0]["text"]

def _rows_from_grid_table(table_root):
    header_root = table_root.select_one(".p-table-header")
    body_root = table_root.select_one(".p-table-body")
    if not header_root or not body_root:
        return []
    header_cells = _build_header_cells(header_root)
    rows = []
    for row in body_root.select(".p-table-body-row"):
        record = {}
        for td in row.select(".p-table-body-item"):
            r1, _, c1, _ = _parse_grid_position(td.get("style", ""))
            label = _label_for_cell(r1, c1, header_cells)
            val = _text_or_none(td)
            if label:
                record[label] = val  # 後勝ち
        rows.append(record)
    return rows

def _find_table_root(soup):
    # villaは .p-table.small、マンションは .p-table だけのこともある
    table = soup.select_one(".p-table.small")
    if not table:
        table = soup.select_one(".p-table")
    return table

def _find_all_tables(soup):
    """Find all tables and return them with their types (apartment/villa/unknown)"""
    # Find all potential table containers
    all_tables = soup.select(".p-table")
    
    apt_table = None
    villa_table = None
    
    for table in all_tables:
        # Get header cells to determine table type
        header_cells = []
        header_root = table.select_one(".p-table-header")
        if header_root:
            for h in header_root.select(".p-table-header-item"):
                txt = _text_or_none(h)
                if txt:
                    header_cells.append(txt)
        
        # Check if it's a villa table by looking for villa-specific columns
        villa_indicators = ["土地面積", "建物面積", "接道状況", "接道１"]
        apt_indicators = ["専有面積", "建物名", "所在階", "管理費"]
        
        has_villa_cols = any(ind in " ".join(header_cells) for ind in villa_indicators)
        has_apt_cols = any(ind in " ".join(header_cells) for ind in apt_indicators)
        
        if has_villa_cols and not villa_table:
            villa_table = table
        elif has_apt_cols and not apt_table:
            apt_table = table
    
    return apt_table, villa_table

# =========================
# マンション/区分（既存系）
# =========================
APT_COLUMNS = [
    "No.",
    "物件番号",
    "物件種目",
    "専有面積 (㎡)",
    "所在地",
    "取引態様",
    "価格 (万円)",
    "用途地域",
    "㎡単価 (万円/㎡)",
    "建物名",
    "所在階",
    "間取",
    "取引状況",
    "管理費 (円/月)",
    "坪単価 (万円/坪)",
    "沿線駅",
    "交通 (分)",
    "商号",
    "築年月 (YYYY-MM)",
    "電話番号",
    "入力日 (YYYYMMDD)",
]

_APT_ALIASES = {
    "No.": "No.",
    "物件番号": "物件番号",
    "物件種目": "物件種目",
    "専有面積": "専有面積 (㎡)",
    "所在地": "所在地",
    "取引態様": "取引態様",
    "価格": "価格 (万円)",
    "用途地域": "用途地域",
    "㎡単価": "㎡単価 (万円/㎡)",
    "建物名": "建物名",
    "所在階": "所在階",
    "間取": "間取",
    "取引状況": "取引状況",
    "管理費": "管理費 (円/月)",
    "坪単価": "坪単価 (万円/坪)",
    "沿線駅": "沿線駅",
    "交通": "交通 (分)",
    "商号": "商号",
    "築年月": "築年月 (YYYY-MM)",
    "電話番号": "電話番号",
}

def parse_apartment_html_to_df(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    table = _find_table_root(soup)
    if not table:
        return pd.DataFrame(columns=APT_COLUMNS)
    raw_rows = _rows_from_grid_table(table)

    records = []
    for rr in raw_rows:
        rec = {k: None for k in APT_COLUMNS}
        mapped = {}
        for k, v in rr.items():
            key = _APT_ALIASES.get(k)
            if key:
                mapped[key] = v

        # 文字列のまま入れる列
        for key in ["No.","物件番号","物件種目","所在地","取引態様","用途地域",
                    "建物名","所在階","間取","取引状況","沿線駅",
                    "商号","電話番号"]:
            rec[key] = mapped.get(key)

        # 数値/正規化
        rec["価格 (万円)"] = _clean_price_million_yen(mapped.get("価格 (万円)"))
        rec["専有面積 (㎡)"] = _clean_area_sqm(mapped.get("専有面積 (㎡)"))
        rec["交通 (分)"] = _clean_minutes(mapped.get("交通 (分)"))
        rec["築年月 (YYYY-MM)"] = _clean_yyyymm_from_jp(mapped.get("築年月 (YYYY-MM)"))

        # ㎡単価 / 坪単価（テキストに単位混じる想定）
        unit_sqm = mapped.get("㎡単価 (万円/㎡)")
        if unit_sqm:
            rec["㎡単価 (万円/㎡)"] = float(re.sub(r"[^\d.]", "", unit_sqm)) if re.search(r"\d", unit_sqm) else None
        else:
            # 価格 / 専有面積 から逆算（万円/㎡）
            if rec["価格 (万円)"] and rec["専有面積 (㎡)"]:
                rec["㎡単価 (万円/㎡)"] = rec["価格 (万円)"] / rec["専有面積 (㎡)"]

        tsubo = _clean_tsubo(rec["専有面積 (㎡)"])
        unit_tsubo = mapped.get("坪単価 (万円/坪)")
        if unit_tsubo:
            rec["坪単価 (万円/坪)"] = float(re.sub(r"[^\d.]", "", unit_tsubo)) if re.search(r"\d", unit_tsubo) else None
        else:
            if rec["価格 (万円)"] and tsubo:
                rec["坪単価 (万円/坪)"] = rec["価格 (万円)"] / tsubo

        # 管理費
        rec["管理費 (円/月)"] = _clean_fee_yen_month(mapped.get("管理費 (円/月)"))

        # 入力日
        rec["入力日 (YYYYMMDD)"] = _get_today_yyyymmdd()

        records.append(rec)

    df = pd.DataFrame(records, columns=APT_COLUMNS)
    # キャスト
    for num_col in ["No.","価格 (万円)","専有面積 (㎡)","㎡単価 (万円/㎡)","坪単価 (万円/坪)","交通 (分)","管理費 (円/月)"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    return df

# =========================
# 戸建（ヴィラ）
# =========================
VILLA_COLUMNS = [
    "No.",
    "物件番号",
    "物件種目",
    "土地面積 (㎡)",
    "所在地",
    "取引態様",
    "価格 (万円)",
    "用途地域",
    "建物面積 (㎡)",
    "㎡単価 (万円/㎡)",
    "間取",
    "取引状況",
    "接道状況",
    "沿線駅",
    "交通 (分)",
    "接道１",
    "商号",
    "築年月 (YYYY-MM)",
    "電話番号",
    "入力日 (YYYYMMDD)",
]
_VILLA_ALIASES = {
    "No.": "No.",
    "物件番号": "物件番号",
    "物件種目": "物件種目",
    "土地面積": "土地面積 (㎡)",
    "所在地": "所在地",
    "取引態様": "取引態様",
    "価格": "価格 (万円)",
    "用途地域": "用途地域",
    "建物面積": "建物面積 (㎡)",
    "間取": "間取",
    "取引状況": "取引状況",
    "接道状況": "接道状況",
    "沿線駅": "沿線駅",
    "交通": "交通 (分)",
    "接道１": "接道１",
    "商号": "商号",
    "築年月": "築年月 (YYYY-MM)",
    "電話番号": "電話番号",
}

def parse_villa_html_to_df(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, "lxml")
    table = _find_table_root(soup)
    if not table:
        return pd.DataFrame(columns=VILLA_COLUMNS)

    raw_rows = _rows_from_grid_table(table)
    records = []
    for rr in raw_rows:
        rec = {k: None for k in VILLA_COLUMNS}
        mapped = {}
        for k, v in rr.items():
            key = _VILLA_ALIASES.get(k)
            if key:
                mapped[key] = v

        # 文字列のまま
        for key in ["No.","物件番号","物件種目","所在地","取引態様","用途地域",
                    "間取","取引状況","接道状況","沿線駅","接道１","商号","電話番号"]:
            rec[key] = mapped.get(key)

        # 正規化
        rec["価格 (万円)"] = _clean_price_million_yen(mapped.get("価格 (万円)"))
        rec["土地面積 (㎡)"] = _clean_area_sqm(mapped.get("土地面積 (㎡)"))
        rec["建物面積 (㎡)"] = _clean_area_sqm(mapped.get("建物面積 (㎡)"))
        rec["交通 (分)"] = _clean_minutes(mapped.get("交通 (分)"))
        rec["築年月 (YYYY-MM)"] = _clean_yyyymm_from_jp(mapped.get("築年月 (YYYY-MM)"))

        # ㎡単価を計算（価格 / 建物面積）
        if rec["価格 (万円)"] and rec["建物面積 (㎡)"]:
            rec["㎡単価 (万円/㎡)"] = rec["価格 (万円)"] / rec["建物面積 (㎡)"]

        # 入力日
        rec["入力日 (YYYYMMDD)"] = _get_today_yyyymmdd()

        records.append(rec)

    df = pd.DataFrame(records, columns=VILLA_COLUMNS)
    for num_col in ["No.","価格 (万円)","土地面積 (㎡)","建物面積 (㎡)","㎡単価 (万円/㎡)","交通 (分)"]:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")
    return df

# =========================
# UI
# =========================
st.title("不動産テーブル：貼り付け → プレビュー → Excel")

# Initialize session state
if 'tab1_df_apt' not in st.session_state:
    st.session_state.tab1_df_apt = None
if 'tab1_df_vil' not in st.session_state:
    st.session_state.tab1_df_vil = None
if 'tab2_df_apt' not in st.session_state:
    st.session_state.tab2_df_apt = None
if 'tab3_df_vil' not in st.session_state:
    st.session_state.tab3_df_vil = None

tab1, tab2, tab3, tab4 = st.tabs(["WEB全体から抽出", "マンション / 区分", "戸建（ヴィラ）", "一括エクスポート"])

with tab1:
    st.subheader("WEBページ全体から自動抽出")
    st.markdown("**使い方:** ブラウザで対象ページを表示し、右クリック → 「ページのソースを表示」 → 全てをコピーして下記に貼り付け")
    full_html = st.text_area("WEBページ全体のHTMLを貼り付け", height=300, key="full_html")
    if st.button("テーブル抽出・プレビュー"):
        if not full_html.strip():
            st.warning("HTMLを貼り付けてください。")
        else:
            soup = BeautifulSoup(full_html, "lxml")
            apt_table, villa_table = _find_all_tables(soup)
            
            if not apt_table and not villa_table:
                st.error("❌ テーブルが見つかりませんでした。HTMLの構造を確認してください。")
                st.session_state.tab1_df_apt = None
                st.session_state.tab1_df_vil = None
            else:
                # Parse and store in session state
                st.session_state.tab1_df_apt = parse_apartment_html_to_df(str(apt_table)) if apt_table else pd.DataFrame()
                st.session_state.tab1_df_vil = parse_villa_html_to_df(str(villa_table)) if villa_table else pd.DataFrame()
                
                # Show what we found
                info_msg = "✅ 検出されたテーブル: "
                if apt_table:
                    info_msg += "マンション/区分 "
                if villa_table:
                    info_msg += "戸建（ヴィラ）"
                st.success(info_msg)
                st.rerun()
    
    # Display stored data
    if st.session_state.tab1_df_apt is not None or st.session_state.tab1_df_vil is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### マンション/区分データ")
            df_apt = st.session_state.tab1_df_apt
            if df_apt is not None and not df_apt.empty:
                st.success(f"{len(df_apt)}件のデータを抽出しました")
                st.dataframe(df_apt, width='stretch', height=300)
            else:
                st.info("マンション/区分データは見つかりませんでした。")
        
        with col2:
            st.markdown("#### 戸建（ヴィラ）データ")
            df_vil = st.session_state.tab1_df_vil
            if df_vil is not None and not df_vil.empty:
                st.success(f"{len(df_vil)}件のデータを抽出しました")
                st.dataframe(df_vil, width='stretch', height=300)
            else:
                st.info("戸建（ヴィラ）データは見つかりませんでした。")
        
        # Excelダウンロードボタン
        df_apt = st.session_state.tab1_df_apt if st.session_state.tab1_df_apt is not None else pd.DataFrame()
        df_vil = st.session_state.tab1_df_vil if st.session_state.tab1_df_vil is not None else pd.DataFrame()
        
        if not df_apt.empty or not df_vil.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                if not df_apt.empty:
                    df_apt.to_excel(writer, sheet_name="apartments", index=False)
                if not df_vil.empty:
                    df_vil.to_excel(writer, sheet_name="villas", index=False)
            st.download_button(
                label="📥 抽出データをExcelでダウンロード",
                data=buffer.getvalue(),
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

with tab2:
    st.subheader("マンション / 区分（HTMLを貼り付け）")
    apt_html = st.text_area("ここにHTMLを貼り付け", height=240, key="apt_html")
    colp1, colp2 = st.columns(2)
    with colp1:
        if st.button("プレビュー（マンション）"):
            st.session_state.tab2_df_apt = parse_apartment_html_to_df(apt_html)
            st.rerun()
    with colp2:
        if st.button("Excel ダウンロード（マンション）"):
            if st.session_state.tab2_df_apt is None:
                st.session_state.tab2_df_apt = parse_apartment_html_to_df(apt_html)
                st.rerun()
    
    if st.session_state.tab2_df_apt is not None:
        df_apt = st.session_state.tab2_df_apt
        if not df_apt.empty:
            st.dataframe(df_apt, width='stretch')
            
            # Download button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_apt.to_excel(writer, sheet_name="apartments", index=False)
            st.download_button(
                label="apartments.xlsx を保存",
                data=buffer.getvalue(),
                file_name="apartments.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("データが見つかりませんでした。HTMLを確認してください。")

with tab3:
    st.subheader("戸建（ヴィラ）（HTMLを貼り付け）")
    villa_html = st.text_area("ここにHTMLを貼り付け", height=240, key="villa_html")
    colv1, colv2 = st.columns(2)
    with colv1:
        if st.button("プレビュー（戸建）"):
            st.session_state.tab3_df_vil = parse_villa_html_to_df(villa_html)
            st.rerun()
    with colv2:
        if st.button("Excel ダウンロード（戸建）"):
            if st.session_state.tab3_df_vil is None:
                st.session_state.tab3_df_vil = parse_villa_html_to_df(villa_html)
                st.rerun()
    
    if st.session_state.tab3_df_vil is not None:
        df_vil = st.session_state.tab3_df_vil
        if not df_vil.empty:
            st.dataframe(df_vil, width='stretch')
            
            # Download button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                df_vil.to_excel(writer, sheet_name="villas", index=False)
            st.download_button(
                label="villas.xlsx を保存",
                data=buffer.getvalue(),
                file_name="villas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.warning("データが見つかりませんでした。HTMLを確認してください。")

with tab4:
    st.subheader("マンション + 戸建 を1ファイルにまとめて出力")
    apt_html2 = st.text_area("マンションHTML", height=180, key="apt_html_bulk")
    villa_html2 = st.text_area("戸建HTML", height=180, key="villa_html_bulk")
    if st.button("一括Excelダウンロード"):
        df_apt2 = parse_apartment_html_to_df(apt_html2)
        df_vil2 = parse_villa_html_to_df(villa_html2)
        if df_apt2.empty and df_vil2.empty:
            st.warning("どちらのHTMLにもデータが見つかりませんでした。")
        else:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                if not df_apt2.empty:
                    df_apt2.to_excel(writer, sheet_name="apartments", index=False)
                if not df_vil2.empty:
                    df_vil2.to_excel(writer, sheet_name="villas", index=False)
            st.download_button(
                label="export_all.xlsx を保存",
                data=buffer.getvalue(),
                file_name="export_all.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
