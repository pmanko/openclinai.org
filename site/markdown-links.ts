import fs from 'node:fs';
import path from 'node:path';

// Repository-relative Markdown links must resolve in the published site or link
// to their maintained source, not to nonexistent files in the static output.
export function publicationLinks(html: string, id: string, base = '/openclinai.org/'): string {
  const root = path.resolve(__dirname, '..');
  const selected = new Set(
    [...fs.readFileSync(path.join(__dirname, 'published-content.ts'), 'utf8').matchAll(/'\.\.\/([^']+\.md)'/g)]
      .map(match => match[1]),
  );
  const ids = new Map<string, number>();
  html = html.replace(/<h([1-6])>(.*?)<\/h\1>/gs, (_, level, text) => {
    const slug = text.replace(/<[^>]*>/g, '').toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu, '').trim().replace(/\s/g, '-');
    const count = ids.get(slug) ?? 0;
    ids.set(slug, count + 1);
    return `<h${level} id="${slug}${count ? '-' + count : ''}">${text}</h${level}>`;
  });
  return html.replace(/href="([^"#][^"]*)"/g, (attribute, href: string) => {
    if (/^(?:[a-z]+:|\/)/i.test(href)) return attribute;
    const [file, fragment] = href.split('#');
    const relative = path.relative(root, path.resolve(path.dirname(id), file)).split(path.sep).join('/');
    const suffix = fragment ? '#' + fragment : '';
    if (selected.has(relative)) return `href="${base}spec/${relative.replace(/\.md$/, '')}.html${suffix}"`;
    return `href="https://github.com/pmanko/openclinai.org/blob/main/${relative}${suffix}"`;
  });
}
