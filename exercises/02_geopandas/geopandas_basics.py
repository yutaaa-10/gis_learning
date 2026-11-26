import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point


def main() -> None:

    # STEP 1: GeoJSONの読み込み
    path = "data/raw/N03-20260101_14_GML/N03-20260101_14.geojson"
    gdf = gpd.read_file(path)

    # STEP 2: データ構造の確認
    print("\n--- GeoDataFrame ---")
    print(gdf.head())
    print(f"Type: {type(gdf)}")
    print(f"Shape: {gdf.shape}")
    print(f"CRS: {gdf.crs}")
    print(gdf.geom_type.value_counts())

    # STEP 3: 藤沢市の抽出
    fujisawa = gdf[gdf["N03_004"] == "藤沢市"].copy()

    print("\n--- Filtering ---")
    print(f"抽出前の件数: {len(gdf)}")
    print(f"抽出後の件数: {len(fujisawa)}")

    # STEP 4: CRSの変換
    fujisawa_wgs84 = fujisawa.to_crs("EPSG:4326")
    kanagawa_wgs84 = gdf.to_crs("EPSG:4326")

    print("\n--- CRS Transformation ---")
    print(f"変換前: {fujisawa.crs}")
    print(f"変換後: {fujisawa_wgs84.crs}")

    # STEP 5: GeoJSONへの保存
    output_path = "data/processed/fujisawa_python.geojson"

    fujisawa_wgs84.to_file(
        output_path,
        driver="GeoJSON"
    )

    print(f"保存完了: {output_path}")

    # STEP 6: 神奈川県と藤沢市の可視化
    fig, ax = plt.subplots(figsize=(10, 10))

    kanagawa_wgs84.plot(
        ax=ax,
        color="lightgray",
        edgecolor="black",
        linewidth=0.3
    )

    fujisawa_wgs84.plot(
        ax=ax,
        color="red",
        edgecolor="black",
        linewidth=0.5
    )

    ax.set_title("Fujisawa City in Kanagawa")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # STEP 7: 面積計算
    fujisawa_projected = fujisawa.to_crs("EPSG:6677")

    area_m2 = fujisawa_projected.area.sum()
    area_km2 = area_m2 / 1_000_000

    print("\n--- Area ---")
    print(f"藤沢市の面積: {area_km2:.2f} km²")

    # STEP 8: 駅の位置情報を生成
    stations = gpd.GeoDataFrame(
        {
            "name": ["Fujisawa", "Tsujido"],
            "geometry": [
                Point(139.4875, 35.3389),
                Point(139.4471, 35.3369)
            ]
        },
        crs="EPSG:4326"
    )

    # 距離計算用の座標変換
    stations_projected = stations.to_crs("EPSG:6677")

    point_a = stations_projected.geometry.iloc[0]
    point_b = stations_projected.geometry.iloc[1]

    distance_m = point_a.distance(point_b)

    print("\n--- Distance ---")
    print(f"藤沢駅と辻堂駅の直線距離: {distance_m:.2f} m")

    # STEP 9: 半径500mのバッファー生成
    station_buffers = stations_projected.copy()

    station_buffers["geometry"] = (
        stations_projected.geometry.buffer(500)
    )

    # STEP 10: バッファーの可視化
    fig, ax = plt.subplots(figsize=(10, 10))

    fujisawa_projected.plot(
        ax=ax,
        color="lightgray",
        edgecolor="black",
        linewidth=0.5
    )

    station_buffers.plot(
        ax=ax,
        color="blue",
        alpha=0.3,
        edgecolor="blue"
    )

    stations_projected.plot(
        ax=ax,
        color="red",
        markersize=20
    )

    # 駅名の表示
    for _, row in stations_projected.iterrows():
        ax.annotate(
            row["name"],
            xy=(row.geometry.x, row.geometry.y),
            xytext=(5, 5),
            textcoords="offset points"
        )

    ax.set_title("Station Buffers - 500m")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_aspect("equal")

    # すべてのグラフを表示
    plt.show()


if __name__ == "__main__":
    main()
