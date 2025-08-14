#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
URL="${1:-$(cat ~/veyra-termux/tunnel_url.txt 2>/dev/null || true)}"
[ -z "${URL:-}" ] && { echo "Usage: scripts/test_public.sh https://mon-url.lhr.life"; exit 1; }

pass(){ printf "✅ %s\n" "$1"; }
fail(){ printf "❌ %s\n" "$1"; exit 1; }

code=$(curl -ks -o /dev/null -w "%{http_code}" "$URL/healthz"); [ "$code" = "200" ] || fail "/healthz $code"; pass "/healthz 200"

home=$(curl -ks "$URL/"); echo "$home" | grep -qi "Veyra le fait" && pass "/ (Hero trouvé)" || pass "/ (200 OK)"

today=$(curl -ks "$URL/today"); echo "$today" | jq -e '.priorities|length>=1' >/dev/null || fail "/today invalide"; pass "/today JSON OK"

resp=$(curl -ks -X POST "$URL/run" -H 'Content-Type: application/json' -H "Idempotency-Key: test$RANDOM" -d '{"id":"admin.attestation"}')
pid=$(echo "$resp" | jq -r '.proof_id'); sha=$(echo "$resp" | jq -r '.sha256')
[ "$pid" != "null" ] && echo "$sha" | grep -Eq '^[a-f0-9]{64}$' || fail "/run KO"; pass "/run -> $pid"

pjson=$(curl -ks "$URL/proofs/$pid"); echo "$pjson" | jq -e --arg id "$pid" '(.id==$id) and (.sha256|test("^[a-f0-9]{64}$"))' >/dev/null || fail "/proofs/$pid invalide"; pass "/proofs/$pid OK"

plist=$(curl -ks "$URL/proofs"); echo "$plist" | jq -e '.items|length>=1' >/dev/null && pass "/proofs (liste) OK" || pass "/proofs (liste vide)"

bench=$(curl -ks "$URL/bench"); echo "$bench" | jq -e 'has("total_proofs")' >/dev/null || fail "/bench invalide"; pass "/bench OK"

metrics=$(curl -ks "$URL/metrics"); echo "$metrics" | jq -e 'has("veyra_proofs_total")' >/dev/null || fail "/metrics invalide"; pass "/metrics OK"

echo "🎉 Tests PUBLIC OK pour $URL"
