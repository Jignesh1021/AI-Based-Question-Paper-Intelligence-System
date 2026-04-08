from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_powerbi_data(frame: pd.DataFrame, output_path: Path) -> str:
    export_frame = frame[["year", "subject", "topic", "marks", "difficulty"]].copy()
    export_frame.to_csv(output_path, index=False)
    return str(output_path)