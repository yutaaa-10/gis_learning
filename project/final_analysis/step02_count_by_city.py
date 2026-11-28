"""STEP 2: 市町村ごとに浄水場・下水処理場はいくつある？"""
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt

# ---- パス（冒頭の定数にまとめる） ----
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CITY_PATH = RAW / "N03-20260101_14_GML" / "N03-20260101_14.shp"
JOUSUI_PATH = RAW / "P21-12_14_GML" / "P21-12b_14.shp"
GESUI_PATH = RAW / "P22-12_14_GML" / "P22b-12_14.shp"
OUT_DIR = ROOT / "project" / "final_analysis" / "outputs"

CRS_METRIC = "EPSG:6677"  # 平面直角座標系 第IX系（単位：メートル）

# ---- 段階1：読み込み ----
city = gpd.read_file(CITY_PATH)
jousui = gpd.read_file(JOUSUI_PATH)
gesui = gpd.read_file(GESUI_PATH, encoding="cp932")  # 日本語の文字化け対策

# ---- 段階2：CRSをそろえる ----
# P21は.prjが無くCRSが不明(None)なので、「元々のCRSはこれ」と宣言する(set_crs)。
# set_crsは座標の数値を変えない。to_crsは座標の数値を計算し直して変換する。
jousui = jousui.set_crs("EPSG:4612")  # JGD2000 緯度経度（仕様書より）

city = city.to_crs(CRS_METRIC)
jousui = jousui.to_crs(CRS_METRIC)
gesui = gesui.to_crs(CRS_METRIC)

# 1つの市町村が島などで複数ポリゴンに分かれているので、市町村ごとに1つにまとめる(dissolve)。
# N03_004=市区町村名（政令市は市名）。区まで分けたいならN03_005も使う。
city = city.dissolve(by="N03_004", as_index=False)[["N03_004", "geometry"]]


# ---- 段階3・4：空間結合して数える ----
def count_points(points, polygons, col_name):
    # 各点に「その点を含む市町村」の名前を付ける
    joined = gpd.sjoin(points, polygons, how="inner", predicate="within")
    counts = joined.groupby("N03_004").size().rename(col_name)
    # 属性結合で市町村に戻す。施設が無い市町村はNaNになるので0で埋める
    result = polygons.merge(counts, left_on="N03_004", right_index=True, how="left")
    result[col_name] = result[col_name].fillna(0).astype(int)
    return result


city = count_points(jousui, city, "n_jousui")
city = count_points(gesui, city, "n_gesui")

print(city[["N03_004", "n_jousui", "n_gesui"]]
      .sort_values("n_jousui", ascending=False)
      .to_string(index=False))
print("浄水場 合計:", city["n_jousui"].sum(), "/", len(jousui))
print("処理場 合計:", city["n_gesui"].sum(), "/", len(gesui))

# ---- 地図 ----
OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Hiragino Sans"  # 日本語を表示するため
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
for ax, col, title in zip(axes, ["n_jousui", "n_gesui"], ["浄水場の数", "下水処理場の数"]):
    city.plot(column=col, cmap="Blues", legend=True, edgecolor="gray", linewidth=0.3, ax=ax)
    ax.set_title(title)
    ax.set_axis_off()
fig.savefig(OUT_DIR / "step02_count_by_city.png", dpi=150, bbox_inches="tight")
print("saved:", OUT_DIR / "step02_count_by_city.png")


