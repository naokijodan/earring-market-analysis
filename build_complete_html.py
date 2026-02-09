#!/usr/bin/env python3
"""イヤリング市場分析HTML完全版生成スクリプト v3 - 全面改善版"""

import pandas as pd
import json
from collections import defaultdict
import re
from datetime import datetime
import numpy as np

# 設定
SHIPPING_JPY = 2700
EXCHANGE_RATE = 155
FEE_RATE = 0.20

# 日英キーワードマッピング
TYPE_KEYWORDS = {
    'Stud': {'en': 'stud earrings', 'jp': 'スタッズ ピアス'},
    'Hoop': {'en': 'hoop earrings', 'jp': 'フープ ピアス'},
    'Drop/Dangle': {'en': 'drop dangle earrings', 'jp': 'ドロップ イヤリング'},
    'Clip-on': {'en': 'clip on earrings', 'jp': 'クリップ イヤリング'},
    'Huggie': {'en': 'huggie earrings', 'jp': 'ハギー ピアス'},
    'Threader': {'en': 'threader earrings', 'jp': 'スレッダー ピアス'},
    'Ear Cuff': {'en': 'ear cuff', 'jp': 'イヤーカフ'},
    'Leverback': {'en': 'leverback earrings', 'jp': 'レバーバック ピアス'},
    'Chandelier': {'en': 'chandelier earrings', 'jp': 'シャンデリア イヤリング'},
    'Other': {'en': 'earrings', 'jp': 'イヤリング'},
}

# ブランド日本語マッピング
BRAND_JP = {
    'CHANEL': 'シャネル',
    'GUCCI': 'グッチ',
    'DIOR': 'ディオール',
    'HERMES': 'エルメス',
    'LOUIS VUITTON': 'ルイヴィトン',
    'TIFFANY': 'ティファニー',
    'TIFFANY & CO.': 'ティファニー',
    'CARTIER': 'カルティエ',
    'BVLGARI': 'ブルガリ',
    'PRADA': 'プラダ',
    'FENDI': 'フェンディ',
    'CELINE': 'セリーヌ',
    'VALENTINO': 'ヴァレンティノ',
    'BALENCIAGA': 'バレンシアガ',
    'SALVATORE FERRAGAMO': 'フェラガモ',
    'Salvatore Ferragamo': 'フェラガモ',
    'MIKIMOTO': 'ミキモト',
    'Vivienne Westwood': 'ヴィヴィアン ウエストウッド',
    'SWAROVSKI': 'スワロフスキー',
    'GIVENCHY': 'ジバンシー',
    'VERSACE': 'ヴェルサーチ',
    'SAINT LAURENT': 'サンローラン',
    'Georg Jensen': 'ジョージジェンセン',
    'Georg Jensen Living': 'ジョージジェンセン',
    'POKEMON': 'ポケモン',
    'A BATHING APE': 'ア ベイシング エイプ',
}

# CSVファイル読み込み
df = pd.read_csv('/Users/naokijodan/Desktop/イヤリング市場データ_sheet8_2026-02-07.csv')

print(f"=== データ読み込み完了 ===")
print(f"総件数: {len(df)}")

# 販売数を数値に変換
df['販売数'] = pd.to_numeric(df['販売数'], errors='coerce').fillna(1).astype(int)
df['売上'] = df['価格'] * df['販売数']

total_sales = int(df['販売数'].sum())
total_revenue = float(df['売上'].sum())

period_start = df['販売日'].min()
period_end = df['販売日'].max()

df['販売日_dt'] = pd.to_datetime(df['販売日'], errors='coerce')
df['販売月'] = df['販売日_dt'].dt.to_period('M').astype(str)

# アイテムタイプ分類
def extract_item_type(title):
    title_upper = str(title).upper()
    if 'STUD' in title_upper:
        return 'Stud'
    if 'HOOP' in title_upper:
        return 'Hoop'
    if 'DROP' in title_upper or 'DANGLE' in title_upper:
        return 'Drop/Dangle'
    if 'CLIP' in title_upper:
        return 'Clip-on'
    if 'HUGGIE' in title_upper:
        return 'Huggie'
    if 'THREADER' in title_upper:
        return 'Threader'
    if 'CUFF' in title_upper:
        return 'Ear Cuff'
    if 'LEVERBACK' in title_upper:
        return 'Leverback'
    if 'CHANDELIER' in title_upper:
        return 'Chandelier'
    return 'Other'

df['アイテムタイプ'] = df['タイトル'].apply(extract_item_type)

# ブランドカテゴリ分類
HIGH_BRANDS = ['CHANEL', 'DIOR', 'LOUIS VUITTON', 'GUCCI', 'HERMES', 'PRADA', 'FENDI', 'CELINE',
               'TIFFANY', 'CARTIER', 'BVLGARI', 'VALENTINO', 'BOTTEGA', 'BALENCIAGA',
               'SALVATORE FERRAGAMO', 'FERRAGAMO', 'MIKIMOTO', 'POMELLATO', 'SAINT LAURENT', 'VERSACE']
DESIGNER_BRANDS = ['Vivienne Westwood', 'A BATHING APE', 'GIVENCHY', 'LANVIN', 'MARC JACOBS',
                   'TOM BINNS', 'Chrome Hearts', 'AGATHA', 'SWAROVSKI', 'Georg Jensen']
CHARACTER_BRANDS = ['POKEMON', 'SANRIO', 'DISNEY']

ALL_BRANDS = HIGH_BRANDS + DESIGNER_BRANDS + CHARACTER_BRANDS

def detect_brand_from_title(row):
    brand = row['ブランド']
    title = str(row['タイトル']).upper()
    if pd.isna(brand) or brand == '(不明)' or brand == '':
        if 'VIVIENNE' in title or 'WESTWOOD' in title:
            return 'Vivienne Westwood'
        if 'POKEMON' in title or 'POKÉMON' in title:
            return 'POKEMON'
        if 'TIFFANY' in title:
            return 'TIFFANY'
        if 'SWAROVSKI' in title:
            return 'SWAROVSKI'
        if 'GEORG JENSEN' in title:
            return 'Georg Jensen'
        for b in ALL_BRANDS:
            if b.upper() in title:
                return b
    return brand

df['ブランド'] = df.apply(detect_brand_from_title, axis=1)

def categorize_brand(brand):
    if pd.isna(brand) or brand == '(不明)' or brand == '':
        return 'ノーブランド'
    brand_upper = str(brand).upper()
    for hb in HIGH_BRANDS:
        if hb.upper() in brand_upper:
            return 'ハイブランド'
    for db in DESIGNER_BRANDS:
        if db.upper() in brand_upper:
            return 'デザイナー'
    for cb in CHARACTER_BRANDS:
        if cb.upper() in brand_upper:
            return 'キャラクター'
    return 'その他'

df['ブランドカテゴリ'] = df['ブランド'].apply(categorize_brand)

# まとめ売り判定（詳細分析用）
def analyze_bulk(title):
    title_upper = str(title).upper()
    # セット数を抽出
    match = re.search(r'(\d+)\s*(PCS|PIECES|PAIRS?|SET)', title_upper)
    if match:
        count = int(match.group(1))
        if count >= 10:
            return '10個以上'
        elif count >= 5:
            return '5-9個'
        elif count >= 2:
            return '2-4個'

    bulk_keywords = ['LOT', 'BULK', 'SET OF', 'BUNDLE', 'COLLECTION', 'まとめ', 'セット']
    for kw in bulk_keywords:
        if kw in title_upper:
            return 'セット（個数不明）'
    return None

df['まとめ売り詳細'] = df['タイトル'].apply(analyze_bulk)
df['まとめ売り'] = df['まとめ売り詳細'].notna()

# ノベルティ判定
def is_novelty(title):
    novelty_keywords = ['NOVELTY', 'GWP', 'LIMITED', 'NOT FOR SALE', '非売品', 'RARE', 'VIP', 'GIFT']
    title_upper = str(title).upper()
    for kw in novelty_keywords:
        if kw in title_upper:
            return True
    return False

df['ノベルティ'] = df['タイトル'].apply(is_novelty)

# 箱あり判定
def has_box(title):
    title_upper = str(title).upper()
    return 'W/BOX' in title_upper or 'WITH BOX' in title_upper or 'BOX' in title_upper

df['箱あり'] = df['タイトル'].apply(has_box)

# 仕入れ上限計算
df['仕入れ上限'] = df['価格'] * EXCHANGE_RATE * (1 - FEE_RATE) - SHIPPING_JPY

# ブランド別統計
def get_brand_stats(brand_df):
    if len(brand_df) == 0:
        return {'count': 0, 'sales': 0, 'revenue': 0, 'avg_price': 0, 'median_price': 0,
                'min_price': 0, 'max_price': 0, 'cv': 0, 'purchase_limit': 0}
    sales = int(brand_df['販売数'].sum())
    prices = brand_df['価格']
    return {
        'count': len(brand_df),
        'sales': sales,
        'revenue': float(brand_df['売上'].sum()),
        'avg_price': float(prices.mean()),
        'median_price': float(prices.median()),
        'min_price': float(prices.min()),
        'max_price': float(prices.max()),
        'cv': float(prices.std() / prices.mean()) if prices.mean() > 0 else 0,
        'purchase_limit': float(brand_df['仕入れ上限'].median())
    }

def get_stability(cv):
    if cv <= 0.3:
        return '★★★'
    elif cv <= 0.5:
        return '★★☆'
    elif cv <= 0.7:
        return '★☆☆'
    else:
        return '☆☆☆'

def calc_novelty_premium(brand_df):
    novelty = brand_df[brand_df['ノベルティ'] == True]
    regular = brand_df[brand_df['ノベルティ'] == False]
    if len(novelty) < 2 or len(regular) < 2:
        return 0.0
    return float((novelty['価格'].median() - regular['価格'].median()) / regular['価格'].median() * 100) if regular['価格'].median() > 0 else 0.0

def calc_box_premium(brand_df):
    with_box = brand_df[brand_df['箱あり'] == True]
    without_box = brand_df[brand_df['箱あり'] == False]
    if len(with_box) < 2 or len(without_box) < 2:
        return 0.0
    return float((with_box['価格'].median() - without_box['価格'].median()) / without_box['価格'].median() * 100) if without_box['価格'].median() > 0 else 0.0

def get_price_distribution(prices):
    bins = [0, 50, 100, 150, 200, 250, 300, 400, 500, 750, 1000, float('inf')]
    labels = ['$0-49', '$50-99', '$100-149', '$150-199', '$200-249', '$250-299',
              '$300-399', '$400-499', '$500-749', '$750-999', '$1000+']
    distribution = pd.cut(prices, bins=bins, labels=labels).value_counts().sort_index()
    return {str(k): int(v) for k, v in distribution.items()}

# 検索リンク生成関数
def gen_ebay_link(brand, item_type=None):
    brand_search = brand.replace(' ', '+')
    if item_type and item_type in TYPE_KEYWORDS:
        type_en = TYPE_KEYWORDS[item_type]['en'].replace(' ', '+')
        return f"https://www.ebay.com/sch/i.html?_nkw={brand_search}+{type_en}&LH_Sold=1&LH_Complete=1"
    return f"https://www.ebay.com/sch/i.html?_nkw={brand_search}+earrings&LH_Sold=1&LH_Complete=1"

def gen_mercari_link(brand, item_type=None):
    brand_jp = BRAND_JP.get(brand, brand)
    if item_type and item_type in TYPE_KEYWORDS:
        type_jp = TYPE_KEYWORDS[item_type]['jp']
        return f"https://jp.mercari.com/search?keyword={brand_jp}%20{type_jp}&status=on_sale"
    return f"https://jp.mercari.com/search?keyword={brand_jp}%20イヤリング&status=on_sale"

# 検索リンク行生成（チェックボックス付き）
def gen_search_links(brand, item_type=None, row_id=''):
    ebay_url = gen_ebay_link(brand, item_type)
    mercari_url = gen_mercari_link(brand, item_type)
    return f'''
        <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
        <input type="checkbox" class="search-checkbox" data-id="{row_id}_ebay">
        <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
        <input type="checkbox" class="search-checkbox" data-id="{row_id}_mercari">
    '''

# ブランド別統計リスト
brand_stats_list = []
for brand in df['ブランド'].dropna().unique():
    if brand == '' or brand == '(不明)':
        continue
    brand_df = df[df['ブランド'] == brand]
    stats = get_brand_stats(brand_df)
    stats['brand'] = brand
    stats['category'] = categorize_brand(brand)
    brand_stats_list.append(stats)
brand_stats_list.sort(key=lambda x: x['sales'], reverse=True)
top20_brands = brand_stats_list[:20]

overall_stats = get_brand_stats(df)

# アイテムタイプ別統計
item_type_stats = {}
for item_type in df['アイテムタイプ'].unique():
    type_df = df[df['アイテムタイプ'] == item_type]
    item_type_stats[item_type] = get_brand_stats(type_df)

# ブランドカテゴリ別統計
brand_cat_stats = {}
for cat in df['ブランドカテゴリ'].unique():
    cat_df = df[df['ブランドカテゴリ'] == cat]
    brand_cat_stats[cat] = {
        'sales': int(cat_df['販売数'].sum()),
        'revenue': float(cat_df['売上'].sum())
    }

# 月別データ
monthly_sales = df.groupby(['販売月', 'アイテムタイプ'])['販売数'].sum().unstack(fill_value=0)
price_dist = get_price_distribution(df['価格'])

print(f"\n=== トップ20ブランド ===")
for i, b in enumerate(top20_brands, 1):
    print(f"  {i}. {b['brand']} ({b['sales']}件)")

# HTML生成開始
html_parts = []

# CSSスタイル
css = '''
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-card: #ffffff;
    --text-primary: #333333;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --accent: #6366f1;
    --positive: #10b981;
    --negative: #ef4444;
}
[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-card: #0f3460;
    --text-primary: #eee;
    --text-secondary: #aaa;
    --border-color: #3a3a5c;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
}
.header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    padding: 30px 20px;
    text-align: center;
    position: relative;
}
.header h1 { font-size: 2em; margin-bottom: 10px; }
.header p { opacity: 0.9; font-size: 0.9em; }
.theme-toggle {
    position: absolute;
    top: 20px;
    right: 20px;
}
.theme-toggle button {
    padding: 10px 20px;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    color: white;
    border-radius: 20px;
    cursor: pointer;
}
.controls {
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    padding: 15px 20px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    align-items: center;
}
.control-group {
    display: flex;
    align-items: center;
    gap: 8px;
}
.control-group label { font-size: 0.85em; color: var(--text-secondary); }
.control-group input {
    width: 80px;
    padding: 6px 10px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-card);
    color: var(--text-primary);
}
.btn {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85em;
    transition: all 0.2s;
}
.btn-primary { background: var(--accent); color: white; }
.btn-secondary { background: var(--bg-card); color: var(--text-primary); border: 1px solid var(--border-color); }
.tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    padding: 10px 20px;
    background: var(--bg-secondary);
    border-bottom: 2px solid var(--border-color);
    overflow-x: auto;
}
.tab {
    padding: 8px 12px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 4px;
    font-size: 0.8em;
    transition: all 0.2s;
    white-space: nowrap;
}
.tab:hover { background: var(--bg-card); }
.tab.active { background: var(--accent); color: white; }
.tab-content {
    display: none;
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
}
.tab-content.active { display: block; }
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    border-left: 4px solid var(--accent);
}
.stat-card .icon { font-size: 1.3em; margin-bottom: 5px; }
.stat-card .value {
    font-size: 1.5em;
    font-weight: bold;
    color: var(--accent);
    margin: 8px 0;
}
.stat-card .label { font-size: 0.8em; color: var(--text-secondary); }
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
}
.table-container {
    overflow-x: auto;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    margin-bottom: 20px;
}
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8em;
}
th, td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
th {
    background: var(--bg-secondary);
    font-weight: 600;
    position: sticky;
    top: 0;
}
tr:hover { background: rgba(99, 102, 241, 0.05); }
.link-btn {
    display: inline-block;
    padding: 3px 6px;
    margin: 1px;
    font-size: 0.7em;
    border-radius: 3px;
    text-decoration: none;
    color: white;
}
.link-ebay { background: #0064d2; }
.link-mercari { background: #ff0211; }
.search-checkbox {
    width: 14px;
    height: 14px;
    margin: 0 4px;
    cursor: pointer;
    vertical-align: middle;
}
.highlight { color: var(--positive); font-weight: bold; }
.section-title {
    font-size: 1.3em;
    color: var(--accent);
    margin: 25px 0 15px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border-color);
}
.insight-box {
    background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
    border-left: 4px solid var(--positive);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.insight-box h3 { color: var(--positive); margin-bottom: 10px; }
.insight-box ul { list-style: none; padding: 0; }
.insight-box li { padding: 6px 0; border-bottom: 1px dashed var(--border-color); }
.strategy-box {
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    border-left: 5px solid #0284c7;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
[data-theme="dark"] .strategy-box {
    background: linear-gradient(135deg, #0f172a, #1e293b);
}
.strategy-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
}
.strategy-card {
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid;
}
.strategy-card.good { background: #e8f5e9; border-color: #4caf50; }
.strategy-card.bad { background: #fff3e0; border-color: #ff9800; }
.strategy-card.price { background: #f3e5f5; border-color: #9c27b0; }
[data-theme="dark"] .strategy-card.good { background: #1b5e20; }
[data-theme="dark"] .strategy-card.bad { background: #e65100; }
[data-theme="dark"] .strategy-card.price { background: #4a148c; }
.strategy-card h4 { margin-bottom: 10px; font-size: 0.95em; }
.strategy-card ul { margin-left: 18px; font-size: 0.85em; }
.checked-row { opacity: 0.4; text-decoration: line-through; }
.brand-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    margin: 20px 0;
}
.brand-chart-container {
    background: var(--bg-card);
    padding: 15px;
    border-radius: 10px;
    border: 1px solid var(--border-color);
}
.brand-chart-container h4 {
    margin-bottom: 10px;
    font-size: 13px;
    color: var(--accent);
}
@media (max-width: 768px) {
    .chart-grid { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .brand-grid { grid-template-columns: 1fr; }
    .strategy-grid { grid-template-columns: 1fr; }
}

/* ブランド固有カラー */
#CHANEL .stat-card { border-top: 3px solid #000000; }
#GUCCI .stat-card { border-top: 3px solid #006341; }
#DIOR .stat-card { border-top: 3px solid #000000; }
#HERMES .stat-card { border-top: 3px solid #FF6600; }
#LOUIS_VUITTON .stat-card { border-top: 3px solid #8B4513; }
#TIFFANY .stat-card { border-top: 3px solid #0abab5; }
#Vivienne_Westwood .stat-card { border-top: 3px solid #6B0B5A; }
#SWAROVSKI .stat-card { border-top: 3px solid #2196f3; }
#PRADA .stat-card { border-top: 3px solid #000000; }
#FENDI .stat-card { border-top: 3px solid #f7db00; }
#CELINE .stat-card { border-top: 3px solid #c4a77d; }
#VALENTINO .stat-card { border-top: 3px solid #c41e3a; }
'''

# グラフ用データ準備
item_type_labels = list(item_type_stats.keys())
item_type_sales = [item_type_stats[k]['sales'] for k in item_type_labels]

brand_cat_labels = list(brand_cat_stats.keys())
brand_cat_sales = [brand_cat_stats[k]['sales'] for k in brand_cat_labels]

top20_brand_labels = [s['brand'][:12] for s in top20_brands]
top20_brand_sales = [s['sales'] for s in top20_brands]

price_dist_labels = list(price_dist.keys())
price_dist_values = list(price_dist.values())

monthly_labels = monthly_sales.index.tolist()[-12:] if len(monthly_sales) > 12 else monthly_sales.index.tolist()
monthly_data = {}
for col in monthly_sales.columns:
    monthly_data[col] = monthly_sales[col].tail(12).tolist()

# Top20ブランドのタブID生成
top20_brand_tabs = []
for stats in top20_brands:
    brand = stats['brand']
    tab_id = brand.replace(' ', '_').replace('&', '').replace('.', '')
    top20_brand_tabs.append((brand, tab_id))

# HTML開始
html_parts.append(f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>イヤリング市場分析（完全版）</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
{css}
    </style>
</head>
<body>
    <div class="header">
        <div class="theme-toggle">
            <button onclick="toggleTheme()" id="themeBtn">🌙 ダークモード</button>
        </div>
        <h1>💎 イヤリング市場分析（完全版）</h1>
        <p>データ期間: {period_start} ~ {period_end} | 生成: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 総件数: {len(df)}件</p>
    </div>

    <div class="controls">
        <div class="control-group">
            <label>💱 為替:</label>
            <input type="number" id="exchangeRate" value="{EXCHANGE_RATE}" step="0.1">
            <button class="btn btn-secondary" onclick="updateExchangeRate()">🔄</button>
        </div>
        <div class="control-group">
            <label>📦 送料:</label>
            <input type="number" id="shippingCost" value="{SHIPPING_JPY}" step="100">円
        </div>
        <div class="control-group">
            <label>💰 手数料:</label>
            <input type="number" id="feeRate" value="{int(FEE_RATE * 100)}" step="1">%
        </div>
        <button class="btn btn-primary" onclick="recalculate()">🔄 再計算</button>
    </div>

    <div class="tabs">
        <button class="tab active" onclick="showTab('overview')">📊 全体分析</button>
        <button class="tab" onclick="showTab('brands')">🏷️ ブランド一覧</button>
        <button class="tab" onclick="showTab('stud')">💎 Stud</button>
        <button class="tab" onclick="showTab('hoop')">⭕ Hoop</button>
        <button class="tab" onclick="showTab('drop')">💧 Drop</button>
        <button class="tab" onclick="showTab('clipon')">📎 Clip-on</button>
        <button class="tab" onclick="showTab('novelty')">🎁 ノベルティ</button>
        <button class="tab" onclick="showTab('bundle')">📦 まとめ売り</button>
        <button class="tab" onclick="showTab('recommend')">⭐ おすすめ</button>
''')

# Top20ブランドタブを追加
for brand, tab_id in top20_brand_tabs:
    short_name = brand[:10] if len(brand) > 10 else brand
    html_parts.append(f'        <button class="tab" onclick="showTab(\'{tab_id}\')">{short_name}</button>\n')

html_parts.append('    </div>\n')

# 全体分析タブ
html_parts.append(f'''
    <div id="overview" class="tab-content active">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">総販売数</div>
                <div class="value">{total_sales:,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">総売上</div>
                <div class="value">${total_revenue:,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">平均価格</div>
                <div class="value">${overall_stats["avg_price"]:.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${overall_stats["median_price"]:.0f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>💡 市場インサイト</h3>
            <ul>
                <li>🔝 <strong>ハイブランドが市場の{brand_cat_stats.get("ハイブランド", {}).get("sales", 0) / total_sales * 100:.0f}%</strong>を占める（{brand_cat_stats.get("ハイブランド", {}).get("sales", 0):,}件）</li>
                <li>💎 <strong>シャネルが独占</strong>: {top20_brands[0]['sales']:,}件で圧倒的シェア</li>
                <li>🎁 <strong>ノベルティ</strong>: {int(df['ノベルティ'].sum())}件 / <strong>まとめ売り</strong>: {int(df['まとめ売り'].sum())}件</li>
            </ul>
        </div>

        <h2 class="section-title">📊 カテゴリ別分析</h2>
        <div class="chart-grid">
            <div class="chart-container"><div id="itemTypeBarChart" style="height:350px;"></div></div>
            <div class="chart-container"><div id="brandCatPieChart" style="height:350px;"></div></div>
        </div>

        <h2 class="section-title">🏷️ ブランド別分析（Top20）</h2>
        <div class="chart-grid">
            <div class="chart-container"><div id="brandBarChart" style="height:450px;"></div></div>
            <div class="chart-container"><div id="brandPieChart" style="height:450px;"></div></div>
        </div>

        <h2 class="section-title">💰 価格帯分布</h2>
        <div class="chart-container"><div id="priceDistChart" style="height:300px;"></div></div>

        <h2 class="section-title">📅 月別販売数推移</h2>
        <div class="chart-container"><div id="monthlyTrendChart" style="height:300px;"></div></div>

        <h2 class="section-title">🏷️ ブランド別詳細（Top20）</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>最低</th>
                        <th>最高</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV</th>
                        <th>安定度</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for i, stats in enumerate(top20_brands):
    brand = stats['brand']
    stability = get_stability(stats['cv'])
    row_id = f"overview_{brand.replace(' ', '_')}"
    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand}</strong></td>
                        <td>{stats["sales"]:,}</td>
                        <td>${stats["min_price"]:.0f}</td>
                        <td>${stats["max_price"]:.0f}</td>
                        <td class="highlight">${stats["median_price"]:.0f}</td>
                        <td data-usd="{stats['median_price']:.2f}">¥{int(stats["purchase_limit"]):,}</td>
                        <td>{stats["cv"]:.2f}</td>
                        <td>{stability}</td>
                        <td>{gen_search_links(brand, None, row_id)}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ブランド一覧タブ
html_parts.append('''
    <div id="brands" class="tab-content">
        <h2 class="section-title">🏷️ ブランド別販売実績（全ブランド）</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>カテゴリ</th>
                        <th>販売数</th>
                        <th>売上</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV</th>
                        <th>安定度</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for i, stats in enumerate(brand_stats_list[:50]):
    brand = stats['brand']
    stability = get_stability(stats['cv'])
    row_id = f"brands_{brand.replace(' ', '_')}_{i}"
    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand}</strong></td>
                        <td>{stats['category']}</td>
                        <td>{stats['sales']:,}</td>
                        <td>${stats['revenue']:,.0f}</td>
                        <td class="highlight">${stats['median_price']:.0f}</td>
                        <td data-usd="{stats['median_price']:.2f}">¥{int(stats['purchase_limit']):,}</td>
                        <td>{stats['cv']:.2f}</td>
                        <td>{stability}</td>
                        <td>{gen_search_links(brand, None, row_id)}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# アイテムタイプ別タブ生成
for item_type, tab_id in [('Stud', 'stud'), ('Hoop', 'hoop'), ('Drop/Dangle', 'drop'), ('Clip-on', 'clipon')]:
    type_df = df[df['アイテムタイプ'] == item_type]
    if len(type_df) == 0:
        continue
    type_stats = get_brand_stats(type_df)

    type_brand_stats = []
    for brand in type_df['ブランド'].dropna().unique():
        if brand == '' or brand == '(不明)':
            continue
        b_df = type_df[type_df['ブランド'] == brand]
        b_stats = get_brand_stats(b_df)
        b_stats['brand'] = brand
        type_brand_stats.append(b_stats)
    type_brand_stats.sort(key=lambda x: x['sales'], reverse=True)

    type_en = TYPE_KEYWORDS.get(item_type, {}).get('en', 'earrings')
    type_jp = TYPE_KEYWORDS.get(item_type, {}).get('jp', 'イヤリング')

    html_parts.append(f'''
    <div id="{tab_id}" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">販売数</div>
                <div class="value">{type_stats['sales']:,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">売上</div>
                <div class="value">${type_stats['revenue']:,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${type_stats['median_price']:.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">仕入上限</div>
                <div class="value" data-usd="{type_stats['median_price']:.2f}">¥{int(type_stats['purchase_limit']):,}</div>
            </div>
        </div>

        <h2 class="section-title">🏷️ {item_type} ブランド別詳細</h2>
        <p style="margin-bottom:15px;color:var(--text-secondary);">検索キーワード: <strong>{type_en}</strong> / <strong>{type_jp}</strong></p>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV</th>
                        <th>安定度</th>
                        <th>検索（タイプ込み）</th>
                    </tr>
                </thead>
                <tbody>
''')

    for j, b_stats in enumerate(type_brand_stats[:25]):
        brand = b_stats['brand']
        stability = get_stability(b_stats['cv'])
        row_id = f"{tab_id}_{brand.replace(' ', '_')}_{j}"
        html_parts.append(f'''
                    <tr>
                        <td><strong>{brand}</strong></td>
                        <td>{b_stats['sales']:,}</td>
                        <td class="highlight">${b_stats['median_price']:.0f}</td>
                        <td data-usd="{b_stats['median_price']:.2f}">¥{int(b_stats['purchase_limit']):,}</td>
                        <td>{b_stats['cv']:.2f}</td>
                        <td>{stability}</td>
                        <td>{gen_search_links(brand, item_type, row_id)}</td>
                    </tr>
''')

    html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ノベルティタブ（詳細分析）
novelty_df = df[df['ノベルティ'] == True]
novelty_stats = get_brand_stats(novelty_df) if len(novelty_df) > 0 else {'sales': 0, 'median_price': 0, 'revenue': 0}

# ノベルティのブランド別統計
novelty_brand_stats = []
for brand in novelty_df['ブランド'].dropna().unique():
    if brand == '' or brand == '(不明)':
        continue
    b_df = novelty_df[novelty_df['ブランド'] == brand]
    b_stats = get_brand_stats(b_df)
    b_stats['brand'] = brand
    novelty_brand_stats.append(b_stats)
novelty_brand_stats.sort(key=lambda x: x['sales'], reverse=True)

# ノベルティの価格帯分布
novelty_price_dist = get_price_distribution(novelty_df['価格']) if len(novelty_df) > 0 else {}

html_parts.append(f'''
    <div id="novelty" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">🎁</div>
                <div class="label">ノベルティ件数</div>
                <div class="value">{len(novelty_df):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">総販売数</div>
                <div class="value">{novelty_stats.get('sales', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">総売上</div>
                <div class="value">${novelty_stats.get('revenue', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${novelty_stats.get('median_price', 0):.0f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>🎁 ノベルティ市場の特徴</h3>
            <ul>
                <li>💎 仕入れルート: 百貨店購入特典、ビューティーカウンター、VIPイベント</li>
                <li>🏷️ キーワード: NOVELTY, GWP, LIMITED, VIP, GIFT, NOT FOR SALE</li>
                <li>📈 CHANELノベルティが最も取引量が多い</li>
            </ul>
        </div>

        <h2 class="section-title">🏷️ ブランド別ノベルティ分析</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>件数</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for i, b_stats in enumerate(novelty_brand_stats[:15]):
    brand = b_stats['brand']
    row_id = f"novelty_{brand.replace(' ', '_')}_{i}"
    brand_jp = BRAND_JP.get(brand, brand)
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand.replace(' ', '+')}+novelty+earrings&LH_Sold=1&LH_Complete=1"
    mercari_url = f"https://jp.mercari.com/search?keyword={brand_jp}%20ノベルティ%20イヤリング&status=on_sale"
    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand}</strong></td>
                        <td>{b_stats['count']}</td>
                        <td>{b_stats['sales']}</td>
                        <td class="highlight">${b_stats['median_price']:.0f}</td>
                        <td data-usd="{b_stats['median_price']:.2f}">¥{int(b_stats['purchase_limit']):,}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <input type="checkbox" class="search-checkbox" data-id="{row_id}_ebay">
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                            <input type="checkbox" class="search-checkbox" data-id="{row_id}_mercari">
                        </td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>

        <h2 class="section-title">📌 ノベルティ人気商品 Top15</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>商品名</th>
                        <th>販売数</th>
                        <th>価格</th>
                        <th>仕入上限</th>
                    </tr>
                </thead>
                <tbody>
''')

novelty_top = novelty_df.nlargest(15, '販売数')[['ブランド', 'タイトル', '価格', '販売数', '仕入れ上限']].to_dict('records')
for i, item in enumerate(novelty_top):
    title = str(item['タイトル'])[:50] + '...' if len(str(item['タイトル'])) > 50 else str(item['タイトル'])
    brand = item['ブランド'] if pd.notna(item['ブランド']) else 'N/A'
    html_parts.append(f'''
                    <tr>
                        <td>{brand}</td>
                        <td>{title}</td>
                        <td>{item['販売数']}</td>
                        <td class="highlight">${item['価格']:.0f}</td>
                        <td data-usd="{item['価格']:.2f}">¥{int(item['仕入れ上限']):,}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# まとめ売りタブ（詳細分析）
bundle_df = df[df['まとめ売り'] == True]
bundle_stats = get_brand_stats(bundle_df) if len(bundle_df) > 0 else {'sales': 0, 'median_price': 0, 'revenue': 0}

# セット内容別統計
bundle_type_stats = bundle_df.groupby('まとめ売り詳細').agg({
    'タイトル': 'count',
    '販売数': 'sum',
    '価格': 'median'
}).reset_index()
bundle_type_stats.columns = ['タイプ', '件数', '販売数', '中央値']
bundle_type_stats = bundle_type_stats.sort_values('販売数', ascending=False)

# まとめ売りのブランド別統計
bundle_brand_stats = []
for brand in bundle_df['ブランド'].dropna().unique():
    if brand == '' or brand == '(不明)':
        continue
    b_df = bundle_df[bundle_df['ブランド'] == brand]
    b_stats = get_brand_stats(b_df)
    b_stats['brand'] = brand
    bundle_brand_stats.append(b_stats)
bundle_brand_stats.sort(key=lambda x: x['sales'], reverse=True)

html_parts.append(f'''
    <div id="bundle" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">まとめ売り件数</div>
                <div class="value">{len(bundle_df):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">総販売数</div>
                <div class="value">{bundle_stats.get('sales', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">総売上</div>
                <div class="value">${bundle_stats.get('revenue', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${bundle_stats.get('median_price', 0):.0f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>📦 まとめ売り市場の特徴</h3>
            <ul>
                <li>⚠️ 単価分析には不向き（平均価格が歪む）</li>
                <li>💎 ブランド品のセットは希少性あり</li>
                <li>📉 ノーブランドのまとめ売りは利益率低め</li>
            </ul>
        </div>

        <h2 class="section-title">📊 セット内容別分析</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>セットタイプ</th>
                        <th>件数</th>
                        <th>販売数</th>
                        <th>中央値</th>
                    </tr>
                </thead>
                <tbody>
''')

for _, row in bundle_type_stats.iterrows():
    html_parts.append(f'''
                    <tr>
                        <td><strong>{row['タイプ']}</strong></td>
                        <td>{row['件数']}</td>
                        <td>{row['販売数']}</td>
                        <td class="highlight">${row['中央値']:.0f}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>

        <h2 class="section-title">🏷️ ブランド別まとめ売り分析</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>件数</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for i, b_stats in enumerate(bundle_brand_stats[:15]):
    brand = b_stats['brand']
    row_id = f"bundle_{brand.replace(' ', '_')}_{i}"
    brand_jp = BRAND_JP.get(brand, brand)
    ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={brand.replace(' ', '+')}+earrings+lot&LH_Sold=1&LH_Complete=1"
    mercari_url = f"https://jp.mercari.com/search?keyword={brand_jp}%20イヤリング%20まとめ&status=on_sale"
    html_parts.append(f'''
                    <tr>
                        <td><strong>{brand}</strong></td>
                        <td>{b_stats['count']}</td>
                        <td>{b_stats['sales']}</td>
                        <td class="highlight">${b_stats['median_price']:.0f}</td>
                        <td>
                            <a href="{ebay_url}" target="_blank" class="link-btn link-ebay">eBay</a>
                            <input type="checkbox" class="search-checkbox" data-id="{row_id}_ebay">
                            <a href="{mercari_url}" target="_blank" class="link-btn link-mercari">メルカリ</a>
                            <input type="checkbox" class="search-checkbox" data-id="{row_id}_mercari">
                        </td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>

        <h2 class="section-title">📌 まとめ売り人気商品 Top15</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>商品名</th>
                        <th>販売数</th>
                        <th>価格</th>
                    </tr>
                </thead>
                <tbody>
''')

bundle_top = bundle_df.nlargest(15, '販売数')[['ブランド', 'タイトル', '価格', '販売数']].to_dict('records')
for item in bundle_top:
    title = str(item['タイトル'])[:50] + '...' if len(str(item['タイトル'])) > 50 else str(item['タイトル'])
    brand = item['ブランド'] if pd.notna(item['ブランド']) else 'N/A'
    html_parts.append(f'''
                    <tr>
                        <td>{brand}</td>
                        <td>{title}</td>
                        <td>{item['販売数']}</td>
                        <td class="highlight">${item['価格']:.0f}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# おすすめ出品順序タブ
for stats in brand_stats_list:
    stats['score'] = stats['sales'] * stats['median_price']
brand_stats_list.sort(key=lambda x: x['score'], reverse=True)

html_parts.append('''
    <div id="recommend" class="tab-content">
        <h2 class="section-title">⭐ おすすめ出品順序 TOP20</h2>
        <p style="margin-bottom:15px;color:var(--text-secondary);">スコア = 販売数 × 中央値</p>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>スコア</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

for i, stats in enumerate(brand_stats_list[:20]):
    brand = stats['brand']
    row_id = f"rec_{brand.replace(' ', '_')}_{i}"
    rank_style = ''
    if i == 0:
        rank_style = 'style="color: gold; font-weight: bold;"'
    elif i == 1:
        rank_style = 'style="color: silver; font-weight: bold;"'
    elif i == 2:
        rank_style = 'style="color: #cd7f32; font-weight: bold;"'

    html_parts.append(f'''
                    <tr>
                        <td {rank_style}>{i + 1}</td>
                        <td><strong>{brand}</strong></td>
                        <td>{stats['sales']:,}</td>
                        <td class="highlight">${stats['median_price']:.0f}</td>
                        <td data-usd="{stats['median_price']:.2f}">¥{int(stats['purchase_limit']):,}</td>
                        <td>{stats['score']:,.0f}</td>
                        <td>{gen_search_links(brand, None, row_id)}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ブランド個別タブ生成（Top20）
brand_price_data = {}

for brand, tab_id in top20_brand_tabs:
    # ブランドデータ抽出
    if 'Vivienne' in brand:
        brand_df = df[df['ブランド'].str.contains('Vivienne', case=False, na=False)].copy()
    elif 'TIFFANY' in brand:
        brand_df = df[df['ブランド'].str.contains('TIFFANY', case=False, na=False)].copy()
    elif 'Georg Jensen' in brand:
        brand_df = df[df['ブランド'].str.contains('Georg Jensen', case=False, na=False)].copy()
    else:
        brand_df = df[df['ブランド'].str.upper() == brand.upper()].copy()

    if len(brand_df) == 0:
        continue

    b_stats = get_brand_stats(brand_df)
    novelty_premium = calc_novelty_premium(brand_df)
    box_premium = calc_box_premium(brand_df)
    novelty_count = int(brand_df['ノベルティ'].sum())
    bulk_count = int(brand_df['まとめ売り'].sum())
    brand_jp = BRAND_JP.get(brand, brand)

    # アイテムタイプ別統計
    item_stats = []
    for item_type in brand_df['アイテムタイプ'].unique():
        type_df = brand_df[brand_df['アイテムタイプ'] == item_type]
        if len(type_df) > 0:
            type_stats = get_brand_stats(type_df)
            type_stats['type'] = item_type
            item_stats.append(type_stats)
    item_stats.sort(key=lambda x: x['sales'], reverse=True)

    # 人気商品Top15
    top_items = brand_df.nlargest(15, '販売数')[['タイトル', '価格', '販売数', '仕入れ上限', 'アイテムタイプ']].to_dict('records')

    # グラフ用データ
    brand_price_dist = get_price_distribution(brand_df['価格'])
    item_dist = brand_df['アイテムタイプ'].value_counts().to_dict()
    brand_price_data[tab_id] = {
        'price_labels': list(brand_price_dist.keys()),
        'price_values': list(brand_price_dist.values()),
        'item_labels': list(item_dist.keys()),
        'item_values': list(item_dist.values())
    }

    html_parts.append(f'''
    <div id="{tab_id}" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">総販売数</div>
                <div class="value">{b_stats['sales']:,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">総売上</div>
                <div class="value">${b_stats['revenue']:,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${b_stats['median_price']:.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">CV値</div>
                <div class="value">{b_stats['cv']:.2f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">🎁</div>
                <div class="label">ノベルティ</div>
                <div class="value">{novelty_count}件</div>
            </div>
        </div>

        <div class="strategy-box">
            <h3>🎯 {brand} 仕入れ戦略</h3>
            <div class="strategy-grid">
                <div class="strategy-card good">
                    <h4>✅ 狙い目条件</h4>
                    <ul>
                        <li>箱・保証書付き（{box_premium:+.0f}%）</li>
                        <li>ノベルティ（{novelty_premium:+.0f}%）</li>
                        <li>人気: {", ".join([s["type"] for s in item_stats[:2]])}</li>
                    </ul>
                </div>
                <div class="strategy-card bad">
                    <h4>⚠️ 避けるべき</h4>
                    <ul>
                        <li>まとめ売り（{bulk_count}件）</li>
                        <li>状態不明・説明曖昧</li>
                        <li>偽物リスク高い格安品</li>
                    </ul>
                </div>
                <div class="strategy-card price">
                    <h4>💰 仕入れ目安</h4>
                    <p>通常: ¥{int(b_stats['purchase_limit']):,}以下</p>
                    <p>上限: ${b_stats['median_price']:.0f}前後</p>
                </div>
            </div>
        </div>

        <h3 class="section-title">📊 市場分析</h3>
        <div class="brand-grid">
            <div class="brand-chart-container">
                <h4>価格帯別分析</h4>
                <div id="{tab_id}_price_chart" style="height: 280px;"></div>
            </div>
            <div class="brand-chart-container">
                <h4>アイテムタイプ別</h4>
                <div id="{tab_id}_item_chart" style="height: 280px;"></div>
            </div>
        </div>

        <h3 class="section-title">📋 アイテムタイプ別詳細</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>タイプ</th>
                        <th>販売数</th>
                        <th>比率</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV</th>
                        <th>検索（タイプ込み）</th>
                    </tr>
                </thead>
                <tbody>
''')

    for k, type_stats in enumerate(item_stats):
        ratio = type_stats['sales'] / b_stats['sales'] * 100 if b_stats['sales'] > 0 else 0
        stability = get_stability(type_stats['cv'])
        row_id = f"{tab_id}_type_{type_stats['type'].replace('/', '_')}_{k}"
        html_parts.append(f'''
                    <tr>
                        <td><strong>{type_stats["type"]}</strong></td>
                        <td>{type_stats["sales"]}</td>
                        <td>{ratio:.1f}%</td>
                        <td class="highlight">${type_stats["median_price"]:.0f}</td>
                        <td data-usd="{type_stats['median_price']:.2f}">¥{int(type_stats["purchase_limit"]):,}</td>
                        <td>{type_stats["cv"]:.2f}</td>
                        <td>{gen_search_links(brand, type_stats['type'], row_id)}</td>
                    </tr>
''')

    html_parts.append(f'''
                </tbody>
            </table>
        </div>

        <h3 class="section-title">📌 人気商品 Top15</h3>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>商品名</th>
                        <th>タイプ</th>
                        <th>販売数</th>
                        <th>価格</th>
                        <th>仕入上限</th>
                        <th>検索</th>
                    </tr>
                </thead>
                <tbody>
''')

    for k, item in enumerate(top_items, 1):
        title = str(item['タイトル'])[:45] + '...' if len(str(item['タイトル'])) > 45 else str(item['タイトル'])
        item_type = item['アイテムタイプ']
        row_id = f"{tab_id}_top_{k}"
        html_parts.append(f'''
                    <tr>
                        <td><strong>{k}</strong></td>
                        <td>{title}</td>
                        <td>{item_type}</td>
                        <td>{item["販売数"]}</td>
                        <td class="highlight">${item["価格"]:.0f}</td>
                        <td data-usd="{item['価格']:.2f}">¥{int(item["仕入れ上限"]):,}</td>
                        <td>{gen_search_links(brand, item_type, row_id)}</td>
                    </tr>
''')

    html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# JavaScript
monthly_traces = []
for item_type, values in monthly_data.items():
    monthly_traces.append({
        'x': monthly_labels,
        'y': values,
        'name': item_type,
        'type': 'scatter',
        'mode': 'lines+markers'
    })

html_parts.append(f'''
    <script>
        function toggleTheme() {{
            const body = document.body;
            const btn = document.getElementById('themeBtn');
            if (body.getAttribute('data-theme') === 'dark') {{
                body.removeAttribute('data-theme');
                btn.textContent = '🌙 ダークモード';
                localStorage.setItem('theme', 'light');
            }} else {{
                body.setAttribute('data-theme', 'dark');
                btn.textContent = '☀️ ライトモード';
                localStorage.setItem('theme', 'dark');
            }}
        }}

        if (localStorage.getItem('theme') === 'dark') {{
            document.body.setAttribute('data-theme', 'dark');
            document.getElementById('themeBtn').textContent = '☀️ ライトモード';
        }}

        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}

        async function updateExchangeRate() {{
            try {{
                const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
                const data = await response.json();
                const rate = data.rates.JPY;
                document.getElementById('exchangeRate').value = rate.toFixed(2);
                recalculate();
                alert('為替更新: 1USD = ' + rate.toFixed(2) + '円');
            }} catch (error) {{
                alert('為替取得に失敗');
            }}
        }}

        function recalculate() {{
            const rate = parseFloat(document.getElementById('exchangeRate').value);
            const shipping = parseFloat(document.getElementById('shippingCost').value);
            const feeRate = parseFloat(document.getElementById('feeRate').value) / 100;

            document.querySelectorAll('[data-usd]').forEach(cell => {{
                const usd = parseFloat(cell.getAttribute('data-usd'));
                const limit = Math.floor(usd * rate * (1 - feeRate) - shipping);
                cell.textContent = '¥' + limit.toLocaleString();
            }});
        }}

        function initCheckboxes() {{
            const saved = JSON.parse(localStorage.getItem('earringChecks') || '{{}}');
            document.querySelectorAll('.search-checkbox').forEach(checkbox => {{
                const id = checkbox.dataset.id;
                if (saved[id]) {{
                    checkbox.checked = true;
                    const row = checkbox.closest('tr');
                    if (row) row.classList.add('checked-row');
                }}
                checkbox.addEventListener('change', function() {{
                    const row = this.closest('tr');
                    if (this.checked) {{
                        saved[id] = true;
                    }} else {{
                        delete saved[id];
                    }}
                    // 同じ行の両方がチェックされたらグレーアウト
                    if (row) {{
                        const checkboxes = row.querySelectorAll('.search-checkbox');
                        const allChecked = Array.from(checkboxes).every(cb => cb.checked);
                        if (allChecked) {{
                            row.classList.add('checked-row');
                        }} else {{
                            row.classList.remove('checked-row');
                        }}
                    }}
                    localStorage.setItem('earringChecks', JSON.stringify(saved));
                }});
            }});
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            initCheckboxes();

            const layout = {{
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: {{ color: '#333', size: 11 }},
                margin: {{ t: 30, r: 20, b: 50, l: 50 }}
            }};

            Plotly.newPlot('itemTypeBarChart', [{{
                x: {json.dumps(item_type_labels)},
                y: {json.dumps(item_type_sales)},
                type: 'bar',
                marker: {{ color: '#6366f1' }}
            }}], {{...layout, title: 'アイテムタイプ別販売数'}});

            Plotly.newPlot('brandCatPieChart', [{{
                labels: {json.dumps(brand_cat_labels)},
                values: {json.dumps(brand_cat_sales)},
                type: 'pie',
                hole: 0.4
            }}], {{...layout, title: 'ブランドカテゴリ別'}});

            Plotly.newPlot('brandBarChart', [{{
                y: {json.dumps(top20_brand_labels)},
                x: {json.dumps(top20_brand_sales)},
                type: 'bar',
                orientation: 'h',
                marker: {{ color: '#8b5cf6' }}
            }}], {{...layout, title: 'ブランド別販売数 Top20', margin: {{ l: 100 }}}});

            Plotly.newPlot('brandPieChart', [{{
                labels: {json.dumps(top20_brand_labels[:10])},
                values: {json.dumps(top20_brand_sales[:10])},
                type: 'pie',
                hole: 0.4
            }}], {{...layout, title: 'ブランド別シェア Top10'}});

            Plotly.newPlot('priceDistChart', [{{
                x: {json.dumps(price_dist_labels)},
                y: {json.dumps(price_dist_values)},
                type: 'bar',
                marker: {{ color: '#10b981' }}
            }}], {{...layout, title: '価格帯別販売数'}});

            Plotly.newPlot('monthlyTrendChart', {json.dumps(monthly_traces)}, {{
                ...layout,
                title: '月別販売数推移',
                showlegend: true
            }});

            const brandData = {json.dumps(brand_price_data)};
            for (const [tabId, data] of Object.entries(brandData)) {{
                const priceChartId = tabId + '_price_chart';
                const itemChartId = tabId + '_item_chart';

                if (document.getElementById(priceChartId)) {{
                    Plotly.newPlot(priceChartId, [{{
                        x: data.price_labels,
                        y: data.price_values,
                        type: 'bar',
                        marker: {{ color: '#6366f1' }}
                    }}], {{...layout, title: ''}});
                }}

                if (document.getElementById(itemChartId)) {{
                    Plotly.newPlot(itemChartId, [{{
                        labels: data.item_labels,
                        values: data.item_values,
                        type: 'pie',
                        hole: 0.4
                    }}], {{...layout, title: ''}});
                }}
            }}
        }});
    </script>
</body>
</html>
''')

# HTMLファイル出力
html_content = ''.join(html_parts)
output_path = '/Users/naokijodan/Desktop/earring-market-analysis/index.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✅ HTML生成完了: {output_path}")
print(f"   - 総件数: {len(df)}")
print(f"   - 総販売数: {total_sales:,}")
print(f"   - ブランドタブ: {len(top20_brand_tabs)}個")
