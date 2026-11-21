# ABAS Cloud — CSV自動レポート（MVP）

## 機能
- CSVアップロード（UTF-8 / CP932、5MB以下、最大5万行・100列）
- 件数・欠損数・数値統計・簡易グラフ
- Markdownレポートのダウンロード

**現段階はルールベースの試作品です。** AIによる文章生成、決済、顧客管理、定期課金、営業自動化は実装していません。

## ローカル実行
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## クラウド公開（Streamlit Community Cloudの例）
1. このフォルダの `app.py` と `requirements.txt` を自分のGitHubリポジトリにアップロード。
2. Streamlit Community Cloudでリポジトリと `app.py` を指定してデプロイ。
3. 公開URLでデモを確認。無料枠の条件や利用制限はサービス側で確認してください。

## 公開前に必須
- 現状はログイン認証・テナント分離・利用規約・決済・データ保持方針がありません。
- **本番の顧客データを扱わないでください。** 公開する場合は匿名のデモデータだけで検証してください。
- 顧客向けには認証、アクセス制御、利用制限、ログ監査、障害対応、プライバシー対策を追加してください。
- CSVの読み込みやレポート生成はサーバーで行われます。データ取り扱いはホスティング先の規約を確認してください。

## 次の実装候補
1. 需要検証（業種を絞って3社以上にヒアリング）
2. 顧客ごとの専用レポートテンプレート
3. 認証・権限管理
4. Stripe等の決済と契約状態の検証
5. オプションとしてAIによる文章要約（API料金上限を設定）
