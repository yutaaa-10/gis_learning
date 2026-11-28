"""STEP 3: 各地点（1kmメッシュ）から一番近い浄水場・下水処理場はどこで、何km離れている？"""
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import Point

# ---- パス・定数 ----
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
CITY_PATH = RAW / "N03-20260101_14_GML" / "N03-20260101_14.shp"
JOUSUI_PATH = RAW / "P21-12_14_GML" / "P21-12b_14.shp"
GESUI_PATH = RAW / "P22-12_14_GML" / "P22b-12_14.shp"
MESH_DIR = RAW / "estat_mesh3_boundary"
POP_DIR = RAW / "estat_mesh3_pop2020"
OUT_DIR = ROOT / "project" / "final_analysis" / "outputs"
PROCESSED = ROOT / "data" / "processed"

MESH1_CODES = ["5238", "5239", "5338", "5339"]  # 神奈川県にかかる1次メッシュ
CRS_METRIC = "EPSG:6677"  # 平面直角座標系 第IX系（単位：メートル）
YODA_LONLAT = (139.435, 35.400)  # 藤沢市用田のおおよその位置（経度, 緯度）※要確認

# ---- 1. 4つのメッシュを読み込んで1つにつなげる ----
meshes = [
    gpd.read_file(MESH_DIR / f"SXYSWS{code}" / f"MESH0{code}.shp").to_crs(CRS_METRIC)
    for code in MESH1_CODES
]
mesh = gpd.GeoDataFrame(pd.concat(meshes, ignore_index=True), crs=CRS_METRIC)
mesh["KEY_CODE"] = mesh["KEY_CODE"].astype(str)
print("メッシュ数（4区画の合計）:", len(mesh))

# ---- 2. 神奈川県にかかるマスだけに絞る ----
kanagawa = gpd.read_file(CITY_PATH).to_crs(CRS_METRIC)
kanagawa_outline = kanagawa.dissolve()[["geometry"]]  # 県全体を1つの形にまとめる
mesh = gpd.sjoin(mesh, kanagawa_outline, how="inner", predicate="intersects").drop(columns="index_right")
print("神奈川県にかかるメッシュ数:", len(mesh))

# ---- 3. 人口の表を読み込んで、KEY_CODEでメッシュとつなぐ ----
# 1行目=列の記号、2行目=日本語の列名なので2行目を飛ばす。文字コードはShift_JIS。
pop = pd.concat(
    [
        pd.read_csv(POP_DIR / f"tblT001140S{code}.txt", encoding="cp932",
                    skiprows=[1], dtype={"KEY_CODE": str})
        for code in MESH1_CODES
    ],
    ignore_index=True,
)
pop = pop[["KEY_CODE", "T001140001", "T001140019"]].rename(
    columns={"T001140001": "pop_total", "T001140019": "pop_65over"}
)
# 秘匿された値は「*」なので数値にできない → NaN にする
for col in ["pop_total", "pop_65over"]:
    pop[col] = pd.to_numeric(pop[col], errors="coerce")

mesh = mesh.merge(pop, on="KEY_CODE", how="left")
mesh["pop_total"] = mesh["pop_total"].fillna(0)  # 表に無いマス＝人が住んでいない
print("人口合計:", int(mesh["pop_total"].sum()))

# ---- 4. 各マスの中心から、一番近い施設までの距離 ----
jousui = gpd.read_file(JOUSUI_PATH).set_crs("EPSG:4612").to_crs(CRS_METRIC)
gesui = gpd.read_file(GESUI_PATH, encoding="cp932").to_crs(CRS_METRIC)

centers = mesh[["KEY_CODE", "pop_total"]].copy()
centers = gpd.GeoDataFrame(centers, geometry=mesh.geometry.centroid, crs=CRS_METRIC)


def nearest(points, facilities, name_col, prefix):
    """各点に、一番近い施設の名前と距離(km)を付ける"""
    joined = gpd.sjoin_nearest(
        points, facilities[[name_col, "geometry"]], how="left", distance_col="dist_m"
    )
    joined = joined[~joined.index.duplicated()]  # 等距離で複数ヒットした場合は1つに
    return pd.DataFrame({
        f"{prefix}_name": joined[name_col],
        f"{prefix}_km": joined["dist_m"] / 1000,
    })


mesh = mesh.join(nearest(centers, jousui, "P21B_003", "jousui"))
mesh = mesh.join(nearest(centers, gesui, "P22b_002", "gesui"))

# ---- 結果の確認 ----
lived = mesh[mesh["pop_total"] > 0]
for prefix, label in [("jousui", "浄水場"), ("gesui", "下水処理場")]:
    km = lived[f"{prefix}_km"]
    w_mean = (km * lived["pop_total"]).sum() / lived["pop_total"].sum()
    print(f"\n[{label}] 人が住むマスの距離: 平均 {km.mean():.1f}km / 最大 {km.max():.1f}km"
          f" / 人口で重み付けした平均 {w_mean:.1f}km")
    print(lived.nlargest(5, f"{prefix}_km")[["KEY_CODE", "pop_total", f"{prefix}_name", f"{prefix}_km"]]
          .to_string(index=False))

yoda = gpd.GeoSeries([Point(YODA_LONLAT)], crs="EPSG:4326").to_crs(CRS_METRIC).iloc[0]
yoda_row = mesh[mesh.contains(yoda)]
print("\n[用田のマス]")
print(yoda_row[["KEY_CODE", "pop_total", "jousui_name", "jousui_km", "gesui_name", "gesui_km"]]
      .to_string(index=False))

# ---- 保存 ----
PROCESSED.mkdir(parents=True, exist_ok=True)
mesh.to_file(PROCESSED / "step03_mesh_distance.gpkg", driver="GPKG")  # QGISで開ける

OUT_DIR.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "Hiragino Sans"
fig, axes = plt.subplots(1, 2, figsize=(14, 7))
for ax, (prefix, facilities, label) in zip(
    axes, [("jousui", jousui, "浄水場"), ("gesui", gesui, "下水処理場")]
):
    mesh.plot(column=f"{prefix}_km", cmap="YlOrRd", legend=True, ax=ax,
              legend_kwds={"label": "最寄り施設までの直線距離 (km)", "shrink": 0.6})
    kanagawa_outline.boundary.plot(ax=ax, color="black", linewidth=0.5)
    facilities.plot(ax=ax, color="blue", markersize=8)
    gpd.GeoSeries([yoda], crs=CRS_METRIC).plot(ax=ax, color="lime", marker="*", markersize=150)
    ax.set_title(f"最寄りの{label}までの距離（青＝施設、緑の星＝用田）")
    ax.set_axis_off()
fig.savefig(OUT_DIR / "step03_nearest_distance.png", dpi=150, bbox_inches="tight")
print("\nsaved:", OUT_DIR / "step03_nearest_distance.png")
