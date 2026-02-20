"""Generate assets/app.ico from the crescent moon design."""
from PIL import Image, ImageDraw


def create_crescent(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = max(1, size // 16)
    draw.ellipse([pad, pad, size - pad, size - pad], fill="#c9a84c")
    offset = int(size * 0.25)
    draw.ellipse(
        [pad + offset, pad - max(1, size // 32), size - pad + offset, size - pad - max(1, size // 32)],
        fill=(0, 0, 0, 0),
    )
    return img


if __name__ == "__main__":
    sizes = [16, 32, 48, 64, 128, 256]
    imgs = [create_crescent(s) for s in sizes]
    imgs[0].save(
        "assets/app.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=imgs[1:],
    )
    print("Created assets/app.ico")
