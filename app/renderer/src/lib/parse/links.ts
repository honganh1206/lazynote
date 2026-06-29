export interface LinkSegment {
  type: "text" | "link";
  value: string;
  displayValue: string;
  fullUrl?: string;
}

// Match URLs but stop before trailing ) when the URL is preceded by (
const URL_REGEX = /https?:\/\/[^\s()]+(?:\([^\s()]*\)[^\s()]*)*|https?:\/\/[^\s]+/g;

export function parseLinks(text: string): LinkSegment[] {
  const segments: LinkSegment[] = [];
  let lastIndex = 0;

  for (const match of text.matchAll(URL_REGEX)) {
    let url = match[0];
    const start = match.index!;

    if (start > lastIndex) {
      const value = text.slice(lastIndex, start);
      segments.push({ type: "text", value, displayValue: value });
    }

    segments.push({
      type: "link",
      value: url,
      displayValue: url,
      fullUrl: url,
    });

    lastIndex = start + url.length;
  }

  if (lastIndex < text.length) {
    const value = text.slice(lastIndex);
    segments.push({ type: "text", value, displayValue: value });
  }

  if (segments.length === 0 && text.length > 0) {
    segments.push({ type: "text", value: text, displayValue: text });
  }

  return segments;
}
