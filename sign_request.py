#!/bin/python3

import electrum_ecc as ecc
import hashlib
import sys
import json

def int_to_bytes(x: int) -> bytes:
    assert type(x) == int
    return x.to_bytes(8, 'big')

def sha256(x: bytes) -> bytes:
    return bytes(hashlib.sha256(x).digest())

def leaf_hash(event_id:str, value:int, nonce:bytes, pubkey:bytes) -> bytes:
    return sha256(b"Leaf:" + event_id + int_to_bytes(value) + nonce + (pubkey if pubkey else bytes(32)))

def sign_leaf_hash(privkey_bytes: bytes, event_id: str, value: int, nonce: bytes):
    privkey = ecc.ECPrivkey(privkey_bytes)
    pubkey = privkey.get_public_key_bytes()[1:]
    leaf_h = leaf_hash(event_id, value, nonce, pubkey)
    signature = privkey.schnorr_sign(leaf_h)
    return pubkey, leaf_h, signature

_, privkey, event_id, value, nonce = sys.argv[:]
privkey = bytes.fromhex(privkey)
nonce = bytes.fromhex(nonce)
event_id = bytes.fromhex(event_id)
value_msats = int(value) * 1000
pubkey, leaf, signature = sign_leaf_hash(privkey, event_id, value_msats, nonce)
r = {
    "pubkey": pubkey.hex(),
    "leaf_hash":leaf.hex(),
    "signature": signature.hex(),
}
print(json.dumps(r))
