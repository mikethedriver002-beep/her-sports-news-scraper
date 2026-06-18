from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageOps

CORE = Path("scripts/generate_hsd_template_renderer_v3.py")


def load_core():
    spec = importlib.util.spec_from_file_location("hsd_renderer_v3_core", CORE)
    if not spec or not spec.loader:
        raise RuntimeError("Phase 5B renderer v3 core is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fast_background(module, size: Tuple[int, int], accent_a, accent_b, seed: int):
    width, height = size
    strip = Image.new("RGBA", (1, 96), (0, 0, 0, 255))
    strip_draw = ImageDraw.Draw(strip)
    for y in range(96):
        ratio = y / 95
        value = int(4 + 9 * ratio)
        strip_draw.point((0, y), fill=(value, value, min(21, value + 7), 255))
    image = strip.resize(size, Image.Resampling.BILINEAR)

    scale = 8
    small_width = max(1, width // scale)
    small_height = max(1, height // scale)
    glow = Image.new("RGBA", (small_width, small_height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow, "RGBA")
    glow_draw.ellipse(
        (-small_width // 2, -small_height // 5, int(small_width * 0.62), int(small_height * 0.58)),
        fill=(*accent_a, 92),
    )
    glow_draw.ellipse(
        (int(small_width * 0.43), int(small_height * 0.36), small_width + small_width // 2, small_height + small_height // 5),
        fill=(*accent_b, 86),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(14)).resize(size, Image.Resampling.BILINEAR)
    image = Image.alpha_composite(image, glow)
    draw = ImageDraw.Draw(image, "RGBA")
    for x in range(-height, width, 72):
        draw.line((x, 0, x + height, height), fill=(255, 255, 255, 9), width=2)
    return image


def fast_player_card(module, image: Image.Image, player: dict[str, Any], box, accent, label: str, mirror: bool = False):
    x, y, width, height = box
    module.panel(image, box, accent, (5, 6, 12, 205), 20)
    player_image = module.load_player(Path(module.clean(player.get("path"))))
    if player_image:
        if mirror:
            player_image = ImageOps.mirror(player_image)
        player_image.thumbnail((width - 24, height - 88), Image.Resampling.LANCZOS)
        paste_x = x + (width - player_image.width) // 2
        paste_y = y + height - 82 - player_image.height
        player_alpha = player_image.getchannel("A").filter(ImageFilter.GaussianBlur(12))
        shadow = Image.new("RGBA", player_image.size, (*accent, 0))
        shadow.putalpha(player_alpha.point(lambda value: min(105, value)))
        image.alpha_composite(shadow, (paste_x, paste_y + 8))
        image.alpha_composite(player_image, (paste_x, paste_y))

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rectangle((x + 1, y + height - 80, x + width - 1, y + height - 1), fill=(4, 4, 8, 225))
    draw.line((x + 18, y + height - 80, x + width - 18, y + height - 80), fill=(*accent, 190), width=2)
    name = module.clean(player.get("display_name")) or label
    selected_font = module.fit(draw, name.upper(), width - 36, 30, 18)
    draw.text((x + 18, y + height - 64), name.upper(), font=selected_font, fill=module.INK)
    draw.text((x + 18, y + height - 28), label.upper(), font=module.font(16, True), fill=accent)


def main() -> None:
    module = load_core()
    module.bg = lambda size, a, b, seed: fast_background(module, size, a, b, seed)
    module.player_card = lambda image, player, box, accent, label, mirror=False: fast_player_card(
        module, image, player, box, accent, label, mirror
    )
    module.main()


if __name__ == "__main__":
    main()
