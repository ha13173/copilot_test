# RedmineTicketManager

## 画像

- 開発開始
  - `https://icons8.jp/icon/NCWbsNZiw6Q2/%E3%82%B3%E3%83%BC%E2%80%8B%E2%80%8B%E3%83%89%E3%83%95%E3%82%A9%E3%83%BC%E3%82%AF`

- 開発項目追加
  - `https://icons8.jp/icon/1FdYDpqhZ86g/%E3%83%A9%E3%83%83%E3%83%97%E3%83%88%E3%83%83%E3%83%97%E3%82%B3%E3%83%BC%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0`

- 開発中プロジェクト一覧
  - `https://icons8.jp/icon/lVHTF1rQnwkd/%E3%83%AA%E3%82%B9%E3%83%88`

- コードレビュー結果PDF出力
  - `https://icons8.jp/icon/h4bm5sevBXVY/%E3%82%B3%E3%83%BC%E2%80%8B%E2%80%8B%E3%83%89%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB`

- チェックリストPDF出力
  - `https://icons8.jp/icon/8c8pwTVuujcD/%E3%83%86%E3%82%B9%E3%83%88%E5%90%88%E6%A0%BC`

## デプロイメモ

### IIS上での運用

- `C:\inetpub\wwwroot\RedmineTicketManager`にクローン

- Python仮想環境の作成

- 以下、リンクを参考に実行
  - 実行内容
    - Pythonのインストール
    - IISのCGIを有効化
    - IISでWebサイトの追加
    - Fast CGIのロック解除
    - `wfastcgi-enable`コマンドの実行
    - `web.config`の作成
  - URL
    - `https://qlitre-weblog.com/django-site-host-on-iis`
    - `https://qiita.com/hakomasu/items/cf8da96ebb1a6204fc47`

- IISの実行アカウントを`KUMA-DOM\SDSOFT1`に変更
  - `https://blog.dreamhive.co.jp/mkoba/?p=3448`

- IISのタイムアウト時間を`120`→`600`秒に変更
  - `https://qiita.com/YoshijiGates/items/6343dbeff79bfa9648eb`

- Fast CGIのタイムアウト時間を`600`秒に設定
  - `https://qiita.com/tsk1000/items/c0c915bf8082b0886c8f`

- ファイアウォールで受信ポート`3001`を許可

- `python manage.py collectstatic`実行

- `python manage.py migrate`実行

### 開発環境での運用

- しばらくはIIS上で順調に稼働していたが、急に以下の不具合が発生し、解決できなかったため、djangoを開発環境で稼働させることにした
  - SeleniumでWebページにはアクセスできるが、印刷処理が永遠に終了しない
  - Redmineチケット作成後のURLを正しく認識できず、404エラーとなる

- 仮想環境に切り替え、`python manage.py runserver 172.20.18.22:3001`を実行するバッチファイル（`launch.bat`）を作成

- PC19106は自動ログオンが有効であるため、`launch.bat`をスタートアップに設定
