# ABAS Ver.2 経営分析デモ

CSVの数値統計、売上・経費・差引利益、条件ベースの改善提案、PDF/Markdownレポートを作成するStreamlitアプリです。

## デプロイ
GitHubリポジトリのルートに `app.py`、`requirements.txt`、`sample_sales.csv` を配置し、Streamlit Community Cloudで `app.py` を指定してください。

## 動作確認
`sample_sales.csv` をアップロードして、指標とPDF出力を確認してください。

## 注意
- 生成AI、ログイン、決済、顧客別データ分離は未実装です。
- 公開デモに個人情報や機密情報をアップロードしないでください。
- 経費を差し引いた参考値であり、会計上の利益を確定するものではありません。
- AIによる自由文分析ではなく、閾値を使うルールベースの提案です。
