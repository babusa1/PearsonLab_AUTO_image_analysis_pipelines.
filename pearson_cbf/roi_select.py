"""Interactive multi-ROI selection for Q1c/Q1d."""

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector

from pearson_cbf.models import ROI


def select_rois_interactive(
    first_frame,
    *,
    min_roi_span: int = 5,
    rois_per_cell: int = 2,
    video_label: str = "",
) -> list[ROI]:
    """
    Draw ROIs on the first frame.

    Keys
    ----
    n : save drawn rectangle as new ROI
    s : save ROI on **same cell** as previous (use for Q1c — 2+ ROIs/ cell)
    u : undo last ROI
    q : finish
    """
    rois: list[ROI] = []
    current: dict[str, int] = {}
    roi_counter = 0
    last_cell_id = "cell_1"

    title = (
        f"{video_label}\n"
        "Drag box → press 'n' (new cell) or 's' (same cell, Q1c) → 'q' when done"
    )
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(first_frame, cmap="gray")
    ax.set_title(title, fontsize=10)

    def _add_roi(same_cell: bool) -> None:
        nonlocal roi_counter, last_cell_id
        if not current:
            return
        roi_counter += 1
        if same_cell and rois:
            cell_id = last_cell_id
        else:
            cell_num = (roi_counter - 1) // rois_per_cell + 1
            cell_id = f"cell_{cell_num}"
            last_cell_id = cell_id

        rois.append(
            ROI(
                x=current["x"],
                y=current["y"],
                w=max(current["w"], min_roi_span),
                h=max(current["h"], min_roi_span),
                label=f"roi_{roi_counter}",
                cell_id=cell_id,
            )
        )
        ax.add_patch(
            plt.Rectangle(
                (current["x"], current["y"]),
                current["w"],
                current["h"],
                fill=False,
                edgecolor="lime" if not same_cell else "cyan",
                linewidth=2,
            )
        )
        ax.set_title(f"{len(rois)} ROI(s) | last cell: {cell_id}")
        fig.canvas.draw_idle()
        current.clear()

    def onselect(eclick, erelease):
        if eclick.xdata is None or erelease.xdata is None:
            return
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        current["x"] = min(x1, x2)
        current["y"] = min(y1, y2)
        current["w"] = abs(x2 - x1)
        current["h"] = abs(y2 - y1)

    def on_key(event):
        if event.key == "n":
            _add_roi(same_cell=False)
        elif event.key == "s":
            _add_roi(same_cell=True)
        elif event.key == "u" and rois:
            rois.pop()
            ax.patches.clear()
            for r in rois:
                ax.add_patch(
                    plt.Rectangle(
                        (r.x, r.y), r.w, r.h, fill=False, edgecolor="lime", linewidth=2
                    )
                )
            fig.canvas.draw_idle()
        elif event.key == "q":
            plt.close(fig)

    RectangleSelector(
        ax,
        onselect,
        useblit=True,
        button=[1],
        minspanx=min_roi_span,
        minspany=min_roi_span,
        interactive=True,
    )
    fig.canvas.mpl_connect("key_press_event", on_key)
    plt.show()

    if not rois:
        raise ValueError("No ROIs saved. Draw a box, press 'n' or 's', then 'q'.")
    return rois
