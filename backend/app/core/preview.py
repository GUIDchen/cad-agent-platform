from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from ezdxf.addons.drawing import Frontend, RenderContext  # noqa: E402
from ezdxf.addons.drawing.config import ColorPolicy, Configuration  # noqa: E402
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend  # noqa: E402


def render(dxf_path: str | Path, png_path: str | Path, dpi: int = 160) -> Path:
    doc = ezdxf.readfile(dxf_path)
    fig = plt.figure(figsize=(11.7, 8.3))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    config = Configuration(color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=config).draw_layout(
        doc.modelspace(), finalize=True
    )
    out = Path(png_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out
