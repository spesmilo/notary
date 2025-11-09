#!/bin/bash

# this script sends a request to the notary and gets an invoice
# once the invoice is paid, it gets a proof and asks the notary to verify it

url=http://localhost:5455/api
#url=https://swaps.electrum.org/notary

if [[ -z "$2" ]] ; then
    usage="usage: $0 event_id amount [privkey]"
    echo $usage
    exit 1
fi

nonce=$(hexdump -n32 -e '16/1 "%02x"' /dev/urandom)

if [[ -z "$3" ]] ; then
    request="{\"event_id\":\"$1\",\"value\":$2,\"nonce\":\"$nonce\"}"
else
    event_id="$1"
    value="$2"
    privkey="$3"
    r=$( $(dirname "$0")/sign_request.py $privkey $event_id $value $nonce)
    signature=$(echo $r|jq -r '.signature')
    pubkey=$(echo $r|jq -r '.pubkey')
    request="{\"event_id\":\"$1\",\"value\":$2,\"nonce\":\"$nonce\",\"upvoter_pubkey\":\"$pubkey\",\"upvoter_signature\":\"$signature\"}"
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
