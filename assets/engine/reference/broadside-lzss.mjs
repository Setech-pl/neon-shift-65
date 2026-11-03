// Literal runs use commands $01-$7F. Match commands are 1LLLLLDD followed by
// the low distance byte: length=L+3, distance=((DD<<8)|low)+1. Zero terminates.
export function packBroadsideLzss(bytes) {
  const byteCount = bytes.length;
  const cost = new Uint32Array(byteCount + 1);
  const choiceLength = new Uint8Array(byteCount);
  const choiceDistance = new Uint16Array(byteCount);

  for (let input = byteCount - 1; input >= 0; input -= 1) {
    let bestCost = Number.MAX_SAFE_INTEGER;
    let bestLength = 1;
    let bestDistance = 0;

    const maximumLiteralLength = Math.min(127, byteCount - input);
    for (let length = 1; length <= maximumLiteralLength; length += 1) {
      const candidateCost = 1 + length + cost[input + length];
      if (candidateCost < bestCost) {
        bestCost = candidateCost;
        bestLength = length;
      }
    }

    const matchDistance = new Uint16Array(35);
    const windowStart = Math.max(0, input - 1024);
    for (let candidate = input - 1; candidate >= windowStart; candidate -= 1) {
      if (bytes[candidate] !== bytes[input]) continue;
      let length = 1;
      while (length < 34 && input + length < byteCount &&
        bytes[candidate + length] === bytes[input + length]) {
        length += 1;
      }
      for (let matched = 3; matched <= length; matched += 1) {
        if (matchDistance[matched] === 0) matchDistance[matched] = input - candidate;
      }
    }
    for (let length = 3; length <= 34; length += 1) {
      if (matchDistance[length] === 0) continue;
      const candidateCost = 2 + cost[input + length];
      if (candidateCost < bestCost) {
        bestCost = candidateCost;
        bestLength = length;
        bestDistance = matchDistance[length];
      }
    }

    cost[input] = bestCost;
    choiceLength[input] = bestLength;
    choiceDistance[input] = bestDistance;
  }

  const output = [];
  for (let input = 0; input < byteCount;) {
    const length = choiceLength[input];
    const matchDistance = choiceDistance[input];
    if (matchDistance === 0) {
      output.push(length, ...bytes.subarray(input, input + length));
    } else {
      const distance = matchDistance - 1;
      output.push(
        0x80 | ((length - 3) << 2) | (distance >>> 8),
        distance & 0xff,
      );
    }
    input += length;
  }
  output.push(0);
  return Buffer.from(output);
}

export function unpackBroadsideLzss(bytes) {
  const output = [];
  let input = 0;
  while (input < bytes.length) {
    const command = bytes[input++];
    if (command === 0) return Buffer.from(output);
    if ((command & 0x80) === 0) {
      if (input + command > bytes.length) throw new Error("Truncated broadside literal run");
      for (let index = 0; index < command; index += 1) output.push(bytes[input++]);
      continue;
    }
    if (input >= bytes.length) throw new Error("Truncated broadside match");
    const distance = 1 + ((command & 0x03) << 8) + bytes[input++];
    const length = 3 + ((command & 0x7c) >>> 2);
    if (distance > output.length) throw new Error("Broadside match precedes output");
    for (let index = 0; index < length; index += 1) {
      output.push(output[output.length - distance]);
    }
  }
  throw new Error("Broadside stream has no terminator");
}
