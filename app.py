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

st.set_page_config(page_title='ABAS | 経営分析 Ver.4', page_icon='📊', layout='wide')
st.title('ABAS | 経営分析 Ver.4')
st.caption('CSVの期間比較、利益分析、改善アクションとPDFレポートを作成します。任意で生成AI分析を利用できます（管理者設定が必要）。')
st.warning('公開デモです。個人情報・顧客情報・機密情報はアップロードしないでください。契約・課金・顧客認証は未稼働です。')

st.subheader('ABAS 月額プラン（提供準備中）')
st.caption('価格は検証用の仮設定です。以下はプラン案内であり、決済・契約を成立させるものではありません。')
plan_a, plan_b = st.columns(2)
with plan_a:
    st.markdown('### スタンダード')
    st.metric('想定月額', '30,000円')
    st.write('CSV分析・期間比較・PDFレポート（予定）')
with plan_b:
    st.markdown('### プロ')
    st.metric('想定月額', '50,000円')
    st.write('スタンダード機能＋個別テンプレート・導入支援（予定）')
st.info('現在は無料の公開デモです。有料プランの申込・支払・利用権限の付与はできません。')
with st.expander('月商シミュレーション（契約数は仮定）'):
    count_std = st.number_input('スタンダード契約数', min_value=0, max_value=10000, value=0, step=1)
    count_pro = st.number_input('プロ契約数', min_value=0, max_value=10000, value=10, step=1)
    st.metric('想定月商（売上総額・税等未調整）', f'{count_std*30000 + count_pro*50000:,}円')
    st.caption('売上予測ではありません。手数料、経費、税金、解約率を考慮していません。')


# ABAS Ver.5 - Stripe Sandbox Checkout
st.subheader("Stripe Sandbox テスト決済")
st.caption("テスト専用です。実際の請求は発生しません。")

try:
    import stripe
    secret_key = st.secrets.get("STRIPE_SECRET_KEY", "")
    prices = {
        "スタンダード": st.secrets.get("STRIPE_PRICE_STANDARD", ""),
        "プロ": st.secrets.get("STRIPE_PRICE_PRO", ""),
    }
except Exception:
    secret_key = ""
    prices = {}

if not secret_key or not all(prices.values()):
    st.warning("StripeのSecrets設定を確認してください。")
elif not secret_key.startswith("sk_test_"):
    st.error("本番APIキーは使用できません。")
else:
    stripe.api_key = secret_key
    app_url = "https://abas-cloud-eakr8jc4vqz979h9nctc5b.streamlit.app/"

    for plan_name, price_id in prices.items():
        if st.button(f"{plan_name}のテスト決済", key=f"pay_{plan_name}"):
            try:
                session = stripe.checkout.Session.create(
                    mode="subscription",
                    line_items=[{"price": price_id, "quantity": 1}],
                    payment_method_types=["card"],
                    success_url=app_url + "?checkout=returned",
                    cancel_url=app_url + "?checkout=canceled",
                )
                st.link_button("Stripeの決済画面を開く", session.url)
            except stripe.error.StripeError:
                st.error("決済画面を作成できません。Sandboxの設定を確認してください。")

st.info("決済画面から戻っても利用権限は付与されません。")

st.divider()


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

st.download_button('サンプルCSVをダウンロード', data='月,売上,経費,受注件数\n1月,120000,45000,12\n2月,160000,53000,15\n3月,190000,61000,19\n4月,175000,57000,17\n'.encode('utf-8-sig'), file_name='sample_sales.csv', mime='text/csv')
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
    if len(revenue)>=2:
        st.subheader('前期間との比較（CSVの行順）')
        last_rev, prev_rev = float(revenue.iloc[-1]), float(revenue.iloc[-2])
        last_profit = float(revenue.iloc[-1]-cost.iloc[-1])
        prev_profit = float(revenue.iloc[-2]-cost.iloc[-2])
        ca,cb=st.columns(2)
        ca.metric('最終行の売上',money(last_rev),delta=money(last_rev-prev_rev))
        cb.metric('最終行の差引利益',money(last_profit),delta=money(last_profit-prev_profit))
        st.caption('最終行とその直前の行を比較しています。時系列順に並んでいることを確認してください。')
        lines.extend([f'最終行の売上：{money(last_rev)}（前行差 {money(last_rev-prev_rev)}）',f'最終行の差引利益：{money(last_profit)}（前行差 {money(last_profit-prev_profit)}）'])
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
    st.subheader('次のアクション（担当者が検証）')
    action_items=['売上が減った期間の顧客数・単価・受注数を確認する','経費を主要費目に分け、前期間との差を確認する','改善施策の担当者・期限・評価指標を決める']
    for i, action in enumerate(action_items,1):
        st.write(f'{i}. {action}')
    lines.extend(['次のアクション：'+item for item in action_items])
    rows=[['指標','集計値','備考'],['売上合計',money(total_sales),'入力行の合計'],['経費合計',money(total_cost),'入力行の合計'],['差引利益',money(profit),'売上－経費']]
else:
    st.info('経営指標の計算には「売上」「経費」の列が必要です。一般統計レポートは作成できます。')
    lines.append('売上・経費の列がないため経営指標の計算は省略しました。')

# 生成AIは管理者がStreamlit SecretsにAPIキーを設定した場合のみ使用可能。
# 利用者のCSV全文は送らず、集計済みの指標・ルールベース提案のみ送信。
st.subheader('生成AIによる追加コメント（任意）')
try:
    api_key = st.secrets.get('OPENAI_API_KEY', '')
except Exception:
    api_key = ''
if not api_key:
    st.info('生成AIは未接続です。ルールベース分析とPDF出力は無料で利用できます。')
elif not rows:
    st.info('生成AIコメントには「売上」「経費」列が必要です。')
else:
    st.caption('「AI分析を実行」を押したときだけ、集計値と改善提案を外部AIサービスに送信します。入力CSVそのものは送信しません。')
    consent = st.checkbox('集計値を外部AIサービスへ送信することに同意します')
    if st.button('AI分析を実行', disabled=not consent):
        try:
            from openai import OpenAI
            client=OpenAI(api_key=api_key, timeout=20.0)
            summary='\n'.join(lines)[:4500]
            response=client.responses.create(model='gpt-4.1-mini', max_output_tokens=650,
                instructions='あなたは中小企業の経営分析補助者です。与えられた集計値だけを使い、事実と仮説を分けて日本語で300字以内の改善提案を述べてください。数値のない原因を断定しないでください。',
                input=summary)
            st.markdown(response.output_text)
            st.session_state['ai_comment']=response.output_text
        except Exception:
            st.error('AIサービスへの接続に失敗しました。管理者に設定・利用枠を確認してください。')
    if st.session_state.get('ai_comment'):
        st.caption('AIコメントは参考情報です。事実関係を確認してから使用してください。')
        lines.append('生成AIによる参考コメント：'+st.session_state['ai_comment'])

pdf=build_pdf(lines,rows)
md='# ABAS 経営分析レポート\n\n'+'\n\n'.join(lines)+'\n'
st.download_button('📄 PDFレポートをダウンロード',pdf,file_name='ABAS_report.pdf',mime='application/pdf')
st.download_button('Markdownレポートをダウンロード',md.encode('utf-8'),file_name='ABAS_report.md',mime='text/markdown')
st.caption('公開デモです。顧客認証・契約・課金・データ分離は未実装です。生成AIは管理者がAPIを設定した場合のみ使用可能です。')
