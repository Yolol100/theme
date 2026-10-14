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


def test_editor_edge_cases(page):
    # Additional Gutenberg fixtures use the browser-loaded data store.
    # This is programmatic block recovery, not the UI recovery button.
    empty_id = os.environ.get('EDITOR_EMPTY_PAGE_ID')
    invalid_id = os.environ.get('EDITOR_INVALID_PAGE_ID')
    assert empty_id and empty_id.isdigit() and invalid_id and invalid_id.isdigit()
    response=page.goto(BASE+'/ci-empty-page/', wait_until='domcontentloaded')
    assert response and response.status==200
    # WordPress can omit the post-content wrapper entirely for a truly empty page.
    # Check rendered semantics, not an incidental empty Core wrapper.
    assert ' '.join(page.locator('main').inner_text().split()) == 'CI Empty Page', (
        'Empty WordPress page rendered unexpected content: ' + page.locator('main').inner_text()
    )

    response=page.goto(BASE+f'/wp-admin/post.php?post={invalid_id}&action=edit',
                       wait_until='domcontentloaded')
    assert response and response.status==200
    page.wait_for_function('''() => Boolean(window.wp && wp.data &&
        wp.data.select('core/editor')?.getCurrentPostType()==='page' &&
        wp.data.select('core/block-editor')?.getBlocks()?.length)''', timeout=45000)
    before=page.evaluate('''() => {
        const editor=wp.data.select('core/block-editor');
        const blocks=editor.getBlocks();
        return blocks.map(b=>({name:b.name,valid:editor.isBlockValid(b.clientId)}));
    }''')
    assert any(b['name']=='core/paragraph' and b['valid'] is False for b in before), (
        f'Invalid serialized Core paragraph was not detected by Gutenberg: {before}'
    )
    recovered=page.evaluate('''async () => {
        const editor=wp.data.select('core/block-editor');
        const bad=editor.getBlocks().find(b=>b.name==='core/paragraph'
            && !editor.isBlockValid(b.clientId));
        if (!bad) throw Error('Expected invalid Core paragraph missing');
        wp.data.dispatch('core/block-editor').replaceBlocks(
            bad.clientId,
            wp.blocks.createBlock('core/paragraph', {content:'CI recoverable block content'})
        );
        await wp.data.dispatch('core/editor').savePost();
        return wp.data.select('core/editor').getCurrentPostId();
    }''')
    assert recovered == int(invalid_id), (recovered,invalid_id)
    page.reload(wait_until='domcontentloaded')
    page.wait_for_function('''() => Boolean(window.wp && wp.data &&
        wp.data.select('core/block-editor')?.getBlocks()?.some(b =>
          b.name==='core/paragraph' &&
          wp.data.select('core/block-editor').isBlockValid(b.clientId) &&
          b.attributes.content==='CI recoverable block content'))''', timeout=45000)
    response=page.goto(BASE+'/ci-invalid-block/', wait_until='domcontentloaded')
    assert response and response.status==200
    assert 'CI recoverable block content' in page.locator('main p').inner_text()
    print('PASS: empty page and genuine Gutenberg invalid-block detection/recovery (store)')


def test_site_editor_api_roundtrip(page):
    # Real authenticated REST calls from the loaded Site Editor, NOT a visual
    # Site Editor edit. No file changes or persistent theme modifications.
    page.goto(BASE+'/wp-admin/site-editor.php',wait_until='domcontentloaded')
    page.wait_for_function("() => Boolean(window.wp && wp.apiFetch && wp.data)",timeout=45000)
    parts=page.evaluate('''async () => {
        const rows=await wp.apiFetch({path:'/wp/v2/template-parts?context=edit&per_page=100'});
        return rows.filter(p => p.theme==='webactueel-starter' &&
            ['header','footer'].includes(p.slug)).map(p=>({
                id:p.id,slug:p.slug,source:p.source,
                original:p.content?.raw
            }));
    }''')
    assert {p['slug'] for p in parts}=={'header','footer'}, f'Incomplete Site Editor parts: {parts}'
    for part in parts:
        assert isinstance(part['original'],str) and part['original'].strip(), part
        marker=f'CI temporary {part["slug"]} override'
        changed=part['original']+f'\n<!-- wp:paragraph --><p>{marker}</p><!-- /wp:paragraph -->'
        try:
            result=page.evaluate('''async ({id,content}) => {
                const path='/wp/v2/template-parts/'+encodeURIComponent(id);
                const updated=await wp.apiFetch({path,method:'POST',data:{content}});
                const fetched=await wp.apiFetch({path:path+'?context=edit'});
                return {id:updated.id, content:fetched.content?.raw};
            }''',{'id':part['id'],'content':changed})
            assert result['id']==part['id'] and marker in result['content'],result
            response=page.goto(BASE+'/',wait_until='domcontentloaded')
            assert response and response.status==200
            region=page.locator(part['slug']).first
            assert marker in region.inner_text(), f'{part["slug"]} customization absent on frontend'
        finally:
            # Delete only the disposable database override. Core restores the
            # original file-backed part without changing the theme ZIP.
            page.goto(BASE+'/wp-admin/site-editor.php',wait_until='domcontentloaded')
            page.wait_for_function("() => Boolean(window.wp && wp.apiFetch)",timeout=45000)
            restored=page.evaluate('''async (id) => {
                const path='/wp/v2/template-parts/'+encodeURIComponent(id);
                const response=await wp.apiFetch({path:path+'?force=true',method:'DELETE'});
                const baseline=await wp.apiFetch({path:path+'?context=edit'});
                return {deleted:Boolean(response.deleted), source:baseline.source, content:baseline.content?.raw};
            }''',part['id'])
            assert restored['deleted'] and restored['content']==part['original'], (
                f'Failed to restore original {part["slug"]} theme part: {restored}'
            )
            response=page.goto(BASE+'/',wait_until='domcontentloaded')
            assert response and response.status==200
            assert marker not in page.locator(part['slug']).inner_text()
            page.goto(BASE+'/wp-admin/site-editor.php',wait_until='domcontentloaded')
            page.wait_for_function("() => Boolean(window.wp && wp.apiFetch)",timeout=45000)
    print('PASS: authenticated Site Editor REST header/footer save/frontend/readback/revert')


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
            # Site Editor is a React application: DOMContentLoaded may precede
            # hydration, especially on WordPress 6.6. Still fail if it remains blank.
            page.wait_for_function(
                '() => Boolean(document.body && document.body.innerText.trim())',
                timeout=45000,
            )
            assert page.locator('body').inner_text().strip(), 'Site Editor remained empty after hydration'
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
                            // The nested cell shape is parsed from saved markup.
                            // Explicit tag is required by core/table's save.js.
                            body: [{cells: [
                                {tag: 'td', content: 'CI Table First'},
                                {tag: 'td', content: 'CI Table Second'}
                            ]}]
                        }),
                        window.wp.blocks.createBlock('core/list', {}, [
                            window.wp.blocks.createBlock('core/list-item', {content: 'CI List Item'})
                        ]),
                        window.wp.blocks.createBlock('core/image', {
                            url: '/wp-includes/images/w-logo-blue-white-bg.png',
                            alt: 'CI image with meaningful alternative text'
                        }),
                        window.wp.blocks.createBlock('core/quote', {}, [
                            window.wp.blocks.createBlock('core/paragraph', {
                                content: 'CI Nested Quote Content'
                            })
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
                               'CI Core Button', 'CI Table First', 'CI Table Second',
                               'CI List Item', 'CI Nested Quote Content'):
                    assert marker in body, f'Missing persisted Gutenberg Core block content: {marker}'
                assert page.locator('main .wp-block-columns .wp-block-column').count() == 2
                assert page.locator('main .wp-block-buttons a[href="/"]').count() == 1
                # Core may create additional empty default cells. The contract
                # is semantic table markup and preservation of both authored cells.
                table = page.locator('main .wp-block-table table').first
                assert table.count() == 1, 'Saved Core table is not rendered as a table'
                assert table.locator('th, td').count() >= 2, (
                    'Saved table cells are absent: ' + table.inner_html()[:1200]
                )
                assert 'CI Table First' in table.inner_text(), 'First cell did not survive save/reload'
                assert 'CI Table Second' in table.inner_text(), 'Second cell did not survive save/reload'
                assert page.locator('main .wp-block-list li').count() == 1
                assert page.locator('main .wp-block-quote').count() == 1
                image=page.locator('main .wp-block-image img').first
                assert image.count() == 1 and image.get_attribute('alt') == (
                    'CI image with meaningful alternative text'
                ), 'Gutenberg image alt text was lost during editor roundtrip'
                print('PASS: Gutenberg store save/reopen, nested quote and image alt text preserved')
                test_editor_edge_cases(page)
                test_editor_role_post(browser)
                if os.environ.get('RUN_SITE_EDITOR_API') == '1':
                    test_site_editor_api_roundtrip(page)
            else:
                print('PASS: authenticated admin login and block editor route; save/reopen NOT_RUN')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
