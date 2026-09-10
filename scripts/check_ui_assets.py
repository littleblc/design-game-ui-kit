"""Read-only sprite QA. Requires Pillow; does not perform matting or repair."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw


def check_assets(asset_root, manifest, out):
    root, out = Path(asset_root).resolve(), Path(out).resolve()
    entries = json.loads(Path(manifest).read_text(encoding="utf-8-sig"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("Manifest must be a nonempty JSON array")
    # Keep generated reports outside source assets, including symlink resolution.
    if out == root or root in out.parents:
        raise ValueError("QA output must be outside the asset root")
    rows, previews, names, files = [], [], set(), set()
    for index, entry in enumerate(entries):
        row = {"index": index, "errors": [], "warnings": []}
        rows.append(row)
        errors, warnings = row["errors"], row["warnings"]
        if not isinstance(entry, dict):
            errors.append("Entry must be an object")
            continue
        name, file = entry.get("name"), entry.get("file")
        row.update(name=name, file=file)
        if not isinstance(name, str) or not name:
            errors.append("Missing string name")
        elif name in names:
            errors.append("Duplicate name")
        else:
            names.add(name)
        if not isinstance(file, str) or not file:
            errors.append("Missing relative file path")
            continue
        path = (root / file).resolve()
        if Path(file).is_absolute() or root not in path.parents:
            errors.append("File path escapes asset root or is absolute")
            continue
        if path in files:
            errors.append("Duplicate asset file")
        files.add(path)
        mode = entry.get("alpha_mode", "cutout")
        if "alpha_mode" not in entry:
            warnings.append("alpha_mode missing; assumed cutout. Classify by intended use")
        if mode not in ("cutout", "opaque", "translucent"):
            errors.append("Invalid alpha_mode")
        try:
            with Image.open(path) as source:
                if source.format != "PNG":
                    errors.append("Final raster asset must be PNG")
                has_alpha = "A" in source.getbands() or "transparency" in source.info
                im = source.convert("RGBA")
        except (OSError, ValueError) as exc:
            errors.append(f"Cannot read image: {exc}")
            continue
        width, height = im.size
        row.update(width=width, height=height, alpha_mode=mode)
        for key, actual in (("width", width), ("height", height)):
            if key in entry and entry[key] != actual:
                errors.append(f"{key} differs from manifest")
        border = entry.get("border", [0, 0, 0, 0])
        if (not isinstance(border, list) or len(border) != 4
                or any(type(x) is not int or x < 0 for x in border)):
            errors.append("border must contain four nonnegative integers [L,B,R,T]")
        elif border[0] + border[2] >= width or border[1] + border[3] >= height:
            errors.append("border leaves no positive-sized stretch center")
        alpha = im.getchannel("A")
        amin, amax = alpha.getextrema()
        hist = alpha.histogram()
        row.update(alpha_min=amin, alpha_max=amax, transparent_pixels=hist[0],
                   partial_alpha_pixels=sum(hist[1:255]), bounds=alpha.getbbox())
        if amax == 0:
            errors.append("Image is completely invisible")
        if mode in ("cutout", "translucent") and not has_alpha:
            errors.append("No actual transparency channel; visible checkerboards are not alpha")
        if mode == "cutout" and amin != 0:
            errors.append("Cutout has no fully transparent exterior pixels")
        if mode == "translucent" and amin == 255:
            errors.append("Translucent asset is fully opaque")
        if mode == "cutout" and alpha.getbbox():
            x0, y0, x1, y1 = alpha.getbbox()
            if x0 == 0 or y0 == 0 or x1 == width or y1 == height:
                warnings.append("Visible pixels touch canvas edge; inspect clipping or intentional bleed")
        rows[-1] = row
        previews.append((str(name or index), im))

    out.mkdir(parents=True, exist_ok=True)
    sheets = []
    for page_start in range(0, len(previews), 12):
        batch = previews[page_start:page_start + 12]
        sheet = Image.new("RGB", (1020, ((len(batch) + 2) // 3) * 200), "#dedede")
        draw = ImageDraw.Draw(sheet)
        for offset, (name, im) in enumerate(batch):
            x, y = (offset % 3) * 340, (offset // 3) * 200
            label = name.encode("ascii", "replace").decode("ascii")
            draw.text((x + 6, y + 5), label[:48], fill="#111111")
            thumb = im.copy()
            thumb.thumbnail((156, 154), Image.Resampling.LANCZOS)
            for column, color in enumerate(("#242735", "#faf5e9")):
                left = x + 6 + column * 166
                draw.rectangle((left, y + 28, left + 160, y + 192), fill=color)
                sheet.paste(thumb, (left + (160 - thumb.width) // 2,
                                   y + 28 + (164 - thumb.height) // 2), thumb)
        filename = f"alpha-review-{page_start // 12 + 1:02d}.png"
        sheet.save(out / filename)
        sheets.append(filename)
    report = {
        "asset_count": len(rows),
        "error_count": sum(len(r["errors"]) for r in rows),
        "warning_count": sum(len(r["warnings"]) for r in rows),
        "limitations": "Checks metadata and alpha, not matte cleanliness, visual fidelity or Unity behavior. Inspect sheets and full-resolution assets.",
        "review_sheets": sheets, "assets": rows,
    }
    (out / "qa-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True, help="Separate directory outside asset root")
    args = parser.parse_args()
    try:
        report = check_assets(args.asset_root, args.manifest, args.out)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Input error: {exc}\n")
    print(f"Assets: {report['asset_count']}; errors: {report['error_count']}; warnings: {report['warning_count']}")
    return 1 if report["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
