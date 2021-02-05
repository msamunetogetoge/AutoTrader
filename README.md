# autotrader
bitflyerのAPIを使って仮想通貨の取引をするアプリ
## 出来る事
- bitflyer 経由でのビットコイン(BTC/JPY)、の売買
- 適当なテクニカル指標を基にした自動売買
- テクニカル指標のパラメータのバックテスト
- テクニカル指標を取り込んだチャートの描画
- チャートに、テクニカル指標や売買記録をつける
![landingpagedemo](chart/static/img/landing_demo.jpg)  

## 使い方
1. bitflyer アカウントを取得してapikey, apisecretをkey.py に貼り付ける   
2. docker-compose.yml のあるディレクトリで以下のコマンドを実行する
```
docker-compose up -d --build
```  
正しくapi key等を入力しているか不安な時は、以下のコマンドを実行する。
```
docker exec -it gunicorn_django_autotrader /bin/bash
python manage.py authcheck
```  
3. 適当なブラウザで`localhost` に接続
4. 以下のコマンドでデータの収集を開始(docker-compose とか、最初の段階で動かしたいけど上手くいかなかった)
```
docker exec -it gunicorn_django_autotrader /bin/bash
python manage.py startstream
```
### 起動に関して 
./docker-compose.yml に書いてあるように、初めにdbinit.shを実行する。  
その時、データベースに色々データをロードするので、起動が遅い。二度目以降は既にデータがあるので、コメントアウトすると起動が速くなる。  
## 画面の解説
### 最初の画面
![landingpagedemo](/static/img/index.jpg)  


- 左上のbitcoin を押すと、最初の画面に戻ってくる。
- bitcoinの下にAUTOTRADING ~~と表示されている時は、自動売買している。algo=" "が使っているアルゴリズム。
- その下にある数字を適当に弄って 紫の1s, 1m, 1hボタンを押すと、1期が1秒,1分,1時間のキャンドルスティック図を描く。
- グラフは右にplotly で描いているので感覚的に線を表示・非表示にしたりズームなどが出来る。

### BACKTEST
![landingpagedemo](/static/img/backtest.jpg)  
- 2016年から2021年までの5年分の日足のデータで、テクニカル指標の最適なパラメータを計算する。
- そのパラメータを使って自動売買する機能はそのうち作る

### AUTOTRADE
![landingpagedemo](/static/img/autotrade.jpg) 
- 使いたいアルゴリズムを選んで選択ボタンを押すと取引を開始する。アルゴリズムのパラメータは今持っているテクニカル現在は45分に一回取引を行うか判断する。
- テクニカル指標を使うアルゴリズムは、パラメータを手動で入力できるようにしたり、取引の間隔を手動で入力できるようにするかもしれない。

### TRADEHISTORY
- 保存されている取引履歴が表示される。
### TRADE
- 手動で取引する。買う時は円、売る時はビットコインの数量を入力する。


## コードを改良したい時
./chart/controllers/ai.py にアルゴリズムが格納されている。ai.Trade, ai.Recognize, ai.Optimize, ai.BackTestに書き加え、chart/models.AlgoList に作ったアルゴリズムを追加すると使える。

## python.manage.pyで使えるコマンド
./autotrade/management/commands に入っているpythonファイルがコマンドで使える.
```
python manage.py commands
```
### csv2backtestdata
BACKTEST のページで使われるデータを作成する。具体的には、./BTC_JPY_bitflyer.csvの中身を、Candle_BackTest に格納する。
### addalgolist
アルゴリズムを追加するコマンド。pyファイルの中の辞書に手打ちして使う。
### authcheck
key.py に入力したapikey等が有効か調べるコマンド。 getbalanceをリクエストして、上手く帰ってきたら使えるという判定。
### getfronsql
stockdata.sql に入っているデータをCandle_1s, Candle_1m, Candle_1hに取り込むコマンド。
### startstream
ticker をapi経由で取得し続けるコマンド。 5秒に一回データを取得する。docker で動かした時は自動でスタートしている。
### starttrade
自動売買を始めるコマンド。アルゴリズムを考えて、アプリ側に追加するのが面倒な時に使う。


