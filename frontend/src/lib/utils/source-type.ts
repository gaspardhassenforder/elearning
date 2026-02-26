export type VideoSourceType = 'youtube' | 'mp4' | null

export function getVideoType(source: {
  asset?: { file_path?: string | null; url?: string | null } | null
}): VideoSourceType {
  const url = source.asset?.url ?? ''
  const path = source.asset?.file_path ?? ''
  if (/youtube\.com|youtu\.be/.test(url)) return 'youtube'
  if (/\.(mp4|webm|mov|avi)$/i.test(path)) return 'mp4'
  return null
}

export function extractYouTubeId(url: string): string | null {
  const m = url.match(/(?:v=|youtu\.be\/)([A-Za-z0-9_-]{11})/)
  return m ? m[1] : null
}
