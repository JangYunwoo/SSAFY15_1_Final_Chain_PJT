from __future__ import annotations

from io import BytesIO

from django.core.files.base import ContentFile

try:
    import numpy as np
    from PIL import Image, ImageDraw
except Exception:
    np = None
    Image = None
    ImageDraw = None


PALETTE = {
    0: (242, 245, 249),  # outside / empty
    1: (103, 137, 203),  # normal die
    2: (226, 87, 76),  # fail die
}


def render_wafer_map_png(wafer_map, cell_size=10, grid=True):
    if np is None or Image is None or wafer_map is None:
        return None

    data = np.array(wafer_map)
    if data.ndim != 2 or data.size == 0:
        return None
    unique_values = set(np.unique(data[~np.isnan(data)]).astype(int).tolist())
    if not unique_values.issubset(set(PALETTE)):
        low = np.percentile(data, 10)
        high = np.percentile(data, 92)
        quantized = np.ones(data.shape, dtype=float)
        quantized[data <= low] = 0
        quantized[data >= high] = 2
        data = quantized

    rows, cols = data.shape
    width = max(cols * cell_size, 1)
    height = max(rows * cell_size, 1)
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    for y in range(rows):
        for x in range(cols):
            raw_value = data[y, x]
            value = int(raw_value) if not np.isnan(raw_value) else 0
            color = PALETTE.get(value, (128, 145, 166))
            x0 = x * cell_size
            y0 = y * cell_size
            x1 = x0 + cell_size
            y1 = y0 + cell_size
            draw.rectangle([x0, y0, x1, y1], fill=color)
            if grid and cell_size >= 6:
                draw.rectangle([x0, y0, x1, y1], outline=(210, 216, 226))

    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, width - 1, height - 1], fill=255)

    wafer = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    wafer.paste(image.convert("RGBA"), (0, 0), mask)

    outline = ImageDraw.Draw(wafer)
    outline.ellipse([0, 0, width - 1, height - 1], outline=(79, 92, 112), width=2)

    canvas_size = max(width, height) + 24
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 0))
    canvas.paste(wafer, ((canvas_size - width) // 2, (canvas_size - height) // 2), wafer)

    output = BytesIO()
    canvas.save(output, format="PNG")
    return ContentFile(output.getvalue())
