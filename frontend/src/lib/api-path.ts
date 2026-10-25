/** Keep the Django slash convention without changing query strings or bodies. */
export function withApiTrailingSlash(url: string): string {
  if (!url) return url;
  const suffixStart = url.search(/[?#]/);
  const pathname = suffixStart < 0 ? url : url.slice(0, suffixStart);
  const suffix = suffixStart < 0 ? "" : url.slice(suffixStart);
  return `${pathname.endsWith("/") ? pathname : `${pathname}/`}${suffix}`;
}
