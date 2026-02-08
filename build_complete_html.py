#!/usr/bin/env python3
"""イヤリング市場分析HTML完全版生成スクリプト - 髪飾り分析HTMLと同等の構造"""

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

# CSVファイル読み込み
df = pd.read_csv('/Users/naokijodan/Desktop/イヤリング市場データ_sheet8_2026-02-07.csv')

print(f"=== データ読み込み完了 ===")
print(f"総件数: {len(df)}")

# 販売数を数値に変換
df['販売数'] = pd.to_numeric(df['販売数'], errors='coerce').fillna(1).astype(int)

# 売上計算
df['売上'] = df['価格'] * df['販売数']

# 総販売数・総売上
total_sales = int(df['販売数'].sum())
total_revenue = float(df['売上'].sum())

# 期間
period_start = df['販売日'].min()
period_end = df['販売日'].max()

# アイテムタイプ分類
def extract_item_type(title):
    title_upper = str(title).upper()
    if 'STUD' in title_upper:
        return 'Stud'
    if 'HOOP' in title_upper:
        return 'Hoop'
    if 'DROP' in title_upper or 'DANGLE' in title_upper:
        return 'Drop/Dangle'
    if 'CLIP' in title_upper or 'CLIP-ON' in title_upper or 'CLIP ON' in title_upper:
        return 'Clip-on'
    if 'HUGGIE' in title_upper:
        return 'Huggie'
    if 'THREADER' in title_upper:
        return 'Threader'
    if 'CUFF' in title_upper or 'EAR CUFF' in title_upper:
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
               'SALVATORE FERRAGAMO', 'FERRAGAMO', 'MIKIMOTO', 'POMELLATO']
DESIGNER_BRANDS = ['Vivienne Westwood', 'A BATHING APE', 'GIVENCHY', 'LANVIN', 'MARC JACOBS',
                   'TOM BINNS', 'Chrome Hearts', 'AGATHA']
CHARACTER_BRANDS = ['POKEMON', 'SANRIO', 'DISNEY']

# 全ブランドリスト（タイトルからの検出用）
ALL_BRANDS = HIGH_BRANDS + DESIGNER_BRANDS + CHARACTER_BRANDS

# ブランド列が空の場合、タイトルからブランドを検出して補完
def detect_brand_from_title(row):
    brand = row['ブランド']
    title = str(row['タイトル']).upper()

    # ブランド列が空または(不明)の場合、タイトルから検出
    if pd.isna(brand) or brand == '(不明)' or brand == '':
        # Vivienne Westwoodの変形
        if 'VIVIENNE' in title or 'WESTWOOD' in title:
            return 'Vivienne Westwood'
        # Pokemonの変形
        if 'POKEMON' in title or 'POKÉMON' in title:
            return 'POKEMON'
        for b in ALL_BRANDS:
            if b.upper() in title:
                return b
    return brand

df['ブランド'] = df.apply(detect_brand_from_title, axis=1)

print(f"=== ブランド補完後 ===")
print(df['ブランド'].value_counts().head(20).to_string())

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

# まとめ売り判定
def is_bulk(title):
    bulk_keywords = ['LOT', 'BULK', 'SET OF', 'BUNDLE', 'X2', 'X3', '2PCS', '3PCS', '4PCS', '5PCS', '6PCS',
                     'PAIR OF', 'PAIRS', 'COLLECTION', '複数', 'まとめ', 'セット', 'SET', 'PCS', 'PACK',
                     '10 PAIR', '15 PAIR', '9 PAIR', 'PIECES']
    title_upper = str(title).upper()
    for kw in bulk_keywords:
        if kw in title_upper:
            return True
    if re.search(r'\d+\s*(PCS|PIECES|PACK|点|個|本)', title_upper):
        return True
    return False

df['まとめ売り'] = df['タイトル'].apply(is_bulk)

# ノベルティ判定
def is_novelty(title):
    novelty_keywords = ['NOVELTY', 'GWP', 'LIMITED', 'NOT FOR SALE', '非売品', 'RARE', 'VIP']
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

# 素材抽出
def extract_material(title):
    title_upper = str(title).upper()
    if '18K' in title_upper or '18 K' in title_upper:
        return '18K Gold'
    if '14K' in title_upper or '14 K' in title_upper:
        return '14K Gold'
    if 'GOLD' in title_upper and 'PLATED' in title_upper:
        return 'Gold Plated'
    if 'GOLD' in title_upper:
        return 'Gold'
    if 'STERLING' in title_upper or '925' in title_upper:
        return 'Sterling Silver'
    if 'SILVER' in title_upper:
        return 'Silver'
    if 'PEARL' in title_upper:
        return 'Pearl'
    if 'TITANIUM' in title_upper:
        return 'Titanium'
    return 'Other'

df['素材'] = df['タイトル'].apply(extract_material)

# VW モチーフ抽出
def extract_vw_motif(title):
    title_upper = str(title).upper()
    if 'ORB' in title_upper:
        if 'TINY' in title_upper:
            return 'Tiny Orb'
        if 'MINI' in title_upper:
            return 'Mini Orb'
        if 'SMALL' in title_upper:
            return 'Small Orb'
        if 'GIANT' in title_upper:
            return 'Giant Orb'
        return 'Standard Orb'
    if 'HEART' in title_upper:
        return 'Heart'
    if 'PEARL' in title_upper:
        return 'Pearl'
    if 'SATURN' in title_upper:
        return 'Saturn'
    return 'Other'

# 仕入れ上限計算
df['仕入れ上限'] = df['価格'] * EXCHANGE_RATE * (1 - FEE_RATE) - SHIPPING_JPY

# ブランド別統計
def get_brand_stats(brand_df):
    if len(brand_df) == 0:
        return {}
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

# 安定度評価
def get_stability(cv):
    if cv <= 0.3:
        return '★★★'
    elif cv <= 0.5:
        return '★★☆'
    elif cv <= 0.7:
        return '★☆☆'
    else:
        return '☆☆☆'

# トップブランドリスト（販売数順）
brand_sales = df.groupby('ブランド')['販売数'].sum().sort_values(ascending=False)
top_brands = [b for b in brand_sales.head(10).index if pd.notna(b) and b != '(不明)' and b != '']

print(f"\n=== トップ10ブランド ===")
for b in top_brands:
    print(f"  - {b}")

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
.btn-primary:hover { opacity: 0.9; }
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
    padding: 10px 16px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 4px;
    font-size: 0.85em;
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
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border-left: 4px solid var(--accent);
}
.stat-card .icon { font-size: 1.5em; margin-bottom: 5px; }
.stat-card .value {
    font-size: 2em;
    font-weight: bold;
    color: var(--accent);
    margin: 10px 0;
}
.stat-card .label { font-size: 0.85em; color: var(--text-secondary); }
.chart-container {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}
.chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
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
    font-size: 0.85em;
}
th, td {
    padding: 12px;
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
    padding: 4px 8px;
    margin: 2px;
    font-size: 0.75em;
    border-radius: 3px;
    text-decoration: none;
    color: white;
}
.link-ebay { background: #0064d2; }
.link-mercari { background: #ff0211; }
.highlight { color: var(--positive); font-weight: bold; }
.section-title {
    font-size: 1.5em;
    color: var(--accent);
    margin: 30px 0 15px 0;
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
.insight-box li { padding: 8px 0; border-bottom: 1px dashed var(--border-color); }
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
.strategy-box h3 { color: #0284c7; margin-bottom: 15px; }
.strategy-box ul { list-style: none; padding: 0; }
.strategy-box li { padding: 8px 0; border-bottom: 1px dashed var(--border-color); }
.check-cell { width: 30px; }
.check-cell input { width: 18px; height: 18px; cursor: pointer; }
.checked-row { opacity: 0.5; text-decoration: line-through; }
@media (max-width: 768px) {
    .chart-grid { grid-template-columns: 1fr; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* CHANEL固有のスタイル */
#CHANEL .stat-card {
    background: linear-gradient(135deg, #00000015 0%, #00000005 100%);
    border-top: 3px solid #000000;
}
.chanel-accent { color: #000000; font-weight: bold; }

/* GUCCI固有のスタイル */
#GUCCI .stat-card {
    background: linear-gradient(135deg, #00634115 0%, #00634105 100%);
    border-top: 3px solid #006341;
}
.gucci-accent { color: #006341; font-weight: bold; }

/* DIOR固有のスタイル */
#DIOR .stat-card {
    background: linear-gradient(135deg, #00000015 0%, #00000005 100%);
    border-top: 3px solid #000000;
}

/* HERMES固有のスタイル */
#HERMES .stat-card {
    background: linear-gradient(135deg, #FF660015 0%, #FF660005 100%);
    border-top: 3px solid #FF6600;
}
.hermes-accent { color: #FF6600; font-weight: bold; }

/* LOUIS VUITTON固有のスタイル */
#LOUIS_VUITTON .stat-card {
    background: linear-gradient(135deg, #8B451315 0%, #8B451305 100%);
    border-top: 3px solid #8B4513;
}
.lv-accent { color: #8B4513; font-weight: bold; }

/* TIFFANY固有のスタイル */
#TIFFANY .stat-card {
    background: linear-gradient(135deg, #0abab515 0%, #0abab505 100%);
    border-top: 3px solid #0abab5;
}
.tiffany-accent { color: #0abab5; font-weight: bold; }

/* Vivienne Westwood固有のスタイル */
#Vivienne_Westwood .stat-card {
    background: linear-gradient(135deg, #6B0B5A15 0%, #6B0B5A05 100%);
    border-top: 3px solid #6B0B5A;
}
.vw-accent { color: #6B0B5A; font-weight: bold; }
'''

# アイテムタイプ別統計
item_type_stats = {}
for item_type in df['アイテムタイプ'].unique():
    type_df = df[df['アイテムタイプ'] == item_type]
    item_type_stats[item_type] = {
        'sales': int(type_df['販売数'].sum()),
        'revenue': float(type_df['売上'].sum()),
        'median': float(type_df['価格'].median()),
        'cv': float(type_df['価格'].std() / type_df['価格'].mean()) if type_df['価格'].mean() > 0 else 0
    }

# ブランドカテゴリ別統計
brand_cat_stats = {}
for cat in df['ブランドカテゴリ'].unique():
    cat_df = df[df['ブランドカテゴリ'] == cat]
    brand_cat_stats[cat] = {
        'sales': int(cat_df['販売数'].sum()),
        'revenue': float(cat_df['売上'].sum())
    }

# 全体分析
overall_stats = get_brand_stats(df)

# タブHTML生成
item_type_tabs = ''
item_type_tab_contents = ''
for item_type in ['Stud', 'Hoop', 'Drop/Dangle', 'Clip-on', 'Huggie', 'Ear Cuff']:
    safe_id = item_type.replace('/', '_').replace('-', '_').replace(' ', '_')
    item_type_tabs += f'<button class="tab" onclick="showTab(\'{safe_id}\')">{item_type}</button>\n'

# ブランド別タブ
brand_tabs = ''
for brand in ['CHANEL', 'GUCCI', 'DIOR', 'HERMES', 'LOUIS VUITTON', 'TIFFANY', 'Vivienne Westwood']:
    safe_id = brand.replace(' ', '_').replace('-', '_')
    brand_tabs += f'<button class="tab" onclick="showTab(\'{safe_id}\')">{brand}</button>\n'

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
        <p>データ期間: {period_start} ~ {period_end} | 生成: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 総件数: {len(df)}件</p>
    </div>

    <div class="controls">
        <div class="control-group">
            <label>💱 為替:</label>
            <input type="number" id="exchangeRate" value="{EXCHANGE_RATE}" step="0.1">
            <button class="btn btn-secondary" onclick="updateExchangeRate()" style="margin-left: 10px;">🔄 最新レート取得</button>
        </div>
        <div class="control-group">
            <label>📦 送料(円):</label>
            <input type="number" id="shippingCost" value="{SHIPPING_JPY}" step="100">
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
        <button class="tab" onclick="showTab('drop')">💧 Drop/Dangle</button>
        <button class="tab" onclick="showTab('clipon')">📎 Clip-on</button>
        <button class="tab" onclick="showTab('novelty')">🎁 ノベルティ</button>
        <button class="tab" onclick="showTab('bundle')">📦 まとめ売り</button>
        <button class="tab" onclick="showTab('recommend')">⭐ おすすめ出品順序</button>
        {brand_tabs}
    </div>
''')

# 全体分析タブ
html_parts.append(f'''
    <!-- 全体分析タブ -->
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
                <li>🔝 <strong>シャネルが市場を独占</strong>: 857件の販売で圧倒的シェア。ココマーク系が人気</li>
                <li>💎 <strong>ハイブランドが売上の{brand_cat_stats.get("ハイブランド", {}).get("sales", 0) / total_sales * 100:.0f}%</strong>: 高単価×高回転の理想的な市場</li>
                <li>⚡ <strong>VWは高回転ミッドレンジ</strong>: 中央値$97で仕入れやすく回転が早い</li>
                <li>🎯 <strong>狙い目</strong>: ルイヴィトン（$360）、ティファニー（$340）は高単価だが需要安定</li>
            </ul>
        </div>

        <h2 class="section-title">📊 カテゴリ別分析</h2>
        <div class="chart-grid">
            <div class="chart-container"><div id="itemTypeBarChart"></div></div>
            <div class="chart-container"><div id="brandCatPieChart"></div></div>
        </div>

        <h2 class="section-title">🏷️ ブランドカテゴリ別</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>カテゴリ</th>
                        <th>販売数</th>
                        <th>売上</th>
                        <th>シェア</th>
                    </tr>
                </thead>
                <tbody>
''')

for cat in ['ハイブランド', 'ノーブランド', 'デザイナー', 'キャラクター', 'その他']:
    if cat in brand_cat_stats:
        stats = brand_cat_stats[cat]
        share = stats['sales'] / total_sales * 100
        html_parts.append(f'''
                    <tr>
                        <td><strong>{cat}</strong></td>
                        <td>{stats['sales']:,}</td>
                        <td>${stats['revenue']:,.0f}</td>
                        <td>{share:.1f}%</td>
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
    <!-- ブランド一覧タブ -->
    <div id="brands" class="tab-content">
        <h2 class="section-title">🏷️ ブランド別販売実績</h2>
        <div class="table-container">
            <table id="brand-table">
                <thead>
                    <tr>
                        <th class="check-cell"></th>
                        <th>ブランド</th>
                        <th>カテゴリ</th>
                        <th>販売数</th>
                        <th>売上</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>CV値</th>
                        <th>安定度</th>
                        <th>リンク</th>
                    </tr>
                </thead>
                <tbody>
''')

# ブランド別統計を計算して出力
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

for i, stats in enumerate(brand_stats_list[:30]):
    brand = stats['brand']
    brand_lower = brand.lower().replace(' ', '+')
    stability = get_stability(stats['cv'])
    html_parts.append(f'''
                    <tr>
                        <td class="check-cell"><input type="checkbox" class="row-check" data-id="brand_{i}"></td>
                        <td><strong>{brand}</strong></td>
                        <td>{stats['category']}</td>
                        <td>{stats['sales']:,}</td>
                        <td>${stats['revenue']:,.0f}</td>
                        <td class="highlight">${stats['median_price']:.0f}</td>
                        <td data-usd="{stats['median_price']:.2f}">¥{int(stats['purchase_limit']):,}</td>
                        <td>{stats['cv']:.2f}</td>
                        <td>{stability}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={brand_lower}+earrings&LH_Sold=1&LH_Complete=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={brand}%20イヤリング&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
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
    type_stats = get_brand_stats(type_df)

    if len(type_df) == 0:
        continue

    # このタイプのブランド別統計
    type_brand_stats = []
    for brand in type_df['ブランド'].dropna().unique():
        if brand == '' or brand == '(不明)':
            continue
        b_df = type_df[type_df['ブランド'] == brand]
        b_stats = get_brand_stats(b_df)
        b_stats['brand'] = brand
        type_brand_stats.append(b_stats)
    type_brand_stats.sort(key=lambda x: x['sales'], reverse=True)

    html_parts.append(f'''
    <!-- {item_type}タブ -->
    <div id="{tab_id}" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">販売数</div>
                <div class="value">{type_stats.get('sales', 0):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">売上</div>
                <div class="value">${type_stats.get('revenue', 0):,.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="label">中央値</div>
                <div class="value">${type_stats.get('median_price', 0):.0f}</div>
            </div>
            <div class="stat-card">
                <div class="icon">📊</div>
                <div class="label">仕入上限</div>
                <div class="value">¥{int(type_stats.get('purchase_limit', 0)):,}</div>
            </div>
        </div>

        <h2 class="section-title">🏷️ {item_type} ブランド別</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="check-cell"></th>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>リンク</th>
                    </tr>
                </thead>
                <tbody>
''')

    for j, b_stats in enumerate(type_brand_stats[:15]):
        brand = b_stats['brand']
        brand_lower = brand.lower().replace(' ', '+')
        html_parts.append(f'''
                    <tr>
                        <td class="check-cell"><input type="checkbox" class="row-check" data-id="{tab_id}_{j}"></td>
                        <td><strong>{brand}</strong></td>
                        <td>{b_stats['sales']:,}</td>
                        <td class="highlight">${b_stats['median_price']:.0f}</td>
                        <td data-usd="{b_stats['median_price']:.2f}">¥{int(b_stats['purchase_limit']):,}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={brand_lower}+{item_type.lower()}+earrings&LH_Sold=1&LH_Complete=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={brand}%20{item_type}%20イヤリング&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
''')

    html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ノベルティタブ
novelty_df = df[df['ノベルティ'] == True]
novelty_stats = get_brand_stats(novelty_df)
html_parts.append(f'''
    <!-- ノベルティタブ -->
    <div id="novelty" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">🎁</div>
                <div class="label">ノベルティ件数</div>
                <div class="value">{len(novelty_df):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">中央値</div>
                <div class="value">${novelty_stats.get('median_price', 0):.0f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>🎁 ノベルティ市場の特徴</h3>
            <ul>
                <li>仕入れルート: 百貨店購入特典、ビューティーカウンター、VIPイベント等</li>
                <li>CHANELノベルティは特に人気が高い</li>
                <li>「非売品」「限定」等のキーワードで付加価値</li>
            </ul>
        </div>

        <h2 class="section-title">🎁 ノベルティ商品一覧</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ブランド</th>
                        <th>商品名</th>
                        <th>価格</th>
                        <th>販売数</th>
                    </tr>
                </thead>
                <tbody>
''')

for _, row in novelty_df.sort_values('販売数', ascending=False).head(20).iterrows():
    html_parts.append(f'''
                    <tr>
                        <td>{row['ブランド'] if pd.notna(row['ブランド']) else 'N/A'}</td>
                        <td>{row['タイトル'][:60]}...</td>
                        <td>${row['価格']:.0f}</td>
                        <td>{row['販売数']}</td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# まとめ売りタブ
bundle_df = df[df['まとめ売り'] == True]
bundle_stats = get_brand_stats(bundle_df)
html_parts.append(f'''
    <!-- まとめ売りタブ -->
    <div id="bundle" class="tab-content">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">📦</div>
                <div class="label">まとめ売り件数</div>
                <div class="value">{len(bundle_df):,}</div>
            </div>
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="label">中央値</div>
                <div class="value">${bundle_stats.get('median_price', 0):.0f}</div>
            </div>
        </div>

        <div class="insight-box">
            <h3>📦 まとめ売りの注意点</h3>
            <ul>
                <li>単価計算には不向き（平均価格が歪む）</li>
                <li>ノーブランド品のまとめ売りは利益率低め</li>
                <li>ブランド品のセットは希少性あり</li>
            </ul>
        </div>
    </div>
''')

# おすすめ出品順序タブ
html_parts.append('''
    <!-- おすすめ出品順序タブ -->
    <div id="recommend" class="tab-content">
        <h2 class="section-title">⭐ おすすめ出品順序 TOP20</h2>
        <p style="margin-bottom: 20px; color: var(--text-secondary);">スコア = 販売数 × 中央値（回転率と利益のバランス）</p>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="check-cell"></th>
                        <th>順位</th>
                        <th>ブランド</th>
                        <th>販売数</th>
                        <th>中央値</th>
                        <th>仕入上限</th>
                        <th>スコア</th>
                        <th>リンク</th>
                    </tr>
                </thead>
                <tbody>
''')

# スコア計算
for stats in brand_stats_list:
    stats['score'] = stats['sales'] * stats['median_price']

brand_stats_list.sort(key=lambda x: x['score'], reverse=True)

for i, stats in enumerate(brand_stats_list[:20]):
    brand = stats['brand']
    brand_lower = brand.lower().replace(' ', '+')
    rank_class = ''
    if i == 0:
        rank_class = 'style="color: gold; font-weight: bold;"'
    elif i == 1:
        rank_class = 'style="color: silver; font-weight: bold;"'
    elif i == 2:
        rank_class = 'style="color: #cd7f32; font-weight: bold;"'

    html_parts.append(f'''
                    <tr>
                        <td class="check-cell"><input type="checkbox" class="row-check" data-id="rec_{i}"></td>
                        <td {rank_class}>{i + 1}</td>
                        <td><strong>{brand}</strong></td>
                        <td>{stats['sales']:,}</td>
                        <td class="highlight">${stats['median_price']:.0f}</td>
                        <td data-usd="{stats['median_price']:.2f}">¥{int(stats['purchase_limit']):,}</td>
                        <td>{stats['score']:,.0f}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={brand_lower}+earrings&LH_Sold=1&LH_Complete=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={brand}%20イヤリング&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
''')

html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# ブランド個別タブ生成
brand_configs = [
    ('CHANEL', 'シャネル', '#000000', 'chanel'),
    ('GUCCI', 'グッチ', '#006341', 'gucci'),
    ('DIOR', 'ディオール', '#000000', 'dior'),
    ('HERMES', 'エルメス', '#FF6600', 'hermes'),
    ('LOUIS VUITTON', 'ルイヴィトン', '#8B4513', 'lv'),
    ('TIFFANY', 'ティファニー', '#0abab5', 'tiffany'),
    ('Vivienne Westwood', 'ヴィヴィアン・ウエストウッド', '#6B0B5A', 'vw'),
]

for brand, brand_jp, color, class_prefix in brand_configs:
    brand_df = df[df['ブランド'].str.upper() == brand.upper()] if brand != 'Vivienne Westwood' else df[df['ブランド'].str.contains('Vivienne', case=False, na=False)]

    if len(brand_df) == 0:
        continue

    b_stats = get_brand_stats(brand_df)
    safe_id = brand.replace(' ', '_')
    brand_lower = brand.lower().replace(' ', '+')

    # 人気商品Top15
    top_items = brand_df.sort_values('販売数', ascending=False).head(15)

    # VWの場合はモチーフ分析を追加
    vw_motif_html = ''
    if brand == 'Vivienne Westwood':
        brand_df['VWモチーフ'] = brand_df['タイトル'].apply(extract_vw_motif)
        motif_stats = brand_df.groupby('VWモチーフ').agg({
            '販売数': 'sum',
            '価格': 'median'
        }).reset_index()
        motif_stats = motif_stats.sort_values('販売数', ascending=False)

        vw_motif_html = '''
        <h2 class="section-title">🔮 モチーフ別分析</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr><th>モチーフ</th><th>販売数</th><th>中央値</th></tr>
                </thead>
                <tbody>
'''
        for _, row in motif_stats.iterrows():
            vw_motif_html += f'''
                    <tr>
                        <td>{row['VWモチーフ']}</td>
                        <td>{int(row['販売数'])}</td>
                        <td>${row['価格']:.0f}</td>
                    </tr>
'''
        vw_motif_html += '''
                </tbody>
            </table>
        </div>
'''

    html_parts.append(f'''
    <!-- {brand}タブ -->
    <div id="{safe_id}" class="tab-content">
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
                <div class="label">仕入上限</div>
                <div class="value" data-usd="{b_stats['median_price']:.2f}">¥{int(b_stats['purchase_limit']):,}</div>
            </div>
        </div>

        <div class="strategy-box">
            <h3>🎯 {brand_jp} 仕入れ戦略</h3>
            <ul>
                <li>💰 <strong>仕入れ目安</strong>: ¥{int(b_stats['purchase_limit']):,}以下で仕入れ</li>
                <li>📦 <strong>箱付きプレミアム</strong>: 箱・ギャランティ付きは+10-20%</li>
                <li>⚠️ <strong>避けるべき</strong>: 傷・変色あり、刻印なし、偽物リスク高</li>
                <li>🔍 <strong>確認ポイント</strong>: ブランド刻印、素材表記、付属品の有無</li>
            </ul>
        </div>

        {vw_motif_html}

        <h2 class="section-title">📌 {brand_jp} 人気商品 Top15</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="check-cell"></th>
                        <th>商品名</th>
                        <th>販売数</th>
                        <th>価格</th>
                        <th>仕入上限</th>
                        <th>リンク</th>
                    </tr>
                </thead>
                <tbody>
''')

    for k, (_, row) in enumerate(top_items.iterrows()):
        title_short = row['タイトル'][:50] + '...' if len(str(row['タイトル'])) > 50 else row['タイトル']
        purchase_limit = row['価格'] * EXCHANGE_RATE * (1 - FEE_RATE) - SHIPPING_JPY
        html_parts.append(f'''
                    <tr>
                        <td class="check-cell"><input type="checkbox" class="row-check" data-id="{class_prefix}_{k}"></td>
                        <td>{title_short}</td>
                        <td>{row['販売数']}</td>
                        <td class="highlight">${row['価格']:.0f}</td>
                        <td data-usd="{row['価格']:.2f}">¥{int(purchase_limit):,}</td>
                        <td>
                            <a href="https://www.ebay.com/sch/i.html?_nkw={brand_lower}+earrings&LH_Sold=1&LH_Complete=1" target="_blank" class="link-btn link-ebay">eBay</a>
                            <a href="https://jp.mercari.com/search?keyword={brand_jp}%20イヤリング&status=on_sale" target="_blank" class="link-btn link-mercari">メルカリ</a>
                        </td>
                    </tr>
''')

    html_parts.append('''
                </tbody>
            </table>
        </div>
    </div>
''')

# JavaScript
item_type_labels = list(item_type_stats.keys())
item_type_sales = [item_type_stats[k]['sales'] for k in item_type_labels]
brand_cat_labels = list(brand_cat_stats.keys())
brand_cat_sales = [brand_cat_stats[k]['sales'] for k in brand_cat_labels]

html_parts.append(f'''
    <script>
        // テーマ切替
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

        // テーマ復元
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.setAttribute('data-theme', 'dark');
            document.getElementById('themeBtn').textContent = '☀️ ライトモード';
        }}

        // タブ切替
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}

        // 為替レート取得
        async function updateExchangeRate() {{
            try {{
                const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
                const data = await response.json();
                const rate = data.rates.JPY;
                document.getElementById('exchangeRate').value = rate.toFixed(2);
                recalculate();
                alert('為替レート更新: 1USD = ' + rate.toFixed(2) + '円');
            }} catch (error) {{
                alert('為替取得に失敗しました');
            }}
        }}

        // 再計算
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

        // チェックボックス保存
        function initCheckboxes() {{
            const saved = JSON.parse(localStorage.getItem('earringChecks') || '{{}}');
            document.querySelectorAll('.row-check').forEach(checkbox => {{
                const id = checkbox.dataset.id;
                if (saved[id]) {{
                    checkbox.checked = true;
                    checkbox.closest('tr').classList.add('checked-row');
                }}
                checkbox.addEventListener('change', function() {{
                    const row = this.closest('tr');
                    if (this.checked) {{
                        row.classList.add('checked-row');
                        saved[id] = true;
                    }} else {{
                        row.classList.remove('checked-row');
                        delete saved[id];
                    }}
                    localStorage.setItem('earringChecks', JSON.stringify(saved));
                }});
            }});
        }}

        // グラフ描画
        document.addEventListener('DOMContentLoaded', function() {{
            initCheckboxes();

            // アイテムタイプ別棒グラフ
            Plotly.newPlot('itemTypeBarChart', [{{
                x: {json.dumps(item_type_labels)},
                y: {json.dumps(item_type_sales)},
                type: 'bar',
                marker: {{ color: '#6366f1' }}
            }}], {{
                title: 'アイテムタイプ別販売数',
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: {{ color: 'var(--text-primary)' }}
            }});

            // ブランドカテゴリ別円グラフ
            Plotly.newPlot('brandCatPieChart', [{{
                labels: {json.dumps(brand_cat_labels)},
                values: {json.dumps(brand_cat_sales)},
                type: 'pie',
                hole: 0.4
            }}], {{
                title: 'ブランドカテゴリ別シェア',
                paper_bgcolor: 'transparent',
                font: {{ color: 'var(--text-primary)' }}
            }});
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
print(f"   - 総売上: ${total_revenue:,.0f}")
