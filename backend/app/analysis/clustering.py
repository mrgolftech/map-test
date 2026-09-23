from collections import deque

from app.schemas.analysis import ClusterStats


def connected_components(
    coordinates: set[tuple[int, int]],
    *,
    neighbor_mode: int,
) -> ClusterStats:
    if not coordinates:
        return ClusterStats(
            component_count=0,
            largest_component=0,
            average_component_size=None,
            cluster_ratio=None,
            component_sizes=[],
        )

    if neighbor_mode == 4:
        offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))
    else:
        offsets = tuple(
            (row_delta, column_delta)
            for row_delta in (-1, 0, 1)
            for column_delta in (-1, 0, 1)
            if not (row_delta == 0 and column_delta == 0)
        )

    remaining = set(coordinates)
    sizes: list[int] = []
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        size = 1

        while queue:
            row, column = queue.popleft()
            for row_delta, column_delta in offsets:
                neighbor = (row + row_delta, column + column_delta)
                if neighbor not in remaining:
                    continue
                remaining.remove(neighbor)
                queue.append(neighbor)
                size += 1

        sizes.append(size)

    sizes.sort(reverse=True)
    largest = sizes[0]
    total = sum(sizes)
    return ClusterStats(
        component_count=len(sizes),
        largest_component=largest,
        average_component_size=total / len(sizes),
        cluster_ratio=largest / total,
        component_sizes=sizes,
    )
