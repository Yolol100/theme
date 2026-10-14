"""Static tests only; do not mistake for WordPress staging evidence."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
THEME=ROOT/'theme'/'webactueel-starter'
FILES={'style.css','theme.json','LICENSE.txt', 'parts/header.html','parts/footer.html','parts/post-list.html','templates/index.html','templates/archive.html','templates/search.html','templates/page.html','templates/single.html','templates/404.html'}
COMMENT=re.compile(r'<!--\s*(/?)wp:([a-z\d/+-]+)(?:\s+(\{.*?\}))?\s*(/?)\s*-->',re.S|re.I)
REFERENCE=re.compile(r'wp:template-part\s+(\{[^\n]*?\})')
VOID={'br','img','hr','input','meta','link','source','area','col','wbr'}

def luminance(c):
    values=[int(c[i:i+2],16)/255 for i in (1,3,5)]
    converted=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return .2126*converted[0]+.7152*converted[1]+.0722*converted[2]

def contrast(c,d):
    a,b=sorted((luminance(c),luminance(d)),reverse=True)
    return (a+.05)/(b+.05)

class HTMLStack(HTMLParser):
    def __init__(self):super().__init__();self.stack=[];self.errors=[]
    def handle_starttag(self,tag,attrs):
        if tag not in VOID:self.stack.append(tag)
    def handle_endtag(self,tag):
        if self.stack and self.stack[-1]==tag:self.stack.pop()
        else:self.errors.append((tag,list(self.stack)))

class ThemeTests(unittest.TestCase):
    def test_only_necessary_runtime_files(self):
        self.assertEqual({p.relative_to(THEME).as_posix() for p in THEME.rglob('*') if p.is_file()},FILES)
    def test_no_php_js_extra_design_or_shop_code(self):
        for name in ('functions.php','assets','patterns','styles','woocommerce','inc'):
            with self.subTest(name=name):self.assertFalse((THEME/name).exists())
        self.assertEqual(list(THEME.rglob('*.php'))+list(THEME.rglob('*.js')),[])
    def test_theme_header(self):
        s=(THEME/'style.css').read_text()
        for term in ('Theme Name: Webactueel Starter','Version: 1.0.4','Requires at least: 6.6','Requires PHP: 8.3','Text Domain: webactueel-starter','License: GPL-2.0-or-later'):
            with self.subTest(term=term):self.assertIn(term,s)
        self.assertEqual(s.split('*/',1)[1].strip(),'')
    def test_theme_long_word_and_table_reflow_guard(self):
        css=json.loads((THEME/'theme.json').read_text())['styles']['css']
        self.assertIn('.wp-block-post-content',css)
        self.assertIn('.wp-block-post-title',css)
        self.assertIn('overflow-wrap: anywhere',css)
        self.assertIn('max-width: 100%',css)
        self.assertIn('overflow-x: auto',css)

    def test_theme_json_version_tokens_palette(self):
        cfg=json.loads((THEME/'theme.json').read_text())
        self.assertEqual(cfg['version'],3)
        self.assertEqual(cfg['$schema'],'https://schemas.wp.org/wp/6.6/theme.json')
        self.assertTrue(cfg['settings']['appearanceTools'])
        self.assertTrue(cfg['settings']['useRootPaddingAwareAlignments'])
        self.assertEqual(cfg['styles']['spacing']['padding']['left'],'clamp(1rem, 3vw, 2rem)')
        self.assertEqual(cfg['styles']['spacing']['padding']['right'],'clamp(1rem, 3vw, 2rem)')
        self.assertEqual(cfg['settings']['layout']['contentSize'],'700px')
        self.assertEqual(cfg['settings']['layout']['wideSize'],'1200px')
        pal={x['slug']:x['color'] for x in cfg['settings']['color']['palette']}
        self.assertEqual(set(pal),{'canvas','ink','accent'})
        self.assertGreaterEqual(contrast(pal['ink'],pal['canvas']),7.0)
        self.assertGreaterEqual(contrast(pal['accent'],pal['canvas']),4.5)
        self.assertEqual([x['name'] for x in cfg['templateParts']],['header','footer'])
        self.assertNotIn('customTemplates',cfg)
    def test_wordpress_v3_root_padding_contract(self):
        cfg=json.loads((THEME/'theme.json').read_text())
        self.assertEqual(cfg['settings']['useRootPaddingAwareAlignments'],True)
        pad=cfg['styles']['spacing']['padding']
        self.assertEqual(set(pad),{'top','right','bottom','left'})
        self.assertEqual(pad['top'],'0')
        self.assertEqual(pad['bottom'],'0')
        self.assertEqual(pad['left'],pad['right'])

    def test_release_version_consistency(self):
        header=(THEME/'style.css').read_text()
        pack=(ROOT/'scripts'/'package.py').read_text()
        readme=(ROOT/'README.md').read_text()
        self.assertIn('Version: 1.0.4',header)
        self.assertIn('Starter-1.0.4-STAGING.zip',pack)
        self.assertIn('Starter-Source-1.0.4.zip',pack)
        self.assertIn('Starter-1.0.4-STAGING.zip',readme)

    def test_block_comment_nesting_and_attrs(self):
        for p in sorted(THEME.rglob('*.html')):
            with self.subTest(path=p.name):
                stack=[];comments=list(COMMENT.finditer(p.read_text()))
                self.assertGreater(len(comments),0)
                for m in comments:
                    closing,kind,attrs,selfclosing=m.groups()
                    if attrs:json.loads(attrs)
                    if closing:
                        self.assertTrue(stack,(p.name,kind))
                        self.assertEqual(stack.pop(),kind)
                    elif not selfclosing:stack.append(kind)
                self.assertEqual(stack,[],p.name)
    def test_html_tags_balanced(self):
        for p in sorted(THEME.rglob('*.html')):
            with self.subTest(path=p.name):
                html=re.sub(r'<!--.*?-->','',p.read_text(),flags=re.S)
                parser=HTMLStack();parser.feed(html)
                self.assertEqual(parser.errors,[],p.name)
                self.assertEqual(parser.stack,[],p.name)
    def test_template_parts_resolve(self):
        for p in sorted(THEME.rglob('*.html')):
            for match in REFERENCE.finditer(p.read_text()):
                slug=json.loads(match.group(1))['slug']
                self.assertTrue((THEME/'parts'/f'{slug}.html').is_file(),(p.name,slug))
    def test_main_landmarks_and_header_footer(self):
        for p in sorted((THEME/'templates').glob('*.html')):
            with self.subTest(template=p.name):
                s=p.read_text()
                self.assertEqual(s.count('"tagName":"main"'),1)
                self.assertEqual(s.count('<main '),1)
                self.assertEqual(s.count('</main>'),1)
                self.assertIn('"slug":"header","tagName":"header"',s)
                self.assertIn('"slug":"footer","tagName":"footer"',s)
    def test_primary_h1_per_template(self):
        for p in sorted((THEME/'templates').glob('*.html')):
            with self.subTest(template=p.name):
                s=p.read_text()
                titles=s.count('<h1 ')+int('wp:post-title {"level":1}' in s)+int('wp:query-title {"type":' in s)
                self.assertEqual(titles,1)
    def test_blog_and_static_homepage_fallback(self):
        self.assertFalse((THEME/'templates'/'front-page.html').exists())
        self.assertFalse((THEME/'templates'/'home.html').exists())
        self.assertIn('"slug":"post-list"',(THEME/'templates'/'index.html').read_text())
        self.assertIn('wp:post-content',(THEME/'templates'/'page.html').read_text())
    def test_archives_search_and_pagination(self):
        s=(THEME/'parts'/'post-list.html').read_text()
        self.assertIn('"inherit":true',s)
        for key in ('wp:post-template','wp:post-title','wp:post-excerpt','wp:query-pagination','wp:query-no-results'):
            self.assertIn(key,s)
        for t in ('index','archive','search'):
            self.assertIn('"slug":"post-list"',(THEME/'templates'/f'{t}.html').read_text())
        for t in ('single','page'):
            self.assertIn('wp:post-content',(THEME/'templates'/f'{t}.html').read_text())
        for t in ('search','404'):
            self.assertIn('wp:search',(THEME/'templates'/f'{t}.html').read_text())
    def test_no_broken_ctas_or_theme_locked_content(self):
        for p in sorted(THEME.rglob('*.html')):
            s=p.read_text()
            for term in ('href=""','href="#"','example.com','waun_','woocommerce/','core/post-meta','templateLock','<script'):
                with self.subTest(file=p.name,term=term):self.assertNotIn(term,s)
    def test_editor_customizable_site_and_navigation(self):
        header=(THEME/'parts'/'header.html').read_text()
        for block in ('wp:site-logo','wp:site-title','wp:navigation'):
            self.assertIn(block,header)
        self.assertNotIn('"ref":',header)
        self.assertIn('wp:site-title',(THEME/'parts'/'footer.html').read_text())
    def test_gitignore_guards_local_credentials_and_build_noise(self):
        ignored=(ROOT/'.gitignore').read_text().splitlines()
        for expected in ('.env','.env.*','*.log','node_modules/','dist/'):
            self.assertIn(expected,ignored)

    def test_ci_actions_use_pinned_node24_versions(self):
        """Avoid deprecated GitHub Actions Node 20 execution and mutable refs."""
        for name in ('ci.yml', 'wordpress-runtime.yml'):
            data=(ROOT/'.github'/'workflows'/name).read_text()
            self.assertIn('actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd',data)
            self.assertIn('actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548',data)
            self.assertNotIn('actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683',data)
            self.assertNotIn('actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',data)

    def test_runtime_wp_cli_matches_wordpress_permissions(self):
        """Regression: WordPress Debian and WP-CLI Alpine use different UIDs."""
        compose=(ROOT/'tests/runtime/compose.yaml').read_text()
        runner=(ROOT/'tests/runtime/run.sh').read_text()
        self.assertIn('    user: "33:33"', compose)
        self.assertIn('      HOME: /tmp', compose)
        self.assertIn('run --rm -T cli wp "$@"', runner)
        self.assertIn('exec -T wordpress test -f /var/www/html/wp-config.php', runner)
        self.assertNotIn('wp core version >/dev/null 2>&1', runner)

    def test_77_scenarios_have_non_fabricated_baseline(self):
        manifest=json.loads((ROOT/'docs/77-scenarios.json').read_text())
        scenarios=manifest['scenarios']
        self.assertEqual(len(scenarios),77)
        self.assertEqual([x['id'] for x in scenarios],list(range(1,78)))
        for case in scenarios:
            self.assertIn(case['baseline_status'],{'SMOKE_PASS','PARTIAL','NOT_RUN','N/A_CI'})
            self.assertTrue(case['acceptance_assertion'])
        self.assertIn('not live results',manifest['purpose'])

    def test_runtime_release_artifact_is_built_once(self):
        flow=(ROOT/'.github/workflows/wordpress-runtime.yml').read_text()
        src=(ROOT/'.github/workflows/ci.yml').read_text()
        runner=(ROOT/'tests/runtime/run.sh').read_text()
        self.assertIn('needs: package',flow)
        self.assertIn('name: runtime-release',flow)
        self.assertIn('actions/download-artifact@70fc10c6e5e1ce46ad2ea6f2b72d43f7d47b13c3',flow)
        self.assertIn('actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f',flow)
        self.assertIn('actions/upload-artifact@bbbca2ddaa5d8feaa63e36b76fdaad77386f024f',src)
        self.assertIn('sha256sum --check SHA256SUMS.txt',runner)
        self.assertNotIn('python3 scripts/package.py',runner)
        self.assertIn("php: '8.4'",flow)
        self.assertIn('PHP_VERSION: ${{ matrix.php }}',flow)
        self.assertIn('RUN_BROWSER',runner)

    def test_checkout_never_uses_real_payment_gateways(self):
        woo=(ROOT/'tests/runtime/woo_store_api.py').read_text()
        runner=(ROOT/'tests/runtime/run.sh').read_text()
        fixture=(ROOT/'tests/runtime/seed_woo.php').read_text()
        self.assertIn("'payment_method': 'cheque'",woo)
        self.assertIn("'real_payment_processed': False",woo)
        self.assertIn('woocommerce_cheque_settings',runner)
        self.assertIn('wc_get_orders',runner)
        self.assertIn('set_virtual( true )',fixture)
        self.assertNotIn("'payment_method': 'stripe'",woo)

    def test_gutenberg_roundtrip_is_real_but_scope_limited(self):
        admin=(ROOT/'tests/runtime/admin_smoke.py').read_text()
        run=(ROOT/'tests/runtime/run.sh').read_text()
        self.assertIn("RUN_EDITOR_E2E=1",run)
        self.assertIn("editor.savePost()",admin)
        self.assertIn("page.reload",admin)
        self.assertIn("Persisted from WordPress block editor",admin)
        self.assertNotIn('payment-provider credentials',admin)

    def test_axe_results_are_advisory_not_wcag_certification(self):
        source=(ROOT/'tests/runtime/axe_audit.py').read_text()
        flow=(ROOT/'.github/workflows/wordpress-runtime.yml').read_text()
        runner=(ROOT/'tests/runtime/run.sh').read_text()
        self.assertIn('axe-core@4.14.0',flow)
        self.assertIn('tests/runtime/axe_audit.py',runner)
        self.assertIn("'wcag_conformance_claim': False",source)
        self.assertIn("'human_screenreader_testing': 'NOT_RUN'",source)

    def test_extended_keyboard_and_reflow_audit(self):
        source=(ROOT/'tests/runtime/axe_audit.py').read_text()
        self.assertIn('keyboard_and_mobile_checks',source)
        self.assertIn('ci-long-content',source)
        self.assertIn("'wcag_conformance_claim': False",source)
        self.assertIn('assert not any(row',source)

    def test_woo_store_api_expects_created_on_new_cart_item(self):
        script=(ROOT/'tests/runtime/woo_store_api.py').read_text()
        self.assertIn('token_a, expected=201)',script)
        self.assertIn('token_b != token_a',script)

    def test_runtime_tests_remain_outside_installable_theme(self):
        for extra in ('tests/runtime/woo_store_api.py','tests/runtime/admin_smoke.py',
                      'tests/runtime/rollback.sh','docs/77-scenarios.json'):
            self.assertTrue((ROOT/extra).is_file())
            self.assertIn(extra,(ROOT/'scripts/package.py').read_text())
        self.assertNotIn('payment complete', (ROOT/'docs/STAGING-ACCEPTANCE.md').read_text())

    def test_packager_does_not_distribute_local_env_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'workspace'
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('dist','__pycache__','*.pyc'))
            (root/'.env').write_text('DUMMY_SECRET=not_for_distribution\n')
            (root/'local-notes.txt').write_text('private dummy\n')
            proc=subprocess.run(['python3','scripts/package.py'],cwd=root,capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            with zipfile.ZipFile(root/'dist'/'Webactueel-Block-Starter-Source-1.0.4.zip') as z:
                self.assertNotIn('.env',z.namelist())
                self.assertNotIn('local-notes.txt',z.namelist())
                self.assertFalse(any('__pycache__' in x or '.pyc' in x for x in z.namelist()))

    def test_packager_rejects_theme_debug_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'workspace'
            shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('dist','__pycache__','*.pyc'))
            theme=root/'theme'/'webactueel-starter'
            debug=theme/'debug.log'
            debug.write_text('test fixture\n')
            proc=subprocess.run(['python3','scripts/package.py'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('Unexpected/missing runtime files',proc.stderr)
            debug.unlink()
            original=theme/'theme.json'
            original.unlink()
            original.symlink_to(THEME/'theme.json')
            proc=subprocess.run(['python3','scripts/package.py'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('symlink',proc.stderr.lower())

    def test_packager_rejects_symlinked_theme_ancestor(self):
        # Before 1.0.4, a linked `theme/` ancestor bypassed the leaf checks.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'workspace'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('dist','__pycache__','*.pyc'))
            original=root/'theme'
            outside=root/'external-theme-source'
            shutil.move(str(original), str(outside))
            original.symlink_to(outside, target_is_directory=True)
            proc=subprocess.run(['python3','scripts/package.py'],cwd=root,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('Symlinked theme path is forbidden',proc.stderr)
            self.assertFalse((root/'dist'/'Webactueel-Block-Starter-1.0.4-STAGING.zip').exists())

    def test_release_zips_rebuild_byte_exact_without_noise(self):
        # Independent black-box check: compare both archives with the actual
        # allow-listed source files, then build a second time and hash both.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'workspace'
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns('dist','__pycache__','*.pyc'))
            command=['python3','scripts/package.py']
            run=subprocess.run(command,cwd=root,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            install=root/'dist'/'Webactueel-Block-Starter-1.0.4-STAGING.zip'
            source=root/'dist'/'Webactueel-Block-Starter-Source-1.0.4.zip'
            expected_prefix='webactueel-starter/'
            with zipfile.ZipFile(install) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), {expected_prefix+x for x in FILES})
                for path in archive.infolist():
                    name=path.filename
                    self.assertEqual(archive.read(name),(root/'theme'/name).read_bytes())
                    self.assertEqual((path.external_attr>>16)&0o170000,0o100000)
            with zipfile.ZipFile(source) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()),
                    {'theme/'+expected_prefix+x for x in FILES} |
                    {'.gitignore','.github/workflows/ci.yml','README.md',
                     'docs/QA.md','scripts/package.py','tests/test_starter.py',
                     '.github/workflows/wordpress-runtime.yml',
                     'tests/runtime/compose.yaml','tests/runtime/run.sh',
                     'tests/runtime/browser_smoke.py','tests/runtime/seed_woo.php',
                     'docs/STAGING-ACCEPTANCE.md','docs/77-scenarios.json',
                     'tests/runtime/woo_store_api.py','tests/runtime/admin_smoke.py',
                     'tests/runtime/rollback.sh','tests/runtime/axe_audit.py'} |
                    {'optional-scaffolding/assets/','optional-scaffolding/patterns/',
                     'optional-scaffolding/styles/'})
                for info in archive.infolist():
                    if info.filename.startswith('theme/'):
                        self.assertEqual(archive.read(info.filename),(root/info.filename).read_bytes())
                    if info.filename.endswith('/'):
                        self.assertEqual(archive.read(info.filename),b'')
                    elif not info.filename.startswith('theme/'):
                        self.assertEqual(archive.read(info.filename),(root/info.filename).read_bytes())
            import hashlib
            before=[hashlib.sha256(path.read_bytes()).hexdigest() for path in (install,source)]
            rerun=subprocess.run(command,cwd=root,capture_output=True,text=True)
            self.assertEqual(rerun.returncode,0,rerun.stderr)
            after=[hashlib.sha256(path.read_bytes()).hexdigest() for path in (install,source)]
            self.assertEqual(before,after)

    def test_release_paths_do_not_follow_symlinks_above_theme(self):
        script=(ROOT/'scripts/package.py').read_text()
        self.assertIn('THEME.relative_to(ROOT).parts',script)
        self.assertIn('cursor.is_symlink()',script)

    def test_packaging_contains_guards(self):
        src=(ROOT/'scripts'/'package.py').read_text()
        for required in ('relative_to','ZipInfo','testzip','read_bytes','sha256','ZipFile','RUNTIME_FILES','SOURCE_FILES','is_symlink'):
            self.assertIn(required,src)

if __name__=='__main__':unittest.main()
