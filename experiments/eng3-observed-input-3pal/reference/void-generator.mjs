import fs from "node:fs";
import { packBroadsideLzss, unpackBroadsideLzss } from "./broadside-lzss.mjs";

const BITMAP_WIDTH = 320;
const BITMAP_HEIGHT = 192;
export const LOADER_DISPLAY_LIST_ADDRESS = 0x3c00;
const BITMAP_BYTES_PER_ROW = 40;
const BITMAP_BYTES = BITMAP_BYTES_PER_ROW * BITMAP_HEIGHT;
const PACKED_BITMAP_RESIDENCY_BYTES = 1997;
const COLOR_REGISTERS = ["COLBK", "COLPF1", "COLPF2"];
const ANTIC_MODE_NUMBERS = new Map([
  ["ANTIC E", 0x0e],
  ["ANTIC F", 0x0f],
]);

function assertInteger(value, name, minimum, maximum) {
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new Error(`${name} must be an integer from ${minimum} to ${maximum}`);
  }
}

function parseByte(value, name) {
  if (typeof value !== "string" || !/^\$[0-9A-Fa-f]{2}$/.test(value)) {
    throw new Error(`${name} must use ca65 byte notation such as $0E`);
  }
  return Number.parseInt(value.slice(1), 16);
}

function parseWord(value, name) {
  if (typeof value !== "string" || !/^\$[0-9A-Fa-f]{4}$/.test(value)) {
    throw new Error(`${name} must use ca65 word notation such as $4010`);
  }
  return Number.parseInt(value.slice(1), 16);
}

// In ANTIC F normal interpretation, a clear bitmap bit uses COLPF2 directly.
// A set bit combines COLPF2's hue with COLPF1's luminance. Keeping this in one
// function makes source validation and preview rendering follow the hardware.
export function anticFRegisterForBitmapBit(registers, bitmapBit) {
  const colpf1 = registers.get("COLPF1");
  const colpf2 = registers.get("COLPF2");
  if (!Number.isInteger(colpf1) || !Number.isInteger(colpf2)) {
    throw new Error("ANTIC F mapping requires COLPF1 and COLPF2 byte values");
  }
  return bitmapBit ? (colpf2 & 0xf0) | (colpf1 & 0x0e) : colpf2;
}

// ANTIC E maps each two-bit bitmap pixel directly to a playfield register.
// The mixed-mode loader uses only 0 (COLBK) and 2 (COLPF1), so COLPF0 does not
// need to be changed or represented in the loader palette source.
export function anticERegisterForBitmapPixel(registers, bitmapPixel) {
  assertInteger(bitmapPixel, "ANTIC E bitmap pixel", 0, 3);
  const register = ["COLBK", "COLPF0", "COLPF1", "COLPF2"][bitmapPixel];
  const value = registers.get(register);
  if (!Number.isInteger(value)) {
    throw new Error(`ANTIC E pixel ${bitmapPixel} requires ${register}`);
  }
  return value;
}

function validatePattern(pattern, name) {
  if (
    !Array.isArray(pattern) ||
    pattern.length === 0 ||
    pattern.length > 8 ||
    pattern.some((row) => (
      typeof row !== "string" ||
      row.length === 0 ||
      row.length > 8 ||
      row.length !== pattern[0].length ||
      /[^01]/.test(row)
    ))
  ) {
    throw new Error(`${name} must be a rectangular binary pattern up to 8x8`);
  }
}

function validateFont(font, name) {
  assertInteger(font.letterSpacing, `${name}.letterSpacing`, 0, 8);
  assertInteger(font.spaceAdvance, `${name}.spaceAdvance`, 1, 16);
  if (!font.glyphs || typeof font.glyphs !== "object") {
    throw new Error(`${name}.glyphs must be an object`);
  }
  for (const [character, rows] of Object.entries(font.glyphs)) {
    if (character.length !== 1 || !Array.isArray(rows) || rows.length === 0) {
      throw new Error(`${name} contains an invalid glyph`);
    }
    const width = rows[0].length;
    if (
      width === 0 ||
      rows.some((row) => row.length !== width || /[^01]/.test(row))
    ) {
      throw new Error(`${name}.${character} must be a rectangular binary glyph`);
    }
  }
}

export function validateLoaderBitmapDefinition(definition) {
  if (definition.formatVersion !== 2) {
    throw new Error("Unsupported loader bitmap formatVersion");
  }
  const bitmap = definition.bitmap;
  if (
    bitmap?.width !== BITMAP_WIDTH ||
    bitmap?.height !== BITMAP_HEIGHT ||
    bitmap?.bytesPerRow !== BITMAP_BYTES_PER_ROW ||
    bitmap?.bitOrder !== "msb-left"
  ) {
    throw new Error("Loader bitmap must be 320x192, 40 bytes per row, MSB first");
  }

  const bitmapAddress = parseWord(bitmap.address, "bitmap.address");
  const secondLmsAddress = parseWord(
    bitmap.secondLmsAddress,
    "bitmap.secondLmsAddress",
  );
  assertInteger(
    bitmap.secondLmsLine,
    "bitmap.secondLmsLine",
    1,
    BITMAP_HEIGHT - 1,
  );
  if (bitmapAddress !== 0x4010 || secondLmsAddress !== 0x5000) {
    throw new Error("Loader bitmap must use $4010 and the second LMS at $5000");
  }
  if (
    bitmapAddress + bitmap.secondLmsLine * BITMAP_BYTES_PER_ROW !==
      secondLmsAddress ||
    secondLmsAddress +
      (BITMAP_HEIGHT - bitmap.secondLmsLine) * BITMAP_BYTES_PER_ROW !==
      0x5e10
  ) {
    throw new Error("Loader bitmap LMS split must occupy $4010-$5E0F");
  }

  if (
    definition.timing?.palFrames !== 250 ||
    definition.timing?.palHz !== 50
  ) {
    throw new Error("Loader timing must be exactly 250 frames at 50 Hz");
  }
  if (
    !Array.isArray(definition.paletteZones) ||
    definition.paletteZones.length !== 3
  ) {
    throw new Error("Loader bitmap must define title, ship, and studio zones");
  }

  let nextLine = 0;
  for (const zone of definition.paletteZones) {
    if (
      zone.startLine !== nextLine ||
      zone.endLine < zone.startLine ||
      zone.endLine >= BITMAP_HEIGHT
    ) {
      throw new Error("Loader palette zones must cover contiguous scanlines");
    }
    const values = new Map();
    for (const register of COLOR_REGISTERS) {
      values.set(
        register,
        parseByte(zone.registers?.[register], `${zone.name}.${register}`),
      );
    }
    const foreground = parseByte(zone.foreground, `${zone.name}.foreground`);
    const modeNumber = ANTIC_MODE_NUMBERS.get(zone.displayMode);
    if (!Number.isInteger(modeNumber)) {
      throw new Error(`${zone.name}.displayMode must be ANTIC E or ANTIC F`);
    }
    assertInteger(
      zone.foregroundPixel,
      `${zone.name}.foregroundPixel`,
      1,
      zone.displayMode === "ANTIC E" ? 3 : 1,
    );
    const effectiveForeground = zone.displayMode === "ANTIC F"
      ? anticFRegisterForBitmapBit(values, zone.foregroundPixel)
      : anticERegisterForBitmapPixel(values, zone.foregroundPixel);
    if (effectiveForeground !== foreground) {
      throw new Error(
        `${zone.name} ${zone.displayMode} registers do not produce its foreground`,
      );
    }
    if (
      values.get("COLBK") !== 0 ||
      (zone.displayMode === "ANTIC F" && (values.get("COLPF2") & 0x0f) !== 0)
    ) {
      throw new Error(
        `${zone.name} must use the mode-appropriate black background`,
      );
    }
    nextLine = zone.endLine + 1;
  }
  if (nextLine !== BITMAP_HEIGHT) {
    throw new Error("Loader palette zones must cover all 192 scanlines");
  }

  if (!definition.patterns || typeof definition.patterns !== "object") {
    throw new Error("Loader bitmap source must define deterministic patterns");
  }
  for (const [name, pattern] of Object.entries(definition.patterns)) {
    validatePattern(pattern, `patterns.${name}`);
  }
  if (!definition.fonts || typeof definition.fonts !== "object") {
    throw new Error("Loader bitmap source must define its pixel fonts");
  }
  for (const [name, font] of Object.entries(definition.fonts)) {
    validateFont(font, `fonts.${name}`);
  }
  if (!Array.isArray(definition.elements) || definition.elements.length === 0) {
    throw new Error("Loader bitmap source must define drawable elements");
  }
  return definition;
}

export function loadLoaderBitmapDefinition(sourcePath) {
  return validateLoaderBitmapDefinition(
    JSON.parse(fs.readFileSync(sourcePath, "utf8")),
  );
}

function patternBit(definition, patternName, x, y) {
  const pattern = definition.patterns[patternName ?? "solid"];
  if (!pattern) {
    throw new Error(`Unknown loader bitmap pattern: ${patternName}`);
  }
  const row = pattern[((y % pattern.length) + pattern.length) % pattern.length];
  return row[((x % row.length) + row.length) % row.length] === "1" ? 1 : 0;
}

function setPixel(pixels, x, y, value) {
  if (x < 0 || x >= BITMAP_WIDTH || y < 0 || y >= BITMAP_HEIGHT) {
    return;
  }
  pixels[y * BITMAP_WIDTH + x] = value ? 1 : 0;
}

function paintPixel(pixels, definition, element, x, y) {
  const value = element.value ?? 1;
  setPixel(
    pixels,
    x,
    y,
    value === 0 ? 0 : patternBit(definition, element.pattern, x, y),
  );
}

function drawRect(pixels, definition, element) {
  for (let y = element.y; y < element.y + element.height; y += 1) {
    for (let x = element.x; x < element.x + element.width; x += 1) {
      paintPixel(pixels, definition, element, x, y);
    }
  }
}

function drawLineSegment(pixels, definition, element, x0, y0, x1, y1) {
  let x = x0;
  let y = y0;
  const dx = Math.abs(x1 - x0);
  const sx = x0 < x1 ? 1 : -1;
  const dy = -Math.abs(y1 - y0);
  const sy = y0 < y1 ? 1 : -1;
  let error = dx + dy;
  const width = element.width ?? 1;
  const radiusBefore = Math.floor((width - 1) / 2);
  const radiusAfter = width - radiusBefore - 1;

  while (true) {
    for (
      let offsetY = -radiusBefore;
      offsetY <= radiusAfter;
      offsetY += 1
    ) {
      for (
        let offsetX = -radiusBefore;
        offsetX <= radiusAfter;
        offsetX += 1
      ) {
        paintPixel(pixels, definition, element, x + offsetX, y + offsetY);
      }
    }
    if (x === x1 && y === y1) {
      break;
    }
    const doubled = error * 2;
    if (doubled >= dy) {
      error += dy;
      x += sx;
    }
    if (doubled <= dx) {
      error += dx;
      y += sy;
    }
  }
}

function drawLine(pixels, definition, element) {
  for (let index = 1; index < element.points.length; index += 1) {
    drawLineSegment(
      pixels,
      definition,
      element,
      element.points[index - 1][0],
      element.points[index - 1][1],
      element.points[index][0],
      element.points[index][1],
    );
  }
}

function pointInsidePolygon(x, y, points) {
  let inside = false;
  for (
    let current = 0, previous = points.length - 1;
    current < points.length;
    previous = current, current += 1
  ) {
    const [currentX, currentY] = points[current];
    const [previousX, previousY] = points[previous];
    if (
      (currentY > y) !== (previousY > y) &&
      x <
        ((previousX - currentX) * (y - currentY)) /
          (previousY - currentY) +
          currentX
    ) {
      inside = !inside;
    }
  }
  return inside;
}

function drawPolygon(pixels, definition, element) {
  const xs = element.points.map(([x]) => x);
  const ys = element.points.map(([, y]) => y);
  const minimumX = Math.max(0, Math.floor(Math.min(...xs)));
  const maximumX = Math.min(BITMAP_WIDTH - 1, Math.ceil(Math.max(...xs)));
  const minimumY = Math.max(0, Math.floor(Math.min(...ys)));
  const maximumY = Math.min(BITMAP_HEIGHT - 1, Math.ceil(Math.max(...ys)));

  for (let y = minimumY; y <= maximumY; y += 1) {
    for (let x = minimumX; x <= maximumX; x += 1) {
      if (pointInsidePolygon(x + 0.5, y + 0.5, element.points)) {
        paintPixel(pixels, definition, element, x, y);
      }
    }
  }
  if (element.outline) {
    drawLine(pixels, definition, {
      ...element,
      points: [...element.points, element.points[0]],
      pattern: "solid",
      value: 1,
      width: 1,
    });
  }
}

function drawText(pixels, definition, element) {
  const font = definition.fonts[element.font];
  if (!font) {
    throw new Error(`Unknown loader bitmap font: ${element.font}`);
  }
  const scaleX = element.scaleX ?? 1;
  const scaleY = element.scaleY ?? 1;
  const letterSpacing = element.letterSpacing ?? font.letterSpacing;
  let cursorX = element.x;

  for (const character of element.text) {
    if (character === " ") {
      cursorX += font.spaceAdvance * scaleX;
      continue;
    }
    const glyph = font.glyphs[character];
    if (!glyph) {
      throw new Error(`Missing loader bitmap glyph: ${character}`);
    }
    for (let glyphY = 0; glyphY < glyph.length; glyphY += 1) {
      for (let glyphX = 0; glyphX < glyph[glyphY].length; glyphX += 1) {
        if (glyph[glyphY][glyphX] !== "1") {
          continue;
        }
        for (let pixelY = 0; pixelY < scaleY; pixelY += 1) {
          for (let pixelX = 0; pixelX < scaleX; pixelX += 1) {
            paintPixel(
              pixels,
              definition,
              element,
              cursorX + glyphX * scaleX + pixelX,
              element.y + glyphY * scaleY + pixelY,
            );
          }
        }
      }
    }
    cursorX += glyph[0].length * scaleX + letterSpacing;
  }
}

function drawStars(pixels, definition, element) {
  for (const [x, y] of element.points) {
    paintPixel(pixels, definition, element, x, y);
    paintPixel(pixels, definition, element, x - 1, y);
    paintPixel(pixels, definition, element, x + 1, y);
    paintPixel(pixels, definition, element, x, y - 1);
    paintPixel(pixels, definition, element, x, y + 1);
  }
}

function drawElement(pixels, definition, element) {
  if (element.kind === "rect") {
    drawRect(pixels, definition, element);
  } else if (element.kind === "polygon") {
    drawPolygon(pixels, definition, element);
  } else if (element.kind === "line") {
    drawLine(pixels, definition, element);
  } else if (element.kind === "repeatLine") {
    for (let index = 0; index < element.count; index += 1) {
      drawLine(pixels, definition, {
        ...element,
        kind: "line",
        points: [
          [element.x + index * element.stepX, element.y1],
          [element.x + index * element.stepX, element.y2],
        ],
      });
    }
  } else if (element.kind === "pixelText") {
    drawText(pixels, definition, element);
  } else if (element.kind === "stars") {
    drawStars(pixels, definition, element);
  } else {
    throw new Error(`Unsupported loader bitmap element kind: ${element.kind}`);
  }
}

export function encodeLoaderBitmapPixels(pixels, paletteZones = undefined) {
  if (
    !(pixels instanceof Uint8Array) ||
    pixels.length !== BITMAP_WIDTH * BITMAP_HEIGHT
  ) {
    throw new Error("Loader bitmap pixels must contain exactly 320x192 entries");
  }
  const bytes = new Uint8Array(BITMAP_BYTES);
  for (let y = 0; y < BITMAP_HEIGHT; y += 1) {
    const zone = paletteZones?.find(
      ({ startLine, endLine }) => y >= startLine && y <= endLine,
    );
    const displayMode = zone?.displayMode ?? "ANTIC F";
    for (
      let byteColumn = 0;
      byteColumn < BITMAP_BYTES_PER_ROW;
      byteColumn += 1
    ) {
      let value = 0;
      if (displayMode === "ANTIC F") {
        for (let bit = 0; bit < 8; bit += 1) {
          value |=
            (pixels[y * BITMAP_WIDTH + byteColumn * 8 + bit] & 1) << (7 - bit);
        }
      } else if (displayMode === "ANTIC E") {
        for (let pixel = 0; pixel < 4; pixel += 1) {
          const sourceOffset = y * BITMAP_WIDTH + byteColumn * 8 + pixel * 2;
          const isForeground = pixels[sourceOffset] | pixels[sourceOffset + 1];
          value |= (isForeground ? zone.foregroundPixel : 0) << (6 - pixel * 2);
        }
      } else {
        throw new Error(`Unsupported loader display mode: ${displayMode}`);
      }
      bytes[y * BITMAP_BYTES_PER_ROW + byteColumn] = value;
    }
  }
  return bytes;
}

export function packLoaderPackBits(bytes) {
  const packed = [];
  let offset = 0;
  while (offset < bytes.length) {
    let runLength = 1;
    while (
      offset + runLength < bytes.length &&
      bytes[offset + runLength] === bytes[offset] &&
      runLength < 127
    ) {
      runLength += 1;
    }
    if (runLength >= 3) {
      packed.push(0x80 | runLength, bytes[offset]);
      offset += runLength;
      continue;
    }

    const literalStart = offset;
    offset += runLength;
    while (offset < bytes.length && offset - literalStart < 127) {
      let nextRun = 1;
      while (
        offset + nextRun < bytes.length &&
        bytes[offset + nextRun] === bytes[offset] &&
        nextRun < 127
      ) {
        nextRun += 1;
      }
      if (nextRun >= 3) {
        break;
      }
      offset += nextRun;
    }
    packed.push(offset - literalStart, ...bytes.subarray(literalStart, offset));
  }
  packed.push(0);
  return Uint8Array.from(packed);
}

export function unpackLoaderPackBits(packed, expectedLength = BITMAP_BYTES) {
  const output = [];
  let offset = 0;
  while (offset < packed.length) {
    const command = packed[offset];
    offset += 1;
    if (command === 0) {
      break;
    }
    if (command & 0x80) {
      const length = command & 0x7f;
      if (length === 0 || offset >= packed.length) {
        throw new Error("Invalid repeated loader bitmap command");
      }
      output.push(...new Array(length).fill(packed[offset]));
      offset += 1;
    } else {
      if (offset + command > packed.length) {
        throw new Error("Invalid literal loader bitmap command");
      }
      output.push(...packed.subarray(offset, offset + command));
      offset += command;
    }
  }
  if (output.length !== expectedLength || offset !== packed.length) {
    throw new Error(
      `Loader bitmap expands to ${output.length} bytes instead of ${expectedLength}`,
    );
  }
  return Uint8Array.from(output);
}

export function compileLoaderBitmap(definition) {
  validateLoaderBitmapDefinition(definition);
  const pixels = new Uint8Array(BITMAP_WIDTH * BITMAP_HEIGHT);
  for (const element of definition.elements) {
    drawElement(pixels, definition, element);
  }
  const paletteZones = definition.paletteZones.map((zone) => ({
    ...zone,
    modeNumber: ANTIC_MODE_NUMBERS.get(zone.displayMode),
    foregroundValue: parseByte(zone.foreground, `${zone.name}.foreground`),
    values: new Map(
      COLOR_REGISTERS.map((register) => [
        register,
        parseByte(zone.registers[register], `${zone.name}.${register}`),
      ]),
    ),
  }));
  const bitmapBytes = encodeLoaderBitmapPixels(pixels, paletteZones);
  const packedBitmap = packBroadsideLzss(bitmapBytes);
  if (packedBitmap.length > PACKED_BITMAP_RESIDENCY_BYTES) {
    throw new Error(
      `Loader bitmap needs ${packedBitmap.length} packed bytes; ` +
      `reserved residency is ${PACKED_BITMAP_RESIDENCY_BYTES}`,
    );
  }
  if (!unpackBroadsideLzss(packedBitmap).equals(Buffer.from(bitmapBytes))) {
    throw new Error("Loader bitmap LZSS round trip failed");
  }

  return {
    width: BITMAP_WIDTH,
    height: BITMAP_HEIGHT,
    bytesPerRow: BITMAP_BYTES_PER_ROW,
    bitmapAddress: parseWord(definition.bitmap.address, "bitmap.address"),
    secondLmsLine: definition.bitmap.secondLmsLine,
    secondLmsAddress: parseWord(
      definition.bitmap.secondLmsAddress,
      "bitmap.secondLmsAddress",
    ),
    pixels,
    bitmapBytes,
    packedBitmap,
    paletteZones,
    dliLines: paletteZones.slice(1).map((zone) => zone.startLine - 1),
    durationFrames: definition.timing.palFrames,
    landmarks: definition.landmarks,
  };
}

export function loaderBitmapPixelValueAt(compiled, x, y) {
  assertInteger(x, "loader bitmap x", 0, BITMAP_WIDTH - 1);
  assertInteger(y, "loader bitmap y", 0, BITMAP_HEIGHT - 1);
  const zone = compiled.paletteZones.find(
    ({ startLine, endLine }) => y >= startLine && y <= endLine,
  );
  if (!zone) {
    throw new Error(`Loader bitmap line ${y} has no palette zone`);
  }
  const value = compiled.bitmapBytes[
    y * BITMAP_BYTES_PER_ROW + Math.floor(x / 8)
  ];
  if (zone.displayMode === "ANTIC F") {
    return (value >> (7 - (x & 7))) & 1;
  }
  return (value >> (6 - Math.floor((x & 7) / 2) * 2)) & 3;
}

function byteLines(bytes) {
  const lines = [];
  for (let offset = 0; offset < bytes.length; offset += 16) {
    const values = [...bytes.subarray(offset, offset + 16)]
      .map((value) => `$${value.toString(16).padStart(2, "0").toUpperCase()}`)
      .join(",");
    lines.push(`    .byte ${values}`);
  }
  return lines;
}

function constantPrefix(name) {
  return `LOADER_${name.replaceAll(/[^A-Za-z0-9]/g, "_").toUpperCase()}`;
}

export function createLoaderDisplayListBytes(
  compiled,
  displayListAddress,
) {
  const bytes = [0x70, 0x70, 0x70];
  for (let line = 0; line < BITMAP_HEIGHT; line += 1) {
    const zone = compiled.paletteZones.find(
      ({ startLine, endLine }) => line >= startLine && line <= endLine,
    );
    const hasLms = line === 0 || line === compiled.secondLmsLine;
    const hasDli = compiled.dliLines.includes(line);
    bytes.push(zone.modeNumber | (hasLms ? 0x40 : 0) | (hasDli ? 0x80 : 0));
    if (hasLms) {
      const address =
        line === 0 ? compiled.bitmapAddress : compiled.secondLmsAddress;
      bytes.push(address & 0xff, address >> 8);
    }
  }
  bytes.push(0x41, displayListAddress & 0xff, displayListAddress >> 8);
  return Uint8Array.from(bytes);
}

export function renderLoaderCa65Include(compiled) {
  const lines = [
    "; Generated from assets/graphics/loader-bitmap.json by scripts/loader-assets.mjs.",
    "; Do not edit this file by hand.",
    `LOADER_BITMAP_ADDRESS = $${compiled.bitmapAddress.toString(16).toUpperCase()}`,
    `LOADER_BITMAP_SECOND_ADDRESS = $${compiled.secondLmsAddress.toString(16).toUpperCase()}`,
    `LOADER_BITMAP_SECOND_LINE = ${compiled.secondLmsLine}`,
    `LOADER_BITMAP_WIDTH = ${compiled.width}`,
    `LOADER_BITMAP_HEIGHT = ${compiled.height}`,
    `LOADER_BITMAP_BYTES_PER_ROW = ${compiled.bytesPerRow}`,
    `LOADER_BITMAP_BYTES = ${compiled.bitmapBytes.length}`,
    `LOADER_BITMAP_PACKED_BYTES = ${compiled.packedBitmap.length}`,
    `LOADER_BITMAP_PACKED_RESIDENCY_BYTES = ${PACKED_BITMAP_RESIDENCY_BYTES}`,
    `LOADER_DURATION_FRAMES = ${compiled.durationFrames}`,
    `LOADER_DLI_COUNT = ${compiled.dliLines.length}`,
    "",
  ];

  for (const zone of compiled.paletteZones) {
    const prefix = constantPrefix(zone.name);
    lines.push(
      `${prefix}_START_LINE = ${zone.startLine}`,
      `${prefix}_END_LINE = ${zone.endLine}`,
      `${prefix}_ANTIC_MODE = $${zone.modeNumber.toString(16).toUpperCase()}`,
      `${prefix}_FOREGROUND = $${zone.foregroundValue.toString(16).padStart(2, "0").toUpperCase()}`,
    );
    for (const register of COLOR_REGISTERS) {
      const value = zone.values.get(register);
      lines.push(
        `${prefix}_${register} = $${value.toString(16).padStart(2, "0").toUpperCase()}`,
      );
    }
  }

  lines.push("", "loader_bitmap_lzss:");
  lines.push(...byteLines(compiled.packedBitmap));
  lines.push(
    "loader_bitmap_lzss_end:",
    "    .res LOADER_BITMAP_PACKED_RESIDENCY_BYTES-(loader_bitmap_lzss_end-loader_bitmap_lzss),$00",
  );
  lines.push("", "loader_display_list = LOADER_DISPLAY_LIST_ADDRESS");
  lines.push(
    '.assert (loader_display_list & $FC00) = ((loader_display_list + LOADER_DISPLAY_LIST_BYTES - 1) & $FC00), error, "loader display list crosses an ANTIC 1 KiB boundary"',
    '.assert LOADER_BITMAP_BYTES = 7680, error, "loader bitmap size must be 7680 bytes"',
    '.assert LOADER_BITMAP_ADDRESS + LOADER_BITMAP_SECOND_LINE * LOADER_BITMAP_BYTES_PER_ROW = LOADER_BITMAP_SECOND_ADDRESS, error, "loader first LMS range is invalid"',
    '.assert LOADER_BITMAP_SECOND_ADDRESS + (LOADER_BITMAP_HEIGHT - LOADER_BITMAP_SECOND_LINE) * LOADER_BITMAP_BYTES_PER_ROW = $5E10, error, "loader bitmap end is invalid"',
    '.assert LOADER_DURATION_FRAMES = 250, error, "loader duration must be 250 PAL frames"',
    "",
  );
  return `${lines.join("\n")}\n`;
}

export function renderLoaderDisplayListCa65Include(compiled) {
  const displayListPrefix = createLoaderDisplayListBytes(compiled, 0).subarray(0, -3);
  const packedPrefix = packBroadsideLzss(displayListPrefix).subarray(0, -1);
  return [
    "; Generated compact loader display list source. Do not edit.",
    `LOADER_DISPLAY_LIST_ADDRESS = $${LOADER_DISPLAY_LIST_ADDRESS.toString(16).toUpperCase()}`,
    `LOADER_DISPLAY_LIST_BYTES = ${displayListPrefix.length + 3}`,
    `LOADER_DISPLAY_LIST_LZSS_BYTES = ${packedPrefix.length + 5}`,
    ".macro EMIT_LOADER_DISPLAY_LIST_LZSS",
    ...byteLines(packedPrefix),
    "    .byte $03,$41,<loader_display_list,>loader_display_list,$00",
    ".endmacro",
    "",
  ].join("\n");
}

export const loaderBitmapConstants = {
  width: BITMAP_WIDTH,
  height: BITMAP_HEIGHT,
  bytesPerRow: BITMAP_BYTES_PER_ROW,
  bytes: BITMAP_BYTES,
};
