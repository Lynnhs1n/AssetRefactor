from core.models import Asset, AssetGroup, AssetType


class ClusteringEngine:
    def __init__(self, time_threshold_sec: float = 3.0):
        self.time_threshold = time_threshold_sec

    def cluster_scattered_assets(self, assets: list[Asset]) -> list[AssetGroup]:
        # Separate image raws (skip .xmp sidecars) for clustering
        clusterable = [a for a in assets if a.asset_type == AssetType.IMAGE and a.ext.lower() != ".xmp"]
        videos = [a for a in assets if a.asset_type == AssetType.VIDEO]

        if not clusterable and not videos:
            return []

        # Cluster images by type, then videos by type
        groups: list[AssetGroup] = []

        image_clusters = self._build_clusters(clusterable)
        for idx, cluster in enumerate(image_clusters):
            if len(cluster) >= 2:
                # Collect all assets including xmp companions
                all_assets = self._collect_with_xmps(cluster)
                groups.append(AssetGroup(
                    assets=all_assets,
                    folder_name=f"AutoSeq_{idx + 1}",
                    is_auto_cluster=True,
                ))
            else:
                # Singleton — no subfolder
                all_assets = self._collect_with_xmps(cluster)
                groups.append(AssetGroup(
                    assets=all_assets,
                    folder_name="",
                    is_auto_cluster=False,
                ))

        video_clusters = self._build_clusters(videos)
        for idx, cluster in enumerate(video_clusters):
            if len(cluster) >= 2:
                all_assets = self._collect_with_xmps(cluster)
                groups.append(AssetGroup(
                    assets=all_assets,
                    folder_name=f"AutoSeq_V{idx + 1}",
                    is_auto_cluster=True,
                ))
            else:
                all_assets = self._collect_with_xmps(cluster)
                groups.append(AssetGroup(
                    assets=all_assets,
                    folder_name="",
                    is_auto_cluster=False,
                ))

        return groups

    def _build_clusters(self, assets: list[Asset]) -> list[list[Asset]]:
        if not assets:
            return []

        # Sort by timestamp
        sorted_assets = sorted(assets, key=lambda a: a.timestamp_epoch)

        clusters: list[list[Asset]] = []
        current_cluster = [sorted_assets[0]]

        for i in range(1, len(sorted_assets)):
            prev = current_cluster[-1]
            curr = sorted_assets[i]

            if self._files_are_sequential(prev, curr) and \
               (curr.timestamp_epoch - prev.timestamp_epoch) < self.time_threshold:
                current_cluster.append(curr)
            else:
                clusters.append(current_cluster)
                current_cluster = [curr]

        clusters.append(current_cluster)
        return clusters

    @staticmethod
    def _files_are_sequential(a: Asset, b: Asset) -> bool:
        if not a.original_digits or not b.original_digits:
            return False
        try:
            num_a = int(a.original_digits)
            num_b = int(b.original_digits)
            return abs(num_a - num_b) == 1
        except ValueError:
            return False

    @staticmethod
    def _collect_with_xmps(assets: list[Asset]) -> list[Asset]:
        result = []
        for asset in assets:
            result.append(asset)
            if asset.xmp_companion:
                result.append(Asset(
                    source_path=asset.xmp_companion,
                    ext=".xmp",
                    asset_type=AssetType.IMAGE,
                    date_prefix=asset.date_prefix,
                    original_digits=asset.original_digits,
                    timestamp_epoch=asset.timestamp_epoch,
                ))
        return result