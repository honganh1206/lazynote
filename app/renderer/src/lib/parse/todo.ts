export type LineType =
  | "checklist-item"
  | "checklist-item-checked"
  | "heading"
  | "comment"
  | "empty";

export interface ParsedLine {
  type: LineType;
  text: string;
  headingLevel?: number;
}

export function parseTodoLines(content: string): ParsedLine[] {
  const lines = content.split("\n");
  // Skip line 0 (the keyword line); parse the rest
  return lines.slice(1).map(classifyLine);
}

export function parsePlainLines(content: string): ParsedLine[] {
  return content.split("\n").map(classifyPlainLine);
}

function classifyPlainLine(line: string): ParsedLine {
  if (line.trim() === "") {
    return { type: "empty", text: line };
  }

  // Markdown-like heading
  // currently support 3 levels of heading
  const headingMatch = line.match(/^(#{1,3}) /);
  if (headingMatch) {
    return {
      type: "heading",
      text: line,
      headingLevel: headingMatch[1].length,
    };
  }

  return { type: "checklist-item", text: line };
}

function classifyLine(line: string): ParsedLine {
  if (line.trim() === "") {
    return { type: "empty", text: line };
  }

  const headingMatch = line.match(/^(#{1,3}) /);
  if (headingMatch) {
    return {
      type: "heading",
      text: line,
      headingLevel: headingMatch[1].length,
    };
  }

  if (line.startsWith("//")) {
    return { type: "comment", text: line };
  }

  if (line.endsWith("/x")) {
    return { type: "checklist-item-checked", text: line.slice(0, -2) };
  }

  return { type: "checklist-item", text: line };
}
