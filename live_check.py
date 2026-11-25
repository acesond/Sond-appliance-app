import asyncio, json
from playwright.async_api import async_playwright

URL = "https://acesond.github.io/Sond-appliance-app/"
SHOT_DIR = "/workspace/downloads/appliance-quote-webapp"

async def main():
    console, errors, failed, responses = [], [], [], []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                  locale="ko-KR", timezone_id="Asia/Seoul",
                                  user_agent="Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36")
        page = await ctx.new_page()
        page.on("console", lambda m: console.append((m.type, m.text)))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append((r.url, r.failure)))
        page.on("response", lambda r: responses.append((r.status, r.url)))
        await page.add_init_script("""
          window.__copied = null;
          if(navigator.clipboard) navigator.clipboard.writeText = function(t){ window.__copied = t; return Promise.resolve(); };
        """)
        await page.goto(URL, wait_until="load", timeout=60000)
        await page.wait_for_timeout(1500)

        info = {}
        info["url"] = page.url
        info["title"] = await page.title()
        info["viewport"] = await page.evaluate("({w: innerWidth, h: innerHeight, dpr: devicePixelRatio})")
        info["overflowX"] = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        info["hFinal"] = (await page.inner_text("#hFinal")).strip()
        info["hPct"] = (await page.inner_text("#hPct")).strip()
        info["hCount"] = (await page.inner_text("#hCount")).strip()
        info["verdict"] = (await page.inner_text("#verdictText")).strip()
        info["detailRows"] = await page.locator("#bd .bdrow").count()
        info["compareCards"] = await page.locator("#cmp .c").count()

        # 모델명 입력칸 존재
        info["modelInputs"] = await page.locator(".mwrap input").count()
        info["modelInputsVisible"] = await page.locator(".mwrap input:visible").count()
        info["modelPlaceholder"] = await page.get_attribute('.item[data-id="tv"] .mwrap input', "placeholder")

        # interaction smoke: add one item, switch tier, remove
        await page.click('.item[data-id="airpur"]')
        await page.wait_for_timeout(300)
        info["afterAdd"] = (await page.inner_text("#hCount")).strip()
        await page.click('.item[data-id="airpur"]')
        await page.wait_for_timeout(300)
        info["afterRemove"] = (await page.inner_text("#hCount")).strip()

        # 모델명 입력: 클릭해도 품목이 풀리지 않고, 값이 유지되는지
        count_before = (await page.inner_text("#hCount")).strip()
        await page.click('.item[data-id="tv"] .mwrap input')
        await page.wait_for_timeout(200)
        await page.type('.item[data-id="tv"] .mwrap input', "OLED65C4", delay=15)
        await page.wait_for_timeout(250)
        info["countBeforeModel"] = count_before
        info["countAfterModel"] = (await page.inner_text("#hCount")).strip()
        info["tvModelValue"] = await page.input_value('.item[data-id="tv"] .mwrap input')
        info["tvTierStillOn"] = await page.evaluate("!!document.querySelector('.item[data-id=\"tv\"] .tiers button.on')")
        await page.click('.item[data-id="tv"] .tiers button[data-tier="value"]')
        await page.wait_for_timeout(250)
        info["tvModelAfterTierSwitch"] = await page.input_value('.item[data-id="tv"] .mwrap input')

        # 견적서 텍스트 복사에 모델명 반영
        await page.fill("#fRegion", "대구 달서구 상인동")
        await page.click("#copyBtn")
        await page.wait_for_timeout(500)
        copied = await page.evaluate("window.__copied") or ""
        info["copiedHasModel"] = "OLED65C4" in copied
        info["copiedHasBasis"] = "가격 기준" in copied
        info["toast"] = (await page.inner_text("#toast")).strip()
        quote_lines = [l for l in copied.split("\n") if "OLED65C4" in l]
        info["quoteModelLine"] = quote_lines

        # CTA links
        info["kakaoHref"] = await page.get_attribute("#ctaKakao, a[href*='open.kakao']", "href")
        info["threadsHref"] = await page.get_attribute("a[href*='threads']", "href")

        # 모델명 입력 화면 스크린샷
        await page.evaluate("document.getElementById('pick').scrollIntoView({block:'start'})")
        await page.wait_for_timeout(350)
        await page.evaluate("window.scrollBy(0, -62)")
        await page.wait_for_timeout(350)
        await page.screenshot(path=SHOT_DIR + "/live-390-model-input.png")
        info["cardOverflow"] = await page.evaluate("""
          Array.from(document.querySelectorAll('.item')).map(function(c){
            return [c.dataset.id, c.scrollWidth - c.clientWidth];
          }).filter(function(x){ return x[1] > 0; })
        """)

        await page.evaluate("window.scrollTo(0,0)")
        await page.wait_for_timeout(300)
        await page.screenshot(path="/workspace/build/appliance-app/live-390-top.png")
        await page.screenshot(path=SHOT_DIR + "/live-390-top.png")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(400)
        await page.screenshot(path="/workspace/build/appliance-app/live-390-bottom.png")
        await page.screenshot(path=SHOT_DIR + "/live-390-bottom.png")

        print(json.dumps(info, ensure_ascii=False, indent=1))
        print("CONSOLE:", json.dumps(console, ensure_ascii=False))
        print("PAGEERRORS:", json.dumps(errors, ensure_ascii=False))
        print("FAILED_REQUESTS:", json.dumps(failed, ensure_ascii=False))
        print("RESPONSES:", json.dumps([r for r in responses], ensure_ascii=False))
        await b.close()

asyncio.run(main())
