from app.schemas.wafer import WaferDataset


def _grid(dataset: WaferDataset) -> list[list[str]]:
    grid = [
        ["."] * dataset.metadata.columns
        for _ in range(dataset.metadata.rows)
    ]
    for die in dataset.dies:
        grid[die.row][die.column] = die.source_char
    return grid


def _pat_notch(notch: str | None) -> str:
    values = {
        "UP": "Up(0)",
        "LEFT": "Left(90)",
        "DOWN": "Down(180)",
        "RIGHT": "Right(270)",
    }
    return values.get((notch or "").upper(), notch or "Unknown")


def serialize_pat(
    dataset: WaferDataset,
    *,
    filename: str = "SYNTH001.01.PAT",
    product_hint: str = "DEMO",
) -> str:
    metadata = dataset.metadata
    rows = ["".join(row) for row in _grid(dataset)]
    return "\n".join(
        [
            product_hint,
            metadata.lot_id or "SYNTH",
            f"{metadata.lot_id or 'SYNTH'}-{metadata.wafer_id or '00'}",
            filename,
            f"SOURCE NOTCH : {_pat_notch(metadata.notch)}",
            *rows,
        ]
    ) + "\n"


def _column_ruler(columns: int) -> list[str]:
    positions = list(range(1, columns + 1))
    return [
        "    " + "".join(str((value // 100) % 10) for value in positions),
        "    " + "".join(str((value // 10) % 10) for value in positions),
        "    " + "".join(str(value % 10) for value in positions),
    ]


def serialize_cp1(dataset: WaferDataset) -> str:
    metadata = dataset.metadata
    summary = dataset.summary
    grid = _grid(dataset)
    lines = [
        "[BOF]",
        f"PRODUCT ID     : {metadata.product_id or ''}",
        f"LOT ID         : {metadata.lot_id or ''}",
        f"WAFER ID       : {metadata.wafer_id or ''}",
        f"FLOW ID        : {metadata.flow_id or ''}",
        (
            "START TIME     : "
            + (metadata.start_time.strftime("%Y/%m/%d %H:%M:%S") if metadata.start_time else "")
        ),
        (
            "STOP TIME      : "
            + (metadata.stop_time.strftime("%Y/%m/%d %H:%M:%S") if metadata.stop_time else "")
        ),
        f"SUBCON         : {metadata.subcon or ''}",
        f"TESTER NAME    : {metadata.tester or ''}",
        f"TEST PROGRAM   : {metadata.test_program or ''}",
        "LOAD BOARD ID  : ",
        f"PROBE CARD ID  : {metadata.probe_card or ''}",
        "SITE NUM       : ",
        "DUT ID         : ",
        "DUT DIFF NUM   : ",
        "OPERATOR ID    : ",
        f"TESTED DIE     : {summary.tested_die}",
        f"PASS DIE       : {summary.pass_die}",
        f"YIELD          : {(summary.yield_ or 0.0) * 100:.2f}%",
        f"SOURCE NOTCH   : {metadata.notch or ''}",
        f"MAP ROW        : {metadata.rows}",
        f"MAP COLUMN     : {metadata.columns}",
        "MAP BIN LENGTH : 1",
        "SHIP           : N",
        "",
        "",
        "[SOFT BIN]",
        "        BINNAME, DIENUM,  YIELD, DESCRIPTION ",
    ]

    for item in sorted(dataset.bins, key=lambda entry: entry.bin):
        description = item.description or ""
        lines.append(
            f"    BIN, {item.bin:6d}, {item.count:6d}, "
            f"{item.percentage * 100:5.2f}%, {{[{description}]}}"
        )

    lines.extend(["", "[SOFT BIN MAP]", *_column_ruler(metadata.columns), ""])
    for row_number, row in enumerate(grid, start=1):
        cp_row = "".join(" " if char == "." else char for char in row)
        lines.append(f"{row_number:03d}  {cp_row}")

    lines.append(f"{metadata.rows + 1:03d}  " + (" " * metadata.columns))
    lines.extend(["", "[EXTENSION]", "", "[EOF]", ""])
    return "\n".join(lines)
