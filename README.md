# GIS Learning

Pythonで地理データを扱う基礎を学び、最終的に日本のオープンデータで人口減少と水インフラの関係を可視化します。

## STEP 1 環境構築

macOS（Apple Silicon）とPython 3.12で確認した構成です。リポジトリのルートで実行します。

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -c "import sys, geopandas, pandas, matplotlib; print(sys.executable); print(geopandas.__version__, pandas.__version__, matplotlib.__version__)"
```

既存の `.venv` がある場合は `source` の行から実行できます。最後のコマンドで、`.venv/bin/python` のパスと3つのバージョンが表示されれば準備完了です。

VS Codeではリポジトリのフォルダを開きます。別のPythonが選ばれていたら、コマンドパレットの `Python: Select Interpreter` で `.venv/bin/python` を選びます。

| ツール | 学ぶ役割 |
| --- | --- |
| pandas | 表形式のデータを `DataFrame` として扱い、行や列を絞り込む |
| GeoPandas | 図形とCRSを持つ `GeoDataFrame` で地理データを扱う |
| Matplotlib | 座標や分析結果を図として描く |
| QGIS | 地理データと分析結果を画面上で確認する |

## ロードマップ

1. **環境構築** — 仮想環境、依存関係、VS CodeとGitの設定
2. **GISの基礎** — 緯度・経度、CRS、ベクターとラスター、Point・LineString・Polygon。[演習01 — 東京・横浜・藤沢を可視化する](exercises/01_basics/README.md)
3. **GeoPandas** — GeoJSONとShapefileの読み込み、属性データ、座標変換、可視化（`exercises/02_geopandas/`）
4. **空間分析** — 距離、バッファ、空間結合、領域内判定、重ね合わせ（`exercises/03_spatial_analysis/`）
5. **実践プロジェクト** — 人口減少と水インフラの関係を可視化する（`project/final_analysis/`）

`data/raw/` には元データ、`data/processed/` には加工結果を置きます。Gitではデータの出典・取得手順と処理コードを管理します。
