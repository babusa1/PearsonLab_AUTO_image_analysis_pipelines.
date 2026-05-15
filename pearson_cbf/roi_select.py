"""
Interactive multi-ROI selection (matplotlib)
============================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Displays the first video frame and lets the user draw rectangular ROIs over
beating cilia. Supports multiple ROIs per cell for Q1c (within-cell synchrony).

Keyboard shortcuts
------------------
n : save ROI and assign to a new cell (or next cell in sequence)
s : save ROI on the **same cell** as the previous ROI (required for Q1c)
u : undo last ROI
q : finish and close window
"""

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
    Open an interactive window to define one or more ROIs.

    Parameters
    ----------
    first_frame
        2D image (first frame of the stack).
    min_roi_span
        Minimum width/height in pixels.
    rois_per_cell
        Default grouping when using ``n`` (pairs of ROIs → cell_1, cell_2, ...).
    video_label
        Shown in the window title.

    Returns
    -------
    list[ROI]
        At least one ROI; raises ``ValueError`` if user quits without saving any.
    """
    rois: list[ROI] = []
    pending_rect: dict[str, int] = {}
    roi_count = 0
    last_cell_id = "cell_1"

    title = (
        f"{video_label}\n"
        "Drag box → 'n' (new cell) or 's' (same cell, Q1c) → 'q' when done"
    )
    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(first_frame, cmap="gray")
    ax.set_title(title, fontsize=10)

    def _commit_roi(same_cell: bool) -> None:
        nonlocal roi_count, last_cell_id
        if not pending_rect:
            return
        roi_count += 1
        if same_cell and rois:
            cell_id = last_cell_id
        else:
            cell_num = (roi_count - 1) // rois_per_cell + 1
            cell_id = f"cell_{cell_num}"
            last_cell_id = cell_id

        rois.append(
            ROI(
                x=pending_rect["x"],
                y=pending_rect["y"],
                w=max(pending_rect["w"], min_roi_span),
                h=max(pending_rect["h"], min_roi_span),
                label=f"roi_{roi_count}",
                cell_id=cell_id,
            )
        )
        color = "cyan" if same_cell else "lime"
        ax.add_patch(
            plt.Rectangle(
                (pending_rect["x"], pending_rect["y"]),
                pending_rect["w"],
                pending_rect["h"],
                fill=False,
                edgecolor=color,
                linewidth=2,
            )
        )
        ax.set_title(f"{len(rois)} ROI(s) saved | cell: {cell_id}")
        fig.canvas.draw_idle()
        pending_rect.clear()

    def _on_rectangle_select(eclick, erelease):
        if eclick.xdata is None or erelease.xdata is None:
            return
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        pending_rect["x"] = min(x1, x2)
        pending_rect["y"] = min(y1, y2)
        pending_rect["w"] = abs(x2 - x1)
        pending_rect["h"] = abs(y2 - y1)

    def _on_key(event):
        if event.key == "n":
            _commit_roi(same_cell=False)
        elif event.key == "s":
            _commit_roi(same_cell=True)
        elif event.key == "u" and rois:
            rois.pop()
            ax.patches.clear()
            for saved in rois:
                ax.add_patch(
                    plt.Rectangle(
                        (saved.x, saved.y),
                        saved.w,
                        saved.h,
                        fill=False,
                        edgecolor="lime",
                        linewidth=2,
                    )
                )
            fig.canvas.draw_idle()
        elif event.key == "q":
            plt.close(fig)

    RectangleSelector(
        ax,
        _on_rectangle_select,
        useblit=True,
        button=[1],
        minspanx=min_roi_span,
        minspany=min_roi_span,
        interactive=True,
    )
    fig.canvas.mpl_connect("key_press_event", _on_key)
    plt.show()

    if not rois:
        raise ValueError("No ROIs saved. Draw a box, press 'n' or 's', then 'q'.")
    return rois
