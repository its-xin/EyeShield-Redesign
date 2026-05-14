"""Unified application branding: same logo as the login window everywhere."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

try:
    from .app_paths import ICONS_DIR
except ImportError:  # pragma: no cover
    from app_paths import ICONS_DIR


def resolve_unified_logo_png_path() -> str:
    """Prefer Logo.png (same asset as login screen)."""
    for name in ("Logo.png", "logo.png"):
        p = ICONS_DIR / name
        if p.is_file():
            return str(p)
    return ""


def resolve_fallback_svg_icon_path() -> str:
    p = ICONS_DIR / "eyeshield_icon.svg"
    return str(p) if p.is_file() else ""


def _render_svg_to_pixmap(svg_path: str, size: int) -> QPixmap:
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QPixmap()
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    return QPixmap.fromImage(image)


def build_application_icon() -> QIcon:
    """
    Multi-resolution icon for window/taskbar (Logo.png when present), matching login branding.
    """
    icon = QIcon()
    png_path = resolve_unified_logo_png_path()
    if png_path:
        base = QPixmap(png_path)
        if not base.isNull():
            for size in (16, 20, 24, 32, 40, 48, 64, 128, 256):
                icon.addPixmap(
                    base.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                )
            return icon

    svg_path = resolve_fallback_svg_icon_path()
    if svg_path:
        for size in (16, 24, 32, 48, 64, 128, 256):
            pm = _render_svg_to_pixmap(svg_path, size)
            if not pm.isNull():
                icon.addPixmap(pm)
        if not icon.isNull():
            return icon

    return icon


def render_unified_brand_pixmap(side: int, *, svg_tint_hex: str | None = None) -> QPixmap:
    """
    Sidebar-sized pixmap: full-color PNG when available; otherwise tinted or plain SVG.
    svg_tint_hex: when PNG is missing, optional #RRGGBB tint for vector fallback (sidebar contrast).
    """
    png_path = resolve_unified_logo_png_path()
    if png_path:
        pm = QPixmap(png_path)
        if not pm.isNull():
            return pm.scaled(side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    svg_path = resolve_fallback_svg_icon_path()
    if not svg_path:
        return QPixmap()

    if not svg_tint_hex:
        return _render_svg_to_pixmap(svg_path, max(side * 2, 64)).scaled(
            side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )

    try:
        import re

        with open(svg_path, "r", encoding="utf-8") as f:
            svg_text = f.read()

        def _replace_paint(match: re.Match[str]) -> str:
            attr = match.group(1)
            value = match.group(2)
            if value.lower() in {"none", "transparent"}:
                return match.group(0)
            return f'{attr}="{svg_tint_hex}"'

        svg_text = re.sub(r'(fill|stroke)=["\']([^"\']+)["\']', _replace_paint, svg_text, flags=re.IGNORECASE)
        data = QByteArray(svg_text.encode("utf-8"))
        renderer = QSvgRenderer(data)
        if not renderer.isValid():
            return _render_svg_to_pixmap(svg_path, max(side * 2, 64)).scaled(
                side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        dim = max(side * 2, 64)
        image = QImage(dim, dim, QImage.Format_ARGB32_Premultiplied)
        image.fill(0)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return QPixmap.fromImage(image).scaled(
            side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
    except OSError:
        return _render_svg_to_pixmap(svg_path, max(side * 2, 64)).scaled(
            side, side, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
