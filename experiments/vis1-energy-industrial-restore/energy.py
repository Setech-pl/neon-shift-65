"""Energy-only offline artwork overlay for the unchanged ENG3 compiler.

Historical device pixels and scene-map fragments are reused from ENG3's
frozen A3 vocabulary. The seam selection and dock check are VIS1 reconstruction.
No game code, publication logic, emulator palette or geometry is changed.
"""


def install(c):
    if c.themes.AREA != 1:
        return

    original_device = c.device
    original_intern = c.Strip.intern
    original_scene = c.scene
    current = {}
    # Asset palette: a muted brass ink serves equipment outside the board and
    # warm container insets. Emulator gamma/hue/contrast remain baseline values.
    c.themes.SPEC = dict(c.themes.SPEC, palette=[238, 156, 34, 230, 0])

    def scene(level, number, arrays):
        current['number'] = number
        return original_scene(level, number, arrays)

    def wall(mask, kind=0):
        p = c.blank()
        c.rect(p, 2, 4, 4, 8, 2)
        if mask & 1:
            c.rect(p, 2, 0, 4, 6, 2)
        if mask & 4:
            c.rect(p, 2, 10, 4, 6, 2)
        if mask & 2:
            c.rect(p, 4, 4, 4, 8, 2)
        if mask & 8:
            c.rect(p, 0, 4, 4, 8, 2)
        # Service collars/apertures repeat along rails, never cut a boundary.
        if mask == 5:
            c.line(p, 2, 4, 5, 4, 1)
            c.rect(p, 3, 8, 2, 2, 0)
        elif mask == 10:
            c.line(p, 2, 4, 5, 4, 1)
            c.rect(p, 3, 8, 2, 2, 0)
        else:
            c.line(p, 2, 4, 4, 4, 1)
        return c.tile(p)

    def device(kind, phase):
        p = original_device(kind, phase)
        if kind == 'installation':
            # Historical compiler cool() erased the authored vertical ribbing.
            # Reinstate inset ribs as black apertures in the metal face.
            for x in (5, 13, 21, 29):
                c.rect(p, x, 17, 1, 9, 0)
        return p

    def devices(old, number, level):
        # A3's original six positions match the accepted owner PNG.
        return old

    def background(pos, original, animated):
        if current['number'] == 1 and pos not in animated:
            row, col = divmod(pos, 40)
            p = c.blank(4, 8)
            if row == 2:
                c.line(p, 0, 4, 3, 4, 1)
            elif row == 23 and 28 <= col <= 39:
                c.line(p, 0, 4, 3, 4, 1)
                if col in (28, 39):
                    c.line(p, 0 if col == 28 else 3, 0,
                           0 if col == 28 else 3, 4, 1)
                # Vertical sockets connect the real four oscilloscope phases.
                if col in (33, 38):
                    c.line(p, 3 if col == 33 else 0, 0,
                           3 if col == 33 else 0, 7, 1)
            return bytes(sum(v << (6 - 2*x) for x, v in enumerate(r)) for r in p)
        # Restore the frozen scene-map composition, rather than ART3's stubs.
        return original

    def intern(self, data, who, selector=0):
        if who.startswith('background'):
            # The compiler has already mapped old scene ink to pixel1.
            # Choose dim brass PF3 ($E6), keeping yellow PF0 ($EE) for gameplay.
            # Only the existing glyph selector and asset palette are used.
            data = bytes(sum((3 if (v >> k) & 3 else 0) << k
                             for k in (0, 2, 4, 6)) for v in data)
            selector = 128
        return original_intern(self, data, who, selector)

    def floor_plan(rows, number, specs):
        result = {}
        for y, row in enumerate(rows):
            for x, ground in enumerate(row):
                if ground not in ' $@':
                    continue
                # A short horizontal copper seam, with air around dock markings.
                if any(abs(x - gx) + abs(y - gy) <= 1
                       for gy, rr in enumerate(rows)
                       for gx, v in enumerate(rr) if v in '.*+'):
                    continue
                if (x + 2 * y) % 3 == 0:
                    result[x, y] = (6, 8, 10)[(x + y) % 3]
        return result, []

    def container_pixels(docked=False, phase=None):
        # Same warm rectangular silhouette in both states; no cyan feet.
        p = c.blank()
        c.rect(p, 1, 1, 6, 13, 1)
        c.rect(p, 2, 2, 4, 11, 3)
        c.line(p, 1, 4, 6, 4, 1)
        c.line(p, 1, 10, 6, 10, 1)
        c.rect(p, 2, 5, 4, 5, 0)
        if docked:
            for x, y in ((2, 7), (3, 8), (4, 7), (5, 6)):
                p[y][x] = 2
        if phase is not None:
            p[2 + phase * 3][1] = 2
        return p

    c.wall = wall
    c.scene = scene
    c.device = device
    c.Strip.intern = intern
    c.container_pixels = container_pixels
    c.decoration.devices = devices
    c.decoration.background = background
    c.decoration.floor_plan = floor_plan
    c.decoration.VARIANT = 'VIS1-energy-industrial'
