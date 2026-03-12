from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("缺少依赖 Pillow。请先执行: pip install -r requirements-python.txt")
    sys.exit(1)


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
OUTPUT_MARKERS = (".cleaned.", "_cleaned.")
MASK_CONFIGS = (
    {"size": 48, "file_name": "mask_48.png", "margin": 32},
    {"size": 96, "file_name": "mask_96.png", "margin": 64},
)


@dataclass
class Mask:
    width: int
    height: int
    margin: int
    pixels: list[int]


@dataclass
class ImageTask:
    original_path: Path
    extension: str
    relative_path: str


def script_root() -> Path:
    return Path(__file__).resolve().parent


def get_mask_path(file_name: str) -> Path:
    return script_root() / "public" / "assets" / file_name


def should_skip_file(file_name: str) -> bool:
    lower_name = file_name.lower()
    return any(marker in lower_name for marker in OUTPUT_MARKERS)


def is_internal_resource(path: Path, root_dir: Path) -> bool:
    try:
        relative_parts = path.relative_to(root_dir).parts
    except ValueError:
        return False

    if not relative_parts:
        return False

    return relative_parts[0].lower() == "public"


def scan_directory(root_dir: Path) -> list[ImageTask]:
    results: list[ImageTask] = []

    for path in root_dir.rglob("*"):
        if not path.is_file():
            continue

        if is_internal_resource(path, root_dir):
            continue

        extension = path.suffix.lower()
        if extension not in IMAGE_EXTENSIONS or should_skip_file(path.name):
            continue

        results.append(
            ImageTask(
                original_path=path,
                extension=extension,
                relative_path=path.relative_to(root_dir).as_posix(),
            )
        )

    return results


def load_masks() -> dict[int, Mask]:
    masks: dict[int, Mask] = {}

    for config in MASK_CONFIGS:
        mask_path = get_mask_path(config["file_name"])
        with Image.open(mask_path) as image:
            rgba = image.convert("RGBA")
            width, height = rgba.size
            source_pixels = list(rgba.getdata())

        processed_pixels: list[int] = []
        for red, green, blue, _alpha in source_pixels:
            luminance = round(0.299 * red + 0.587 * green + 0.114 * blue)
            processed_pixels.extend((255, 255, 255, luminance))

        masks[config["size"]] = Mask(
            width=width,
            height=height,
            margin=config["margin"],
            pixels=processed_pixels,
        )

    return masks


def select_mask(width: int, height: int, masks: dict[int, Mask]) -> Mask | None:
    return masks.get(96 if width > 1024 and height > 1024 else 48)


def pixel_brightness(pixels: list[int], index: int) -> float:
    return 0.299 * pixels[index] + 0.587 * pixels[index + 1] + 0.114 * pixels[index + 2]


def detect_watermark(raw_pixels: list[int], mask: Mask, image_width: int, image_height: int) -> bool:
    offset_x = image_width - mask.width - mask.margin
    offset_y = image_height - mask.height - mask.margin

    if offset_x < 0 or offset_y < 0:
        return False

    watermark_brightness = 0.0
    watermark_pixel_count = 0.0
    surrounding_brightness = 0.0
    surrounding_pixel_count = 0
    strong_mask_brightness = 0.0
    strong_mask_pixel_count = 0
    weak_mask_brightness = 0.0
    weak_mask_pixel_count = 0
    near_white_strong_count = 0

    for mask_y in range(mask.height):
        for mask_x in range(mask.width):
            image_x = offset_x + mask_x
            image_y = offset_y + mask_y
            image_index = (image_y * image_width + image_x) * 4
            mask_index = (mask_y * mask.width + mask_x) * 4
            alpha = mask.pixels[mask_index + 3] / 255.0
            brightness = pixel_brightness(raw_pixels, image_index)

            if alpha > 0.1:
                watermark_brightness += brightness * alpha
                watermark_pixel_count += alpha

            if alpha >= 0.35:
                strong_mask_brightness += brightness
                strong_mask_pixel_count += 1
                if brightness >= 245:
                    near_white_strong_count += 1
            elif alpha <= 0.05:
                weak_mask_brightness += brightness
                weak_mask_pixel_count += 1

    sample_size = min(mask.width, mask.height)

    for image_y in range(offset_y, min(offset_y + mask.height, image_height)):
        for image_x in range(max(0, offset_x - sample_size), offset_x):
            image_index = (image_y * image_width + image_x) * 4
            surrounding_brightness += pixel_brightness(raw_pixels, image_index)
            surrounding_pixel_count += 1

    for image_y in range(max(0, offset_y - sample_size), offset_y):
        for image_x in range(offset_x, min(offset_x + mask.width, image_width)):
            image_index = (image_y * image_width + image_x) * 4
            surrounding_brightness += pixel_brightness(raw_pixels, image_index)
            surrounding_pixel_count += 1

    average_watermark = watermark_brightness / watermark_pixel_count if watermark_pixel_count > 0 else 0.0
    average_surrounding = surrounding_brightness / surrounding_pixel_count if surrounding_pixel_count > 0 else 128.0
    average_strong_mask = strong_mask_brightness / strong_mask_pixel_count if strong_mask_pixel_count > 0 else average_watermark
    average_weak_mask = weak_mask_brightness / weak_mask_pixel_count if weak_mask_pixel_count > 0 else average_surrounding
    near_white_ratio = near_white_strong_count / strong_mask_pixel_count if strong_mask_pixel_count > 0 else 0.0

    uplift_vs_surrounding = average_watermark - average_surrounding
    uplift_vs_local_box = average_strong_mask - average_weak_mask

    if average_surrounding >= 235:
        surrounding_threshold = 1.6
        local_box_threshold = 1.2
    elif average_surrounding >= 220:
        surrounding_threshold = 2.2
        local_box_threshold = 1.5
    elif average_surrounding >= 200:
        surrounding_threshold = 3.0
        local_box_threshold = 1.9
    elif average_surrounding >= 180:
        surrounding_threshold = 4.5
        local_box_threshold = 2.4
    else:
        surrounding_threshold = 10.0
        local_box_threshold = 3.0

    if uplift_vs_surrounding >= 10.0:
        return True

    if uplift_vs_surrounding >= surrounding_threshold and uplift_vs_local_box >= local_box_threshold:
        return True

    if average_surrounding >= 220 and uplift_vs_local_box >= 2.2 and near_white_ratio >= 0.32:
        return True

    return False


def clamp_color(value: float) -> int:
    return max(0, min(255, round(value)))


def reverse_alpha_blend(raw_pixels: list[int], mask: Mask, image_width: int, image_height: int) -> None:
    offset_x = image_width - mask.width - mask.margin
    offset_y = image_height - mask.height - mask.margin

    for mask_y in range(mask.height):
        for mask_x in range(mask.width):
            image_x = offset_x + mask_x
            image_y = offset_y + mask_y

            if image_x < 0 or image_y < 0 or image_x >= image_width or image_y >= image_height:
                continue

            image_index = (image_y * image_width + image_x) * 4
            mask_index = (mask_y * mask.width + mask_x) * 4
            alpha = min(mask.pixels[mask_index + 3] / 255.0, 0.99)

            if alpha < 0.01:
                continue

            inverse_alpha = 1.0 - alpha
            if inverse_alpha < 0.01:
                continue

            raw_pixels[image_index] = clamp_color((raw_pixels[image_index] - 255 * alpha) / inverse_alpha)
            raw_pixels[image_index + 1] = clamp_color((raw_pixels[image_index + 1] - 255 * alpha) / inverse_alpha)
            raw_pixels[image_index + 2] = clamp_color((raw_pixels[image_index + 2] - 255 * alpha) / inverse_alpha)


def save_image(raw_pixels: list[int], image: Image.Image, output_path: Path, extension: str) -> None:
    result = Image.frombytes("RGBA", image.size, bytes(raw_pixels))

    if extension in {".jpg", ".jpeg"}:
        result = result.convert("RGB")
        result.save(output_path, format="JPEG", quality=100)
        return

    if extension == ".webp":
        result.save(output_path, format="WEBP", quality=100)
        return

    result.save(output_path, format="PNG")


def process_image(task: ImageTask, masks: dict[int, Mask]) -> tuple[str, str]:
    with Image.open(task.original_path) as source_image:
        rgba = source_image.convert("RGBA")
        raw_pixels = list(rgba.tobytes())
        width, height = rgba.size

        mask = select_mask(width, height, masks)
        if mask is None:
            return "skipped", "没有可用的 mask"

        if not detect_watermark(raw_pixels, mask, width, height):
            return "skipped", "未检测到 Nano Banana 水印"

        reverse_alpha_blend(raw_pixels, mask, width, height)
        save_image(raw_pixels, rgba, task.original_path, task.extension)
        return "cleaned", f"已覆盖 {task.original_path.name}"


def write_log(root_dir: Path, entries: list[tuple[str, str, str]]) -> None:
    log_path = root_dir / "NanoBananaBatchRemover.log"
    lines = [
        f"time={datetime.now().isoformat()}",
        f"root={root_dir}",
    ]
    lines.extend(f"{status}\t{relative_path}\t{detail}" for status, relative_path, detail in entries)
    lines.append("")
    log_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    root_dir = script_root()
    print(f"扫描目录: {root_dir}")

    try:
        masks = load_masks()
    except Exception as error:
        print(f"加载 mask 失败: {error}")
        return 1

    tasks = scan_directory(root_dir)
    print(f"发现图片: {len(tasks)} 张")

    entries: list[tuple[str, str, str]] = []
    cleaned_count = 0
    skipped_count = 0
    error_count = 0

    for index, task in enumerate(tasks, start=1):
        print(f"[{index}/{len(tasks)}] 处理中: {task.relative_path}")
        try:
            status, detail = process_image(task, masks)
            entries.append((status, task.relative_path, detail))
            if status == "cleaned":
                cleaned_count += 1
            else:
                skipped_count += 1
            print(f"    -> {detail}")
        except Exception as error:
            error_count += 1
            detail = str(error)
            entries.append(("error", task.relative_path, detail))
            print(f"    -> 失败: {detail}")

    write_log(root_dir, entries)

    print("")
    print("处理完成")
    print(f"成功清理: {cleaned_count}")
    print(f"跳过无水印: {skipped_count}")
    print(f"处理失败: {error_count}")
    print(f"日志文件: {root_dir / 'NanoBananaBatchRemover.log'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())