#!/data/data/com.termux/files/usr/bin/bash
set -e
ROOT=$(cat ~/veyra-termux/tunnel_url.txt 2>/dev/null || echo "https://veyra.local")
PAGES="/ /app /benchmarks /demos /kits /business /docs /security /status /help /privacy /terms /legal"
echo '<?xml version="1.0" encoding="UTF-8"?>' > public/sitemap.xml
echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' >> public/sitemap.xml
for p in $PAGES; do
  echo "  <url><loc>${ROOT}${p}</loc></url>" >> public/sitemap.xml
done
echo '</urlset>' >> public/sitemap.xml
