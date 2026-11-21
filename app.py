import io
import math
import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from xml.sax.saxutils import escape

st.set_page_config(page_title='ABAS | 経営分析 Ver.2', page_icon='📊', layout='wide')
st.title('ABAS | 経営分析 Ver.2')
st.caption('CSVを集計し、利益・経費率・売上推移を分析してPDFレポートを作成します。生成AI・顧客認証・決済は未接続です。')
st.warning('公開デモです。個人情報・顧客情報・機密情報はアップロードしないでください。')

@st.cache_data(show_spinner=False)
def load_csv(raw):
    for enc in ('utf-8-sig', 'cp932'):
        try:
            return pd.read_csv(io.BytesIO(raw), encoding=enc, nrows=50001)
        except UnicodeDecodeError:
            continue
    raise ValueError('UTF-8またはShift-JIS形式のCSVを使用してください。')

def money(x):
    return f'{x:,.0f}円'

def build_pdf(lines, rows):
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    style = ParagraphStyle('jp', fontName='HeiseiKakuGo-W5', fontSize=10, leading=17, spaceAfter=9)
    title_style = ParagraphStyle('titlejp', parent=style, fontSize=16, leading=23, spaceAfter=18)
    story = [Paragraph('ABAS 経営分析レポート', title_style)]
    for line in lines:
        story.append(Paragraph(escape(str(line)), style))
    if rows:
        data = [[Paragraph(escape(str(x)), style) for x in row] for row in rows]
        table = Table(data, colWidths=[110, 130, 130], repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EFF8')),('GRID',(0,0),(-1,-1),0.35,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
        story.extend([Spacer(1,12),table])
    doc.build(story)
    return buf.getvalue()

uploaded = st.file_uploader('CSVファイルを選択（最大5MB）', type=['csv'])
if uploaded is None:
    st.info('最初は sample_sales.csv をアップロードしてください。列名「売上」「経費」を自動認識します。')
    st.stop()
if uploaded.size > 5 * 1024 * 1024:
    st.error('5MB以下のCSVを使用してください。')
    st.stop()
try:
    df = load_csv(uploaded.getvalue())
except (ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
    st.error(f'CSVを読み込めません: {exc}')
    st.stop()
if len(df)>50000 or df.shape[1]>100:
    st.error('データは5万行・100列以下にしてください。')
    st.stop()
if df.empty:
    st.error('CSVにデータ行がありません。')
    st.stop()
st.subheader('データ概要')
a,b,c=st.columns(3)
a.metric('行数',f'{len(df):,}')
b.metric('列数',str(df.shape[1]))
c.metric('欠損セル数',f'{int(df.isna().sum().sum()):,}')
st.dataframe(df.head(30),use_container_width=True)

num_cols=[]
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        num_cols.append(col)
    elif col in ('売上','経費','受注件数'):
        conv=pd.to_numeric(df[col],errors='coerce')
        if conv.notna().sum()>0:
            df[col]=conv
            num_cols.append(col)

if not num_cols:
    st.warning('数値列がありません。数値のあるCSVをアップロードしてください。')
    st.stop()
st.subheader('数値データの統計')
st.dataframe(df[num_cols].describe().T.round(2),use_container_width=True)
chart_col=st.selectbox('グラフに表示する項目',num_cols)
label_col=next((c for c in ('月','年月','日付','日','期間') if c in df.columns),None)
if label_col:
    chart_df=pd.DataFrame({label_col:df[label_col].astype(str),chart_col:df[chart_col]})
    st.line_chart(chart_df.set_index(label_col))
else:
    st.line_chart(df[chart_col].reset_index(drop=True))

lines=[f'対象データ：{len(df)}行、{len(df.columns)}列。', '注意：数値は入力CSVに基づく集計です。会計上の利益や税額を確定するものではありません。']
rows=[]
st.subheader('経営指標と改善提案')
if '売上' in num_cols and '経費' in num_cols:
    revenue=pd.to_numeric(df['売上'],errors='coerce')
    cost=pd.to_numeric(df['経費'],errors='coerce')
    valid=revenue.notna() & cost.notna()
    if not valid.all():
        st.warning(f'売上と経費が両方数値の{int(valid.sum())}行だけを経営指標の計算に使用します。')
    revenue=revenue[valid]; cost=cost[valid]
    if revenue.empty:
        st.error('売上と経費を計算できる行がありません。')
        st.stop()
    total_sales=float(revenue.sum()); total_cost=float(cost.sum()); profit=total_sales-total_cost
    margin=profit/total_sales*100 if total_sales>0 else None
    cost_rate=total_cost/total_sales*100 if total_sales>0 else None
    x,y,z=st.columns(3)
    x.metric('売上合計',money(total_sales))
    y.metric('経費合計',money(total_cost))
    z.metric('差引利益（参考）',money(profit))
    if margin is not None:
        st.metric('差引利益率（参考）',f'{margin:.1f}%')
    advice=[]
    if total_sales<=0:
        advice.append('売上合計が0以下のため、利益率の評価を省略しました。入力値を確認してください。')
    else:
        if profit<0:
            advice.append('経費合計が売上合計を上回っています。費目別の内訳を確認してください。')
        if cost_rate>=70:
            advice.append('経費率が70%以上です。大きな費目から削減余地を調査してください。')
        if len(revenue)>=2 and revenue.iloc[-2]>0:
            change=(revenue.iloc[-1]/revenue.iloc[-2]-1)*100
            if change<=-10:
                advice.append(f'最終行の売上は前行比{change:.1f}%です。集客数・客単価などの要因を確認してください。')
            elif change>=10:
                advice.append(f'最終行の売上は前行比+{change:.1f}%です。増加要因を検証してください。')
        if not advice:
            advice.append('設定した警告条件には該当しません。売上推移と経費内訳の定期確認を推奨します。')
    st.markdown('**自動改善提案（ルールベース）**')
    for item in advice: st.write('・'+item)
    lines.extend([f'売上合計：{money(total_sales)}',f'経費合計：{money(total_cost)}',f'差引利益（参考）：{money(profit)}'])
    if margin is not None: lines.append(f'差引利益率（参考）：{margin:.1f}%')
    lines.extend(['改善提案：'+item for item in advice])
    rows=[['指標','集計値','備考'],['売上合計',money(total_sales),'入力行の合計'],['経費合計',money(total_cost),'入力行の合計'],['差引利益',money(profit),'売上－経費']]
else:
    st.info('経営指標の計算には「売上」「経費」の列が必要です。一般統計レポートは作成できます。')
    lines.append('売上・経費の列がないため経営指標の計算は省略しました。')

pdf=build_pdf(lines,rows)
md='# ABAS 経営分析レポート\n\n'+'\n\n'.join(lines)+'\n'
st.download_button('📄 PDFレポートをダウンロード',pdf,file_name='ABAS_report.pdf',mime='application/pdf')
st.download_button('Markdownレポートをダウンロード',md.encode('utf-8'),file_name='ABAS_report.md',mime='text/markdown')
st.caption('本アプリは公開デモです。認証・契約・課金・データ分離・生成AI連携は実装されていません。')
