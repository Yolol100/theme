"""Authenticated browser check for WordPress admin and block-editor loading.

The fixture page is created by WP-CLI. A gated, actual Gutenberg data-store
roundtrip is executed on current WordPress in one isolated profile; Site Editor
menus/global styles still require separate human acceptance.
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
            assert page.locator('body').inner_text().strip(), 'Empty block editor response'
            assert not page.locator('body').get_by_text('critical error', exact=False).count(), 'Critical error in admin'
            if os.environ.get('RUN_EDITOR_E2E') == '1':
                page_id = os.environ.get('EDITOR_TEST_PAGE_ID')
                assert page_id and page_id.isdigit(), 'Missing fixture page ID'
                response = page.goto(
                    BASE + f'/wp-admin/post.php?post={page_id}&action=edit',
                    wait_until='domcontentloaded',
                )
                assert response and response.status == 200
                page.wait_for_function(
                    '(id) => Boolean(window.wp && wp.data && wp.blocks && '
                    'wp.data.select("core/editor") && '
                    'wp.data.select("core/editor").getCurrentPostId() === id)',
                    arg=int(page_id), timeout=45000,
                )
                page.evaluate('''async () => {
                    const editor = window.wp.data.dispatch('core/editor');
                    const blocks = window.wp.data.dispatch('core/block-editor');
                    editor.editPost({title: 'Gutenberg E2E Saved Page'});
                    blocks.insertBlocks(window.wp.blocks.createBlock('core/paragraph', {
                        content: 'Persisted from WordPress block editor on CI'
                    }));
                    await editor.savePost();
                }''')
                page.reload(wait_until='domcontentloaded')
                page.wait_for_function(
                    '() => Boolean(window.wp && wp.data && '
                    'wp.data.select("core/editor") && '
                    'wp.data.select("core/editor").getEditedPostAttribute("title") === '
                    '"Gutenberg E2E Saved Page")', timeout=45000,
                )
                response = page.goto(BASE + '/starter-page/', wait_until='domcontentloaded')
                assert response and response.status == 200
                body = page.locator('main').inner_text()
                assert 'Gutenberg E2E Saved Page' in body
                assert 'Persisted from WordPress block editor on CI' in body
                print('PASS: Gutenberg editor store save/reopen and frontend content roundtrip')
            else:
                print('PASS: authenticated admin login and block editor route; save/reopen NOT_RUN')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
