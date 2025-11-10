#!/bin/bash
alice="./run_electrum --regtest -D /tmp/alice"
bob="./run_electrum --regtest -D /tmp/bob"

$bob load_wallet

while true; do
    event_id=$(hexdump -n32 -e '16/1 "%02x"' /dev/urandom)
    nonce=$(hexdump -n32 -e '16/1 "%02x"' /dev/urandom)
    value=$(($RANDOM % 256))
    echo "$alice notary_add_request $event_id $value $nonce"
    invoice=$($alice notary_add_request $event_id $value $nonce| jq '.invoice')
    $bob lnpay $invoice --timeout 3
    # sleep random time
    sleep $((2 + $RANDOM % 5))
done
