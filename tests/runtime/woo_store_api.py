"""WooCommerce session/cart contract tests against isolated CI only.

Uses WooCommerce's documented public Store API and Cart-Token. These tests do
not bypass nonce security and do not process real or simulated payments.
"""
import json
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
API = BASE + '/wp-json/wc/store/v1'


def request(path, method='GET', data=None, token=None, expected=200):
    payload = json.dumps(data).encode('utf-8') if data is not None else None
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if token is not None:
        headers['Cart-Token'] = token
    req = Request(API + path, method=method, data=payload, headers=headers)
    try:
        with urlopen(req, timeout=35) as response:
            status = response.status
            body = response.read()
            response_headers = response.headers
    except HTTPError as error:
        status = error.code
        body = error.read()
        response_headers = error.headers
    assert status == expected, f'{method} {path}: HTTP {status}, expected {expected}; {body[:350]!r}'
    return json.loads(body), response_headers


def main():
    products, _ = request('/products?slug=ci-test-product')
    assert len(products) == 1, 'The synthetic WooCommerce product is missing'
    product_id = products[0]['id']
    assert int(products[0]['prices']['price']) > 0

    empty_a, headers_a = request('/cart')
    token_a = headers_a.get('Cart-Token')
    assert token_a, 'WooCommerce did not provide a Cart-Token'
    assert not empty_a['items']

    added, _ = request('/cart/add-item', 'POST', {'id': product_id, 'quantity': 1}, token_a, expected=201)
    assert len(added['items']) == 1 and added['items'][0]['quantity'] == 1
    key = added['items'][0]['key']

    updated, _ = request('/cart/update-item', 'POST', {'key': key, 'quantity': 2}, token_a)
    assert updated['items'][0]['quantity'] == 2
    assert updated['items'][0]['key'] == key

    # Two guests must never share the same cart state.
    empty_b, headers_b = request('/cart')
    token_b = headers_b.get('Cart-Token')
    assert token_b and token_b != token_a, 'Anonymous carts are not isolated'
    assert not empty_b['items'], 'Another guest can see a different cart'

    removed, _ = request('/cart/remove-item', 'POST', {'key': key}, token_a)
    assert not removed['items']
    again, _ = request('/cart', token=token_a)
    assert not again['items']

    # Do not test an actual payment gateway or create an order in public CI.
    print('PASS: WooCommerce public Store API, cart tokens, quantities, removal and guest isolation')


if __name__ == '__main__':
    main()
