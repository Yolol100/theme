"""Authenticated browser check for WordPress admin and block-editor loading.

The content is created by WP-CLI during fixture setup. Seeing the editor load
is not proof of editor save/reopen; those remain separately tracked in QA.
"""
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
PASSWORD = os.environ.get('CI_WP_PASSWORD', 'ci-local-only-password')


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            response = page.goto(BASE + '/wp-login.php', wait_until='domcontentloaded')
            assert response and response.status == 200
            page.locator('#user_login').fill('ci_admin')
            page.locator('#user_pass').fill(PASSWORD)
            page.locator('#wp-submit').click()
            page.wait_for_url('**/wp-admin/**', timeout=25000)
            assert page.locator('#wpadminbar').count() == 1, 'WordPress admin login failed'
            response = page.goto(BASE + '/wp-admin/post-new.php?post_type=page', wait_until='domcontentloaded')
            assert response and response.status == 200
            page.locator('body').wait_for(state='visible')
            # The Site Editor shell should render without a PHP/React fatal error.
            page.locator('body').get_by_text('critical error', exact=False).count() == 0 or (_ for _ in ()).throw(AssertionError('Critical error in admin'))
            assert page.locator('body').inner_text().strip(), 'Empty block editor response'
            print('PASS: authenticated admin login and block editor route; save/reopen NOT_RUN')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
