#!/bin/sh
# Runs once against a running Keycloak, after the `dreev` realm has been
# imported from dreev-realm.json (structure only — no secrets, no users,
# since Keycloak strips secrets from exports and the partial-export API
# never includes users). This script fills in the two pieces that can't
# live in a committed file: client secrets (from this machine's own .env,
# never from git) and the reviewer user/password. Safe to run again after
# a restart — every step here is idempotent (kcadm update / get-or-create).
set -eu

KCADM="/opt/keycloak/bin/kcadm.sh"
SERVER_URL="http://localhost:8080"

: "${KEYCLOAK_ADMIN:?KEYCLOAK_ADMIN is required}"
: "${KEYCLOAK_ADMIN_PASSWORD:?KEYCLOAK_ADMIN_PASSWORD is required}"
: "${KEYCLOAK_REVIEWER_CLIENT_SECRET:?KEYCLOAK_REVIEWER_CLIENT_SECRET is required}"
: "${FREEP_TEST_CLIENT_SECRET:?FREEP_TEST_CLIENT_SECRET is required}"
: "${REVIEWER_USERNAME:?REVIEWER_USERNAME is required}"
: "${REVIEWER_PASSWORD:?REVIEWER_PASSWORD is required}"
: "${REVIEWER_EMAIL:?REVIEWER_EMAIL is required}"

echo "[init-secrets] waiting for Keycloak to accept admin login..."
until "$KCADM" config credentials --server "$SERVER_URL" --realm master \
  --user "$KEYCLOAK_ADMIN" --password "$KEYCLOAK_ADMIN_PASSWORD" >/dev/null 2>&1; do
  sleep 2
done

reviewer_ui_id=$("$KCADM" get clients -r dreev -q clientId=freep-reviewer-ui --fields id --format csv --noquotes)
test_client_id=$("$KCADM" get clients -r dreev -q clientId=freep-test-client --fields id --format csv --noquotes)

echo "[init-secrets] setting freep-reviewer-ui secret..."
"$KCADM" update "clients/${reviewer_ui_id}" -r dreev -s "secret=${KEYCLOAK_REVIEWER_CLIENT_SECRET}"

echo "[init-secrets] setting freep-test-client secret..."
"$KCADM" update "clients/${test_client_id}" -r dreev -s "secret=${FREEP_TEST_CLIENT_SECRET}"

if "$KCADM" get users -r dreev -q "username=${REVIEWER_USERNAME}" --fields id --format csv --noquotes | grep -q .; then
  echo "[init-secrets] reviewer user already exists, skipping creation"
else
  echo "[init-secrets] creating reviewer user..."
  "$KCADM" create users -r dreev \
    -s "username=${REVIEWER_USERNAME}" \
    -s "email=${REVIEWER_EMAIL}" \
    -s emailVerified=true \
    -s "firstName=${REVIEWER_FIRST_NAME:-Freep}" \
    -s "lastName=${REVIEWER_LAST_NAME:-Reviewer}" \
    -s enabled=true
fi

"$KCADM" set-password -r dreev --username "$REVIEWER_USERNAME" \
  --new-password "$REVIEWER_PASSWORD" --temporary=false

echo "[init-secrets] done."
