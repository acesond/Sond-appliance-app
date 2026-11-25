import asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

BASE = pathlib.Path("/workspace/build/appliance-app")
URL = (BASE / "index.html").as_uri()

async def main():
    console, errors, failed = [], [], []
    ok = True
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                  locale="ko-KR", timezone_id="Asia/Seoul",
                                  user_agent="Mozilla/5.0 (Linux; Android 14; SM-S918N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36")
        page = await ctx.new_page()
        page.on("console", lambda m: console.append((m.type, m.text)))
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("requestfailed", lambda r: failed.append((r.url, r.failure)))
        await page.add_init_script("""
          window.__copied = null;
          if(navigator.clipboard) navigator.clipboard.writeText = function(t){ window.__copied = t; return Promise.resolve(); };
        """)
        await page.goto(URL, wait_until="load")
        await page.wait_for_timeout(400)

        async def txt(sel):
            return (await page.inner_text(sel)).strip()

        # 기본 상태: 프리셋 move (TV·냉장고·세탁건조·에어컨·식기세척기)
        print("start count:", await txt("#hCount"), "| final:", await txt("#dFinal"))
        model_inputs = page.locator(".mwrap input")
        print("model inputs total:", await model_inputs.count(), "| visible:",
              await page.locator(".mwrap input:visible").count())
        ph = await page.get_attribute('.item[data-id="tv"] .mwrap input', "placeholder")
        print("placeholder:", ph)

        # 1) 모델명 입력해도 품목 선택이 풀리지 않는지
        before = await txt("#hCount")
        await page.click('.item[data-id="tv"] .mwrap input')
        await page.wait_for_timeout(200)
        print("focus input -> count:", await txt("#hCount"), "| tv selected:",
              await page.evaluate("document.querySelector('.item[data-id=\"tv\"]').classList.contains('sel')"))
        await page.click('.item[data-id="tv"] .mwrap input')
        await page.wait_for_timeout(200)
        print("second click -> count:", await txt("#hCount"))
        if await txt("#hCount") != before:
            ok = False
            print("FAIL: model input click toggled the item")

        await page.type('.item[data-id="tv"] .mwrap input', "OLED65C4", delay=20)
        await page.wait_for_timeout(250)
        print("after type sub:", (await txt('.item[data-id="tv"] .sub')))
        print("typed value:", await page.input_value('.item[data-id="tv"] .mwrap input'))
        if await page.input_value('.item[data-id="tv"] .mwrap input') != "OLED65C4":
            ok = False
            print("FAIL: typed model not kept in input")

        # 2) 등급을 바꿔도 모델명 유지
        await page.click('.item[data-id="tv"] .tiers button[data-tier="value"]')
        await page.wait_for_timeout(250)
        print("after tier=value count:", await txt("#hCount"), "| value:",
              await page.input_value('.item[data-id="tv"] .mwrap input'))

        # 3) 직접 금액 입력 품목에도 모델명
        await page.click('.item[data-id="robot"]')
        await page.wait_for_timeout(150)
        await page.click('.item[data-id="robot"] .tiers button[data-tier="custom"]')
        await page.fill('.item[data-id="robot"] .cwrap input', "1550000")
        await page.type('.item[data-id="robot"] .mwrap input', "SM-R72", delay=20)
        await page.wait_for_timeout(250)
        print("robot custom:", await txt('.item[data-id="robot"] .pnow'), "| sub:",
              await txt('.item[data-id="robot"] .sub'), "| model:",
              await page.input_value('.item[data-id="robot"] .mwrap input'))

        # 4) 견적서 복사에 모델명 반영
        await page.fill("#fRegion", "대구 달서구 상인동")
        await page.click("#copyBtn")
        await page.wait_for_timeout(500)
        copied = await page.evaluate("window.__copied") or ""
        print("TOAST:", await txt("#toast"))
        print("COPIED >>>")
        print(copied)
        print("<<<")
        if "OLED65C4" not in copied or "SM-R72" not in copied:
            ok = False
            print("FAIL: copied quote missing model names")
        if "가격 기준" not in copied:
            ok = False
            print("FAIL: copied quote missing price-basis note")

        # 5) 선택 해제 후 재선택해도 모델명 유지되는지
        await page.click('.item[data-id="tv"] h3')
        await page.wait_for_timeout(200)
        print("deselect tv count:", await txt("#hCount"), "| input hidden:",
              not await page.locator('.item[data-id="tv"] .mwrap').is_visible())
        await page.click('.item[data-id="tv"] h3')
        await page.wait_for_timeout(200)
        print("reselect tv value:", await page.input_value('.item[data-id="tv"] .mwrap input'))

        # 6) 프리셋 이동 후에도 카드 렌더 깨짐 없는지
        await page.click('#presets button[data-preset="honsu"]')
        await page.wait_for_timeout(300)
        print("honsu count:", await txt("#hCount"), "| visible model inputs:",
              await page.locator(".mwrap input:visible").count())

        # 7) 오버플로 / 레이아웃
        ov = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        cardov = await page.evaluate("""
          Array.from(document.querySelectorAll('.item')).map(function(c){
            return [c.dataset.id, c.scrollWidth - c.clientWidth, c.querySelector('.mwrap input').scrollWidth - c.querySelector('.mwrap input').clientWidth];
          }).filter(function(x){ return x[1] > 0; })
        """)
        print("doc overflow px:", ov, "| card overflow:", json.dumps(cardov, ensure_ascii=False))
        if ov != 0:
            ok = False
            print("FAIL: horizontal overflow", ov)

        # 8) 키보드 Enter는 입력칸만 닫고 카드 토글 안 함
        await page.click('.item[data-id="air"] .mwrap input')
        cnt = await txt("#hCount")
        await page.type('.item[data-id="air"] .mwrap input', "AF17DX", delay=10)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(200)
        print("enter -> count:", cnt, "->", await txt("#hCount"), "| focused:",
              await page.evaluate("document.activeElement.tagName"))
        if cnt != await txt("#hCount"):
            ok = False
            print("FAIL: Enter toggled item")

        # 스크린샷 (모델명 보이는 카드 영역)
        await page.evaluate("document.getElementById('pick').scrollIntoView({block:'start'})")
        await page.wait_for_timeout(300)
        await page.evaluate("window.scrollBy(0,-62)")
        await page.wait_for_timeout(300)
        await page.screenshot(path=str(BASE/"preview-model-390.png"))

        print("CONSOLE:", json.dumps(console, ensure_ascii=False))
        print("PAGEERRORS:", json.dumps(errors, ensure_ascii=False))
        print("FAILED:", json.dumps(failed, ensure_ascii=False))
        if errors or failed or [c for c in console if c[0] == "error"]:
            ok = False
        print("RESULT:", "PASS" if ok else "FAIL")
        await b.close()
        return 0 if ok else 1

sys.exit(asyncio.run(main()))
