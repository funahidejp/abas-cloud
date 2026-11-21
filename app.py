import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title='ABAS | CSVレポート', page_icon='📊', layout='wide')
st.title('ABAS | CSV自動レポート')
st.caption('試作品：アップロードしたCSVを集計し、レポートを生成します。AI API・決済・顧客アカウントは未接続です。')
st.warning('試作段階です。個人情報・機密情報を含むファイルはアップロードしないでください。')
file = st.file_uploader('CSVファイルを選択（最大5MB）', type=['csv'])
if file:
    if file.size > 5 * 1024 * 1024:
        st.error('ファイルサイズは5MB以下にしてください。')
        st.stop()
    raw = file.getvalue()
    df = None
    for enc in ('utf-8-sig', 'cp932'):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc, nrows=50000, low_memory=False)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as exc:
            st.error(f'CSVを読み込めませんでした: {type(exc).__name__}')
            st.stop()
    if df is None:
        st.error('UTF-8またはShift-JIS形式のCSVを使用してください。')
        st.stop()
    if df.shape[1] > 100:
        st.error('列数は100以下にしてください。')
        st.stop()
    st.subheader('データ概要')
    a,b,c = st.columns(3)
    a.metric('行数（最大5万行）', f'{len(df):,}')
    b.metric('列数', f'{len(df.columns):,}')
    c.metric('欠損セル数', f'{int(df.isna().sum().sum()):,}')
    st.dataframe(df.head(20), use_container_width=True)
    numeric = df.select_dtypes(include='number')
    report = [f'# CSV分析レポート', '', f'- 読込行数: {len(df):,}', f'- 列数: {len(df.columns):,}', f'- 欠損セル数: {int(df.isna().sum().sum()):,}', '']
    if not numeric.empty:
        st.subheader('数値項目の統計')
        summary = numeric.describe().T.round(2)
        st.dataframe(summary, use_container_width=True)
        report += ['## 数値項目の統計', summary.to_csv(index=True), '']
        choice = st.selectbox('グラフ表示する数値列', numeric.columns.tolist())
        st.line_chart(numeric[choice].reset_index(drop=True))
    else:
        st.info('数値列がないため統計とグラフは省略しました。')
    report += ['## 各列の欠損数']
    report += [f'- {col}: {int(num)}' for col,num in df.isna().sum().items()]
    st.download_button('分析レポートをダウンロード（Markdown）', '\n'.join(report).encode('utf-8'), 'report.md', 'text/markdown')
