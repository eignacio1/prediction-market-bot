import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("depth_stats", pathlib.Path(__file__).parents[1] / "12_EXPLORATORY/thin_markets/depth_stats.py")
ds = importlib.util.module_from_spec(spec); spec.loader.exec_module(ds)


def test_metrics_fixed_point_schema():
    m = ds.metrics(*ds.parse({"orderbook_fp": {"yes_dollars": [["0.40", "30"], ["0.38", "10"]], "no_dollars": [["0.58", "20"]]}}))
    assert m["spread"] == 2 and m["d1"] == 50 and m["d5"] == 60 and m["side2"] == 20


def test_metrics_legacy_cents_and_empty_side():
    assert ds.metrics(*ds.parse({"orderbook": {"yes": [[40, 10]], "no": [[55, 7]]}}))["spread"] == 5
    assert ds.metrics(*ds.parse({"orderbook": {"yes": [[40, 10]], "no": []}})) is None
