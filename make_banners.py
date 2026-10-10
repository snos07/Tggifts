# -*- coding: utf-8 -*-
"""NEXUS banners: neon-purple 3D style, robot mascots, crystals. Output: 1280x640 JPG (drop-in for images/*.jpg)."""
import math, random, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scipy.spatial import Delaunay

W, H, S = 1280, 640, 2
CW, CH = W * S, H * S
F_BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
F_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
HANDLE = "NEXUS SHOP"
WHITE = (255, 255, 255)


def P(v):
    return int(round(v * S))


def new_mask(size=None):
    return Image.new("L", size or (CW, CH), 0)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def mix(c, k):
    return tuple(max(0, min(255, int(x * k))) for x in c)


def crop_box(size, bb, m):
    x0, y0, x1, y1 = bb
    return (max(0, x0 - m), max(0, y0 - m), min(size[0], x1 + m), min(size[1], y1 + m))


def glow(base, mask, color, radius, strength=1.0):
    bb = mask.getbbox()
    if not bb:
        return
    box = crop_box(base.size, bb, int(radius * S * 3))
    m = mask.crop(box).filter(ImageFilter.GaussianBlur(radius * S))
    m = m.point(lambda v: min(255, int(v * strength)))
    layer = Image.composite(Image.new("RGB", m.size, color), Image.new("RGB", m.size, (0, 0, 0)), m)
    base.paste(ImageChops.screen(base.crop(box), layer), box[:2])


def fill(base, mask, src, alpha=1.0):
    bb = mask.getbbox()
    if not bb:
        return
    m = mask.crop(bb)
    if alpha < 1:
        m = m.point(lambda v: int(v * alpha))
    img = Image.new("RGB", m.size, src) if isinstance(src, tuple) else src.crop(bb)
    base.paste(img, bb[:2], m)


def vgrad(w, h, stops):
    t = np.linspace(0, 1, h)
    ts = [s[0] for s in stops]
    arr = np.zeros((h, 1, 3))
    for c in range(3):
        arr[:, 0, c] = np.interp(t, ts, [s[1][c] for s in stops])
    return Image.fromarray(np.repeat(arr, w, axis=1).astype("uint8"))


def erode(mask, r):
    return mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v >= 250 else 0)


def dilate(mask, r):
    return mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: 255 if v > 6 else 0)


# ---------------------------------------------------------------- background
def background(accent, accent2, seed):
    yy, xx = np.mgrid[0:CH, 0:CW].astype("float32")
    nx, ny = xx / CW, yy / CH
    base = np.zeros((CH, CW, 3), "float32")
    base[:] = (9, 3, 28)

    def rad(cx, cy, rx, ry, col, k):
        d = np.sqrt(((nx - cx) / rx) ** 2 + ((ny - cy) / ry) ** 2)
        a = np.clip(1 - d, 0, 1) ** 2 * k
        base[...] += a[..., None] * np.array(col, "float32")

    rad(0.5, 0.40, 0.75, 0.85, (92, 44, 215), 0.95)
    rad(0.05, 0.05, 0.55, 0.65, accent2, 0.38)
    rad(0.97, 0.95, 0.55, 0.65, accent, 0.40)
    rad(0.5, 1.05, 0.7, 0.45, (150, 50, 210), 0.25)
    img = Image.fromarray(np.clip(base, 0, 255).astype("uint8"))

    rnd = random.Random(seed)
    # лучи света
    rays = new_mask()
    d = ImageDraw.Draw(rays)
    cx, cy = P(640), P(260)
    for i in range(16):
        a = rnd.uniform(0, math.tau)
        w = rnd.uniform(0.02, 0.06)
        R = P(1500)
        d.polygon([(cx, cy), (cx + R * math.cos(a - w), cy + R * math.sin(a - w)),
                   (cx + R * math.cos(a + w), cy + R * math.sin(a + w))], fill=rnd.randint(30, 70))
    rays = rays.filter(ImageFilter.GaussianBlur(P(5)))
    glow(img, rays, (140, 110, 255), 1, 1.0)

    # боке
    bok = new_mask()
    d = ImageDraw.Draw(bok)
    for _ in range(34):
        r = rnd.uniform(5, 26)
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        d.ellipse((P(x - r), P(y - r), P(x + r), P(y + r)), fill=rnd.randint(40, 150))
    glow(img, bok, accent2, 2.2, 1.0)
    return img


# ---------------------------------------------------------------- rocks
def rocks(base, pts, rim, seed):
    mask = new_mask()
    ImageDraw.Draw(mask).polygon([(P(x), P(y)) for x, y in pts], fill=255)
    bb = mask.getbbox()
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    rnd = random.Random(seed)
    pp = [(rnd.uniform(0, w), rnd.uniform(0, h)) for _ in range(55)]
    pp += [(0, 0), (w, 0), (0, h), (w, h), (w / 2, 0), (w / 2, h), (0, h / 2), (w, h / 2)]
    tri = Delaunay(pp)
    layer = Image.new("RGB", (w, h), (12, 5, 32))
    d = ImageDraw.Draw(layer)
    for s in tri.simplices:
        tp = [pp[i] for i in s]
        cxm = sum(p[0] for p in tp) / 3
        cym = sum(p[1] for p in tp) / 3
        k = rnd.uniform(0.2, 1.0) * (0.55 + 0.45 * (1 - cym / h))
        d.polygon(tp, fill=(int(11 + 26 * k), int(5 + 9 * k), int(30 + 52 * k)))
    base.paste(layer, bb[:2], mask.crop(bb))
    line = new_mask()
    ImageDraw.Draw(line).line([(P(x), P(y)) for x, y in pts], fill=255, width=P(2.6), joint="curve")
    glow(base, line, rim, 5, 2.5)
    fill(base, line, mix(rim, 1.5), 0.85)


# ---------------------------------------------------------------- gems / sparkles
def gem(base, cx, cy, size, rot, color):
    V = [(0, -1.0), (0.58, -0.32), (0.5, 0.45), (0, 1.0), (-0.5, 0.45), (-0.58, -0.32)]
    c, s = math.cos(rot), math.sin(rot)
    pts = [(P(cx + size * (x * c - y * s)), P(cy + size * (x * s + y * c))) for x, y in V]
    ctr = (P(cx + size * 0.04), P(cy - size * 0.06))
    sil = new_mask()
    ImageDraw.Draw(sil).polygon(pts, fill=255)
    glow(base, sil, color, size * 0.30, 1.5)
    d = ImageDraw.Draw(base)
    shades = [1.25, 0.95, 0.55, 0.38, 0.62, 1.05]
    for i in range(6):
        d.polygon([ctr, pts[i], pts[(i + 1) % 6]], fill=mix(color, shades[i]))
    edge = lerp(color, WHITE, 0.65)
    for i in range(6):
        d.line([pts[i], pts[(i + 1) % 6]], fill=edge, width=P(1.6))
    for i in (0, 2, 4):
        d.line([ctr, pts[i]], fill=lerp(color, WHITE, 0.4), width=P(1.0))
    hl = [pts[0], lerp_pt(pts[0], pts[1], 0.55), lerp_pt(ctr, pts[1], 0.4), lerp_pt(pts[0], pts[5], 0.55)]
    d.polygon(hl, fill=lerp(color, WHITE, 0.8))


def lerp_pt(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def sparkles(base, items, color):
    m = new_mask()
    d = ImageDraw.Draw(m)
    for x, y, r in items:
        q = r * 0.16
        pts = []
        for i in range(8):
            a = i * math.pi / 4 - math.pi / 2
            rr = r if i % 2 == 0 else q
            pts.append((P(x + rr * math.cos(a)), P(y + rr * math.sin(a))))
        d.polygon(pts, fill=255)
    glow(base, m, color, 4, 2.0)
    fill(base, m, (255, 250, 255))


# ---------------------------------------------------------------- neon icons
def icon_mask(kind, cx, cy, k=1.0):
    m = new_mask()
    d = ImageDraw.Draw(m)
    wd = P(8.5 * k)

    def T(x, y):
        return (P(cx + x * k), P(cy + y * k))

    def line(pts, closed=False):
        pp = [T(*p) for p in pts] + ([T(*pts[0])] if closed else [])
        d.line(pp, fill=255, width=wd, joint="curve")
        for p in pp:
            d.ellipse((p[0] - wd // 2, p[1] - wd // 2, p[0] + wd // 2, p[1] + wd // 2), fill=255)

    if kind == "crown":
        line([(-50, 32), (-50, -18), (-25, 6), (0, -34), (25, 6), (50, -18), (50, 32)], True)
        for x, y in ((-50, -26), (0, -43), (50, -26)):
            a = T(x, y)
            r = P(6 * k)
            d.ellipse((a[0] - r, a[1] - r, a[0] + r, a[1] + r), fill=255)
    elif kind == "bag":
        line([(-40, -12), (40, -12), (46, 46), (-46, 46)], True)
        a = T(0, -12)
        r = P(24 * k)
        d.arc((a[0] - r, a[1] - r - P(4 * k), a[0] + r, a[1] + r - P(4 * k)), 180, 360, fill=255, width=wd)
    elif kind == "mega":
        line([(-48, -14), (-6, -14), (42, -44), (42, 44), (-6, 14), (-48, 14)], True)
        line([(-32, 14), (-24, 46)])
        a = T(40, 0)
        r = P(34 * k)
        d.arc((a[0] - r, a[1] - r, a[0] + r, a[1] + r), -55, 55, fill=255, width=wd)
    elif kind == "code":
        line([(-18, -32), (-50, 0), (-18, 32)])
        line([(18, -32), (50, 0), (18, 32)])
        line([(9, -40), (-9, 40)])
    elif kind == "bolt":
        line([(10, -52), (-32, 6), (-4, 6), (-12, 52), (32, -8), (4, -8)], True)
    elif kind == "swap":
        line([(-48, -20), (48, -20)])
        line([(26, -38), (48, -20), (26, -2)])
        line([(48, 22), (-48, 22)])
        line([(-26, 4), (-48, 22), (-26, 40)])
    return m


def draw_icon(base, kind, cx, cy, k, glow_col):
    m = icon_mask(kind, cx, cy, k)
    glow(base, m, glow_col, 14, 2.6)
    glow(base, m, glow_col, 5, 3.0)
    fill(base, m, (244, 238, 255))


# ---------------------------------------------------------------- 3D title
def title(base, text, cx, cy, accent, max_w=1140, max_size=152):
    size = max_size
    while True:
        f = ImageFont.truetype(F_BLACK, P(size))
        bb = f.getbbox(text, stroke_width=P(size * 0.02))
        if (bb[2] - bb[0]) <= P(max_w) or size <= 60:
            break
        size -= 3
    sw = P(size * 0.022)
    mask = new_mask()
    ImageDraw.Draw(mask).text((P(cx), P(cy)), text, font=f, fill=255, anchor="mm", stroke_width=sw, stroke_fill=255)
    bb = mask.getbbox()
    dy = P(cy) - (bb[1] + bb[3]) // 2                   # центрируем по фактической высоте глифов
    mask = ImageChops.offset(mask, 0, dy)
    bb = mask.getbbox()
    D = P(size * 0.075)
    box = crop_box(base.size, bb, P(90) + D)
    lm = mask.crop(box)
    local = base.crop(box)
    lb = lm.getbbox()

    ext = new_mask(lm.size)
    for i in range(1, D + 1):
        ext = ImageChops.lighter(ext, ImageChops.offset(lm, 0, i))
    union = ImageChops.lighter(lm, ext)

    # тень
    sh = ImageChops.offset(union, 0, P(10)).filter(ImageFilter.GaussianBlur(P(9)))
    fill(local, sh, (0, 0, 0), 0.6)
    # неоновое свечение
    glow(local, union, accent, 22, 1.8)
    glow(local, union, lerp(accent, WHITE, 0.25), 7, 2.2)
    ring = ImageChops.subtract(dilate(union, P(3.2)), union)
    fill(local, ring, lerp(accent, WHITE, 0.45))
    # боковая грань
    top_c, bot_c = (96, 66, 226), (28, 12, 88)
    for i in range(D, 0, -1):
        t = i / D
        local.paste(lerp(top_c, bot_c, t), (0, i), lm)
    # лицевая грань
    h = local.size[1]
    t0, t1 = lb[1] / h, lb[3] / h
    face = vgrad(local.size[0], h, [(0, (255, 255, 255)), (t0, (255, 255, 255)), ((t0 + t1) / 2, (232, 222, 255)),
                                    (t1, (168, 140, 255)), (1, (168, 140, 255))])
    local.paste(face, (0, 0), lm)
    # блик сверху / тень снизу — объём
    hl = ImageChops.subtract(lm, ImageChops.offset(lm, 0, P(4.5))).filter(ImageFilter.GaussianBlur(P(1.2)))
    fill(local, hl.point(lambda v: min(255, v * 2)), WHITE)
    sd = ImageChops.subtract(lm, ImageChops.offset(lm, 0, -P(6))).filter(ImageFilter.GaussianBlur(P(2)))
    fill(local, sd, (112, 74, 226), 0.85)
    base.paste(local, box[:2])


# ---------------------------------------------------------------- pill
def pill(base, text, cx, cy, accent):
    f = ImageFont.truetype(F_BOLD, P(33))
    tw = f.getlength(text) / S
    w, h = tw + 170, 66
    m = new_mask()
    ImageDraw.Draw(m).rounded_rectangle((P(cx - w / 2), P(cy - h / 2), P(cx + w / 2), P(cy + h / 2)), radius=P(h / 2), fill=255)
    glow(base, m, accent, 12, 0.9)
    fill(base, m, (16, 7, 44), 0.82)
    ring = ImageChops.subtract(m, erode(m, P(1.6)))
    glow(base, ring, accent, 7, 2.6)
    fill(base, ring, lerp(accent, WHITE, 0.35))
    t = new_mask()
    d = ImageDraw.Draw(t)
    d.text((P(cx), P(cy) - P(1)), text, font=f, fill=255, anchor="mm")
    glow(base, t, accent, 5, 1.4)
    fill(base, t, (240, 233, 255))
    ar = new_mask()
    d = ImageDraw.Draw(ar)
    for sgn in (-1, 1):
        x = cx + sgn * (w / 2 - 34)
        d.polygon([(P(x + sgn * 7), P(cy)), (P(x - sgn * 5), P(cy - 11)), (P(x - sgn * 5), P(cy + 11))], fill=255)
    glow(base, ar, accent, 5, 2.4)
    fill(base, ar, lerp(accent, WHITE, 0.4))


# ---------------------------------------------------------------- shaded blob
def blob(base, mask, top=(255, 255, 255), bottom=(205, 190, 255), rim=(135, 105, 235), rimw=9, spec=True):
    bb = mask.getbbox()
    if not bb:
        return
    m = mask.crop(bb)
    w, h = m.size
    pad = int(rimw * S * 3)
    pm = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    pm.paste(m, (pad, pad))
    inv = ImageChops.invert(pm).filter(ImageFilter.GaussianBlur(rimw * S))
    rim_a = ImageChops.multiply(inv, pm).point(lambda v: min(255, int(v * 1.8)))
    face = Image.new("RGB", pm.size, (0, 0, 0))
    face.paste(vgrad(w, h, [(0, top), (1, bottom)]), (pad, pad))
    face = Image.composite(Image.new("RGB", pm.size, rim), face, rim_a)
    if spec:
        sp = Image.new("L", pm.size, 0)
        ImageDraw.Draw(sp).ellipse((pad + w * 0.08, pad + h * 0.05, pad + w * 0.58, pad + h * 0.30), fill=170)
        sp = ImageChops.multiply(sp.filter(ImageFilter.GaussianBlur(max(2, h * 0.04))), pm)
        face = Image.composite(Image.new("RGB", pm.size, WHITE), face, sp)
    base.paste(face, (bb[0] - pad, bb[1] - pad), pm)


# ---------------------------------------------------------------- robot
def robot(base, ox, oy, flip, accent, k=1.0):
    def T(x, y):
        return (P(ox + flip * x * k), P(oy + y * k))

    def rr(x0, y0, x1, y1, r):
        a, b = T(x0, y0), T(x1, y1)
        m = new_mask()
        ImageDraw.Draw(m).rounded_rectangle((min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])),
                                            radius=P(r * k), fill=255)
        return m

    def circ(x, y, r):
        a = T(x, y)
        m = new_mask()
        rp = P(r * k)
        ImageDraw.Draw(m).ellipse((a[0] - rp, a[1] - rp, a[0] + rp, a[1] + rp), fill=255)
        return m

    def cap(p0, p1, wd):
        a, b = T(*p0), T(*p1)
        m = new_mask()
        d = ImageDraw.Draw(m)
        d.line([a, b], fill=255, width=P(wd * k))
        rp = P(wd * k / 2)
        for p in (a, b):
            d.ellipse((p[0] - rp, p[1] - rp, p[0] + rp, p[1] + rp), fill=255)
        return m

    wave = cap((78, 128), (172, -52), 40)
    hand_w = circ(180, -66, 32)
    arm2 = cap((80, 128), (104, 228), 38)
    hand2 = circ(106, 238, 25)
    torso = rr(-84, 98, 84, 300, 58)
    head = rr(-142, -104, 142, 100, 82)
    union = new_mask()
    for mm in (wave, hand_w, arm2, torso, head):
        union = ImageChops.lighter(union, mm)
    glow(base, union, accent, 14, 1.0)
    glow(base, union, lerp(accent, WHITE, 0.3), 4, 0.9)

    body_top, body_bot = (232, 224, 255), (160, 138, 238)
    blob(base, wave, (230, 220, 255), (170, 150, 242), rimw=7)
    blob(base, arm2, (230, 220, 255), (170, 150, 242), rimw=7)
    blob(base, hand_w, (255, 255, 255), (214, 200, 255), rimw=7)
    blob(base, hand2, (255, 255, 255), (214, 200, 255), rimw=6)
    blob(base, torso, body_top, body_bot, rimw=12)

    # нагрудная панель с короной
    chest = rr(-46, 136, 46, 214, 24)
    fill(base, chest, (14, 6, 38))
    ring = ImageChops.subtract(chest, erode(chest, P(1.4)))
    glow(base, ring, accent, 4, 2.2)
    fill(base, ring, lerp(accent, WHITE, 0.4), 0.9)
    cr = icon_mask("crown", ox, oy + 175 * k, 0.33 * k)
    glow(base, cr, accent, 5, 2.5)
    fill(base, cr, (232, 220, 255))

    neck = rr(-32, 90, 32, 118, 12)
    fill(base, neck, (58, 32, 140))
    blob(base, head, (250, 246, 255), (192, 174, 250), rim=(118, 88, 224), rimw=13)

    # наушники
    for sgn in (-1, 1):
        ear = circ(sgn * 152, 6, 31)
        glow(base, ear, accent, 6, 1.6)
        blob(base, ear, (150, 108, 255), (84, 42, 196), rim=(60, 26, 150), rimw=6)
        core = circ(sgn * 152, 6, 13)
        fill(base, core, (200, 178, 255), 0.9)

    # визор
    visor = rr(-114, -66, 114, 66, 52)
    vb = visor.getbbox()
    fill(base, visor, vgrad(vb[2] - vb[0], vb[3] - vb[1], [(0, (26, 12, 70)), (1, (8, 3, 24))]))
    vr = ImageChops.subtract(visor, erode(visor, P(2.2)))
    glow(base, vr, accent, 6, 2.2)
    fill(base, vr, lerp(accent, (60, 30, 160), 0.35), 0.95)
    # блик на стекле
    gl = new_mask()
    a, b, c, e = T(-96, -48), T(-52, -48), T(-84, 30), T(-112, 30)
    ImageDraw.Draw(gl).polygon([a, b, c, e], fill=255)
    gl = ImageChops.multiply(gl, visor).filter(ImageFilter.GaussianBlur(P(2)))
    fill(base, gl, (150, 120, 255), 0.18)

    # глаза ^ ^
    eyes = new_mask()
    d = ImageDraw.Draw(eyes)
    for sgn in (-1, 1):
        a = T(sgn * 48, 14)
        r = P(25 * k)
        d.arc((a[0] - r, a[1] - r, a[0] + r, a[1] + r), 188, 352, fill=255, width=P(14 * k))
        for ang in (188, 352):
            px = a[0] + r * math.cos(math.radians(ang))
            py = a[1] + r * math.sin(math.radians(ang))
            rp = P(7 * k)
            d.ellipse((px - rp, py - rp, px + rp, py + rp), fill=255)
    glow(base, eyes, (150, 100, 255), 14, 2.0)
    glow(base, eyes, (180, 140, 255), 5, 2.2)
    fill(base, eyes, (226, 206, 255))

    # румянец
    bl = new_mask()
    d = ImageDraw.Draw(bl)
    for sgn in (-1, 1):
        a = T(sgn * 78, 34)
        d.ellipse((a[0] - P(17 * k), a[1] - P(8 * k), a[0] + P(17 * k), a[1] + P(8 * k)), fill=255)
    glow(base, bl, (255, 90, 200), 6, 1.6)


# ---------------------------------------------------------------- scene
def banner(name, text, icon, accent, accent2, gem_col, seed, out_dir):
    img = background(accent, accent2, seed)

    # дальние кристаллы
    far = [(560, 548, 20, 0.3), (845, 560, 26, -0.25), (430, 470, 16, 0.5)]
    for x, y, s, r in far:
        gem(img, x, y, s, r, gem_col)

    # скалы
    rocks(img, [(-40, 330), (20, 350), (62, 440), (128, 500), (205, 548), (262, 600), (300, 690), (-40, 690)],
          lerp(accent, (150, 120, 255), 0.6), seed + 1)
    rocks(img, [(1320, 330), (1260, 350), (1218, 440), (1152, 500), (1075, 548), (1018, 600), (980, 690), (1320, 690)],
          lerp(accent, (150, 120, 255), 0.6), seed + 2)
    rocks(img, [(300, 700), (350, 626), (430, 650), (520, 598), (620, 632), (720, 600), (820, 640), (905, 608),
                (960, 700)], lerp(accent2, (120, 90, 255), 0.4), seed + 3)

    # близкие кристаллы
    near = [(92, 84, 64, -0.35), (212, 50, 32, 0.45), (150, 178, 24, 0.2), (1226, 226, 40, 0.35),
            (1112, 42, 28, -0.4), (338, 372, 18, 0.2), (944, 388, 22, -0.3)]
    for x, y, s, r in near:
        gem(img, x, y, s, r, gem_col)

    robot(img, 228, 414, -1, accent)
    robot(img, 1052, 414, 1, accent)

    pill(img, HANDLE, 640, 352, accent)
    title(img, text, 640, 214, accent)
    draw_icon(img, icon, 1168, 92, 0.95, accent)

    random.seed(seed)
    sp = [(random.uniform(40, 1240), random.uniform(20, 600), random.uniform(5, 13)) for _ in range(14)]
    sp += [(1050, 150, 15), (240, 150, 12), (700, 480, 9)]
    sparkles(img, sp, lerp(accent, WHITE, 0.4))

    # виньетка и зерно
    arr = np.asarray(img).astype("float32")
    yy, xx = np.mgrid[0:CH, 0:CW].astype("float32")
    d = np.sqrt(((xx / CW - 0.5) / 0.75) ** 2 + ((yy / CH - 0.5) / 0.8) ** 2)
    vig = 1 - 0.38 * np.clip(d, 0, 1.2) ** 2.2
    arr *= vig[..., None]
    arr += np.random.default_rng(seed).normal(0, 2.0, arr.shape[:2])[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype("uint8")).resize((W, H), Image.LANCZOS)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".jpg")
    img.save(path, quality=93, subsampling=0, optimize=True)
    return path


SPECS = {
    "main":    ("ГЛАВНОЕ МЕНЮ", "crown", (122, 92, 255), (70, 90, 255), (110, 190, 255), 11),
    "shop":    ("МАГАЗИН",      "bag",   (206, 80, 255), (120, 70, 255), (230, 130, 255), 22),
    "ads":     ("РЕКЛАМА",      "mega",  (80, 140, 255), (60, 90, 255),  (110, 210, 255), 33),
    "dev":     ("РАЗРАБОТКА",   "code",  (70, 170, 255), (80, 80, 255),  (110, 220, 255), 44),
    "mod":     ("MOD ULTRA",    "bolt",  (186, 76, 255), (90, 60, 255),  (200, 130, 255), 55),
    "convert": ("КОНВЕРТАЦИЯ",  "swap",  (96, 120, 255), (60, 180, 230), (110, 230, 235), 66),
}

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/out"
    names = sys.argv[2:] or list(SPECS)
    for n in names:
        t, ic, a, a2, g, sd = SPECS[n]
        print(banner(n, t, ic, a, a2, g, sd, out), flush=True)
