"""Authenticated browser check for WordPress admin and block-editor loading.

The fixture page is created by WP-CLI. A gated, actual Gutenberg data-store
roundtrip is executed on current WordPress in one isolated profile; Site Editor
menus/global styles still require separate human acceptance.
"""
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BASE_URL', 'http://localhost:8080').rstrip('/')
PASSWORD = os.environ.get('CI_WP_PASSWORD', 'ci-local-only-password')



def test_editor_role_post(browser):
    """Editor can publish and reopen posts but cannot enter Site Editor."""
    context=browser.new_context()
    page=context.new_page()
    try:
        page.goto(BASE+'/wp-login.php',wait_until='domcontentloaded')
        page.locator('#user_login').fill('ci_editor')
        page.locator('#user_pass').fill(os.environ.get('CI_EDITOR_PASSWORD','ci-editor-disposable-password'))
        page.locator('#wp-submit').click()
        page.wait_for_url('**/wp-admin/**',timeout=25000)
        response=page.goto(BASE+'/wp-admin/post-new.php',wait_until='domcontentloaded')
        assert response and response.status==200
        page.wait_for_function("() => Boolean(window.wp && wp.data && wp.data.select('core/editor')?.getCurrentPostType()==='post')",timeout=45000)
        created=page.evaluate("""async () => {
          const editor=wp.data.dispatch('core/editor');
          editor.editPost({title:'CI Editor Role Post',status:'publish'});
          wp.data.dispatch('core/block-editor').insertBlocks([
            wp.blocks.createBlock('core/heading',{level:2,content:'CI Editor Heading'}),
            wp.blocks.createBlock('core/paragraph',{content:'Editor role persisted content'})
          ]);
          await editor.savePost();
          return {id:wp.data.select('core/editor').getCurrentPostId(),
            status:wp.data.select('core/editor').getEditedPostAttribute('status')};
        }""")
        assert created['id']>0 and created['status']=='publish',created
        page.goto(BASE+'/wp-admin/post.php?post='+str(created['id'])+'&action=edit',wait_until='domcontentloaded')
        page.wait_for_function("""() => Boolean(window.wp && wp.data &&
            wp.data.select('core/editor')?.getEditedPostAttribute('title')==='CI Editor Role Post' &&
            wp.data.select('core/block-editor')?.getBlocks()?.some(block => block.name === 'core/heading'))""",timeout=45000)
        response=page.goto(BASE+'/?p='+str(created['id']),wait_until='domcontentloaded')
        assert response and response.status==200
        assert 'Editor role persisted content' in page.locator('main').inner_text()
        assert 'CI Editor Heading' in page.locator('main h2').inner_text()
        response=page.goto(BASE+'/wp-admin/site-editor.php',wait_until='domcontentloaded')
        assert response and ('site-editor.php' not in page.url or 'not allowed' in page.locator('body').inner_text().lower())
        print('PASS: editor user role publishes and reopens post; Site Editor access denied')
    finally:
        context.close()


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
            # A real authenticated browser visit, not a REST-only Site Editor check.
            # Saving site-wide parts/navigation/global styles is reserved for the
            # separate isolated staging and human acceptance workflow.
            site_editor = page.goto(BASE + '/wp-admin/site-editor.php', wait_until='domcontentloaded')
            assert site_editor and site_editor.status == 200, 'Admin cannot open Site Editor'
            assert page.locator('body').inner_text().strip(), 'Site Editor returned an empty shell'
            response = page.goto(BASE + '/wp-admin/post-new.php?post_type=page', wait_until='domcontentloaded')
            assert response and response.status == 200
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
                    blocks.insertBlocks([
                        window.wp.blocks.createBlock('core/paragraph', {
                            content: 'Persisted from WordPress block editor on CI'
                        }),
                        window.wp.blocks.createBlock('core/heading', {
                            level: 2, content: 'CI Gutenberg Heading'
                        }),
                        window.wp.blocks.createBlock('core/columns', {}, [
                            window.wp.blocks.createBlock('core/column', {}, [
                                window.wp.blocks.createBlock('core/paragraph', {content: 'CI Column One'})
                            ]),
                            window.wp.blocks.createBlock('core/column', {}, [
                                window.wp.blocks.createBlock('core/paragraph', {content: 'CI Column Two'})
                            ])
                        ]),
                        window.wp.blocks.createBlock('core/buttons', {}, [
                            window.wp.blocks.createBlock('core/button', {text: 'CI Core Button', url: '/'})
                        ]),
                        window.wp.blocks.createBlock('core/table', {
                            body: [{cells: [{content: 'CI Table First'}, {content: 'CI Table Second'}]}]
                        }),
                        window.wp.blocks.createBlock('core/list', {}, [
                            window.wp.blocks.createBlock('core/list-item', {content: 'CI List Item'})
                        ])
                    ]);
                    await editor.savePost();
                }''')
                page.reload(wait_until='domcontentloaded')
                page.wait_for_function(
                    '() => Boolean(window.wp && wp.data && '
                    'wp.data.select("core/editor") && '
                    'wp.data.select("core/editor").getEditedPostAttribute("title") === '
                    '"Gutenberg E2E Saved Page")', timeout=45000,
                )
                page.wait_for_function('''() => Boolean(window.wp && wp.data &&
                    ['core/columns', 'core/table', 'core/list'].every(name =>
                        wp.data.select('core/block-editor')?.getBlocks()?.some(block => block.name === name)))''', timeout=45000)
                response = page.goto(BASE + '/starter-page/', wait_until='domcontentloaded')
                assert response and response.status == 200
                body = page.locator('main').inner_text()
                assert 'Gutenberg E2E Saved Page' in body
                assert 'Persisted from WordPress block editor on CI' in body
                for marker in ('CI Gutenberg Heading', 'CI Column One', 'CI Column Two',
                               'CI Core Button', 'CI Table First', 'CI Table Second', 'CI List Item'):
                    assert marker in body, f'Missing persisted Gutenberg Core block content: {marker}'
                assert page.locator('main .wp-block-columns .wp-block-column').count() == 2
                assert page.locator('main .wp-block-buttons a[href="/"]').count() == 1
                assert page.locator('main .wp-block-table table td').count() == 2
                assert page.locator('main .wp-block-list li').count() == 1
                print('PASS: Gutenberg editor store save/reopen and frontend paragraph, heading, columns, button, table and list')
                test_editor_role_post(browser)
            else:
                print('PASS: authenticated admin login and block editor route; save/reopen NOT_RUN')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
