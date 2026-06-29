export const REGISTERED_KEYWORDS = ['todo'] as const

const KEYWORD_PATTERN = /^(\w+)(?::\s*(.*))?$/

export function isKeywordRegistered(keyword: string): boolean {
  return (REGISTERED_KEYWORDS as readonly string[]).includes(keyword.toLowerCase())
}

export function detectMode(content: string): { keyword: string; title: string } | null {
  const firstLine = content.split('\n')[0].trim()
  if (!firstLine) return null

  const match = firstLine.match(KEYWORD_PATTERN)
  if (!match) return null

  const keyword = match[1].toLowerCase()
  if (!isKeywordRegistered(keyword)) return null

  return { keyword, title: match[2]?.trim() ?? '' }
}
