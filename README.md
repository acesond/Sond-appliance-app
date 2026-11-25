# 가전 조합·체감가 계산 웹앱

`index.html` 단일 파일 (외부 의존성 0). 390px 모바일 기준 + PC 반응형.

**배포 주소**: https://acesond.github.io/Sond-appliance-app/ (GitHub Pages, `main` / root — `main`에 푸시하면 자동 반영)

## 배포 전 바꿀 곳

`index.html` `<script>` 맨 위 `CONFIG`:

```js
const CONFIG = {
  kakaoOpenChatUrl: "https://open.kakao.com/o/XXXXXXXX",  // ← 실제 오픈카톡방 링크로 교체
  threadsUrl: "https://www.threads.com/@sond__b",
  blogUrl: "https://blog.naver.com/lgbestshopson",
  ...
};
```

오픈카톡방 링크만 바꾸면 CTA가 실제 상담으로 연결됩니다.

## 화면 구성

1. 히어로: 예상 최종 체감가 / 정상가 대비 절약률 / 정상가·실결제·품목 수
2. 품목 조합: 9개 품목(TV·냉장고·세탁건조·에어컨·식기세척기·로봇청소기·공기청정기·인덕션·무선청소기), 각 프리미엄/가성비/직접입력 + 품목별 **모델명 입력(선택)** + 빠른 조합 3종
3. 결제 혜택: 제휴카드 5/7/10%(한도), 상품권 3/5/7%, 포인트·사은품 토글
4. 계산 상세: 정상가 → 기본할인 → 다품목(2:3%·3:5%·4:7%·5+:9%) → 카드 → 상품권 → 실결제 → 포인트·사은품 → 최종 체감가
5. 비교: 온라인 단품 최저가(폐가전 수거·에어컨 설치비 포함) vs 베스트샵 다품목, 유리한 쪽 자동 판정
6. 견적 요청: 예산·입주 시기·지역 + 견적서 텍스트 복사(품목별 입력한 모델명 포함) + 오픈카톡/스레드 버튼

## 검증

```bash
LD_LIBRARY_PATH=/workspace/.libs/usr/lib/x86_64-linux-gnu python3 test_app.py   # 클릭·계산·복사·스크린샷
LD_LIBRARY_PATH=/workspace/.libs/usr/lib/x86_64-linux-gnu python3 test_model_input.py  # 모델명 입력·복사 반영·오버플로
LD_LIBRARY_PATH=/workspace/.libs/usr/lib/x86_64-linux-gnu python3 regress.py    # 빈 상태·1품목·직접입력·반응형
LD_LIBRARY_PATH=/workspace/.libs/usr/lib/x86_64-linux-gnu python3 final_shots.py # 최종 4장 재생성
```

컨테이너에 Chromium 시스템 라이브러리가 없어 `fetch_libs.py`로 deb에서 `/workspace/.libs`로 추출해 두었습니다(재실행 시 재사용).

## 스크린샷

| 파일 | 크기 |
|---|---|
| preview-top-390.png | 780×1688 (390×844 @2x) |
| preview-result-390.png | 780×2360 (390×1180 @2x) |
| preview-cta-390.png | 780×1688 (390×844 @2x) |
| preview-desktop.png | 1180×1600 |
