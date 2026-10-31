"""Generic browser and accessibility checks for isolated WordPress theme ZIPs."""
import json
import re
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

WIDTHS=(320,375,390,412,600,740,741,768,900,1024,1200,1281,1440)
REPORT=Path('reports/external-browser.json')
AXE=Path('node_modules/axe-core/axe.min.js')
PHP_DIAGNOSTIC=re.compile(r'(?:PHP\s+)?(?:Warning|Notice|Deprecated|Fatal error|Parse error)\s*:',re.I)

def local_only(route):
    url=urlsplit(route.request.url)
    if url.scheme in ('http','https') and url.hostname not in ('localhost','127.0.0.1'):
        route.abort()
    else:
        route.continue_()

def main():
    REPORT.parent.mkdir(exist_ok=True)
    checked=[]
    violations=[]
    try:
        with sync_playwright() as pw:
            for engine_name in ('chromium','firefox','webkit'):
                browser=getattr(pw,engine_name).launch(headless=True)
                try:
                    context=browser.new_context(viewport={'width':390,'height':850})
                    context.route('**/*',local_only)
                    page=context.new_page()
                    errors=[]
                    asset_errors=[]
                    page.on('pageerror',lambda e: errors.append(type(e).__name__))
                    page.on('response',lambda r: asset_errors.append(r.status) if r.status>=400 and '/wp-content/' in r.url else None)
                    for width in WIDTHS:
                        page.set_viewport_size({'width':width,'height':850})
                        response=page.goto('http://localhost:8080/',wait_until='domcontentloaded',timeout=45000)
                        assert response and response.status==200
                        assert page.title().strip()
                        assert not PHP_DIAGNOSTIC.search(page.content())
                        metrics=page.evaluate('''() => ({viewport:innerWidth,scroll:document.documentElement.scrollWidth})''')
                        assert metrics['scroll']<=metrics['viewport']+2
                        checked.append({'engine':engine_name,'width':width,'status':'PASS'})
                        if engine_name=='chromium' and width in (390,1440):
                            assert AXE.is_file()
                            page.add_script_tag(path=str(AXE.resolve()))
                            axe=page.evaluate('''async () => await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})''')
                            violations.extend({'width':width,'rule':v['id'],'node_count':len(v.get('nodes',[]))} for v in axe['violations'])
                    no_js=browser.new_context(java_script_enabled=False,viewport={'width':375,'height':850})
                    no_js.route('**/*',local_only)
                    response=no_js.new_page().goto('http://localhost:8080/',wait_until='domcontentloaded')
                    assert response and response.status==200
                    no_js.close()
                    assert not errors and not asset_errors
                    context.close()
                finally:
                    browser.close()
        status='FAIL' if violations else 'PASS'
        data={'status':status,'browser_viewports':checked,'automated_axe_violations':violations,'wcag_em_manual':'NOT_RUN','production_approved':False}
    except Exception as exc:
        data={'status':'FAIL','error_type':type(exc).__name__,'browser_viewports':checked,'wcag_em_manual':'NOT_RUN','production_approved':False}
    REPORT.write_text(json.dumps(data,indent=2)+'\n')
    print('External browser QA:',data['status'])
    raise SystemExit(0 if data['status']=='PASS' else 1)

if __name__=='__main__':
    main()
