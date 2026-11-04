"""Optional browser smoke test. Install playwright separately; not required to run the mission."""
from pathlib import Path
import json
import shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'evidence/jezero'


def main():
    with sync_playwright() as pw:
        chrome=shutil.which('google-chrome') or shutil.which('chromium')
        kwargs={'headless':True,'args':['--no-sandbox']}
        if chrome:kwargs['executable_path']=chrome
        browser=pw.chromium.launch(**kwargs)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto((OUT/'viewer.html').as_uri());page.wait_for_timeout(250)
        assert page.locator('#agents tr').count()==6
        page.locator('#seek').evaluate('(e)=>{e.value=e.max;e.dispatchEvent(new Event("input"))}')
        assert page.locator('#samples').inner_text()=='4 / 4'
        assert page.locator('#coverage').inner_text()=='100.0 %'
        for layer in ['prior','reference','sigma','mean']:
            page.locator('#layer').select_option(layer);page.wait_for_timeout(100)
        page.screenshot(path=str(OUT/'viewer_screenshot.png'),full_page=True)
        assert not errors,errors
        (OUT/'browser_check.json').write_text(json.dumps({'status':'passed','agents':6,'final_samples':4,'layers_checked':4,'javascript_errors':errors},indent=2)+'\n')
        browser.close()


if __name__=='__main__':main()
