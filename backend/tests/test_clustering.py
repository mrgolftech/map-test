from app.analysis.clustering import connected_components


def test_connected_components_8_neighbor():
    coordinates = {
        (0, 0),
        (0, 1),
        (1, 1),
        (5, 5),
        (8, 8),
        (8, 9),
    }
    result = connected_components(coordinates, neighbor_mode=8)

    assert result.component_sizes == [3, 2, 1]
    assert result.component_count == 3
    assert result.largest_component == 3
    assert result.average_component_size == 2.0
    assert result.cluster_ratio == 0.5


def test_connected_components_empty():
    result = connected_components(set(), neighbor_mode=8)

    assert result.component_count == 0
    assert result.largest_component == 0
    assert result.average_component_size is None
    assert result.cluster_ratio is None
