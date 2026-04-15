from src.visualization.wifi_map_3d import AccessPointEstimate, _scale_sizes, render_wifi_scene


def test_scale_sizes_stronger_rssi_gets_bigger_nodes() -> None:
    sizes = _scale_sizes([-80.0, -60.0, -40.0])
    assert sizes[0] < sizes[1] < sizes[2]


def test_render_scene_contains_receiver_and_ap_traces() -> None:
    fig = render_wifi_scene(
        [
            AccessPointEstimate("ap-1", 1.0, 2.0, 3.0, -55.0, 4.2),
            AccessPointEstimate("ap-2", -2.5, 0.0, 1.2, -72.0, 7.0),
        ],
        ascii_overlay=True,
        distance_model_label="unit-test-model",
    )

    trace_names = [trace.name for trace in fig.data]
    assert "Receiver Origin" in trace_names
    assert "Access Points (node size ∝ RSSI)" in trace_names

    legend_blob = "".join(a.text for a in fig.layout.annotations)
    assert "unit-test-model" in legend_blob


def test_invalid_ap_entries_are_filtered_out() -> None:
    fig = render_wifi_scene(
        [
            AccessPointEstimate("good", 0.0, 1.0, 2.0, -60.0, 3.0),
            AccessPointEstimate("bad", float("nan"), 1.0, 2.0, -60.0, 3.0),
        ]
    )
    ap_trace = [t for t in fig.data if t.name == "Access Points (node size ∝ RSSI)"][0]
    assert len(ap_trace.x) == 1
