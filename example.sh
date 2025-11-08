#!/bin/bash

# this sends a notarization request to notary.electrum.org
url=http://localhost:5455/api
#url=https://swaps.electrum.org/notary

if [[ -z "$2" ]] ; then
    usage="usage: $0 event_id amount [pubkey signature]"
    echo $usage
    exit 1
fi

nonce=$(hexdump -n32 -e '16/1 "%02x"' /dev/urandom)

if [[ -z "$3" ]] ; then
    request="{\"event_id\":\"$1\",\"value\":$2,\"nonce\":\"$nonce\"}"
else
    request="{\"event_id\":\"$1\",\"value\":$2,\"nonce\":\"$nonce\",\"pubkey\":\"$3\",\"signature\":\"$4\"}"
fi

echo "your request"
echo $request | jq --color-output

invoice=$(curl -s -X POST $url/add_request -H 'Content-Type: application/json' -d @<(echo $request))

echo "notary invoice:"
echo $invoice | jq --color-output

proof="{\"error\":\"initializing...\"}"
while error=$(echo $proof|jq '.error') && [[ $error != null ]]; do
    printf "$error\r"
    sleep 1
    proof=$(curl -s -X POST $url/get_proof -H 'Content-Type: application/json' -d @<(echo $invoice))
done
printf "                                                 \r"
echo "proof:"
echo $proof | jq --color-output

echo "proof verification:"
verify=$(curl -s -X POST $url/verify_proof -H 'Content-Type: application/json' -d @<(echo $proof))
echo $verify | jq --color-output
