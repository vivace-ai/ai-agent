// 가게 홈페이지에 문의 단추와 채팅 창을 붙인다.
(function () {
  const server = new URL(document.currentScript.src).origin;
  const frame = document.createElement("iframe");
  frame.src = server + "/";
  frame.title = "모과상점 문의";
  frame.style.cssText = "display:none;position:fixed;right:20px;" +
    "bottom:84px;width:360px;height:520px;max-width:calc(100vw - 40px);" +
    "max-height:calc(100vh - 120px);border:0;border-radius:16px;" +
    "box-shadow:0 12px 40px rgba(0,0,0,.2);z-index:9999;background:#fff";
  const button = document.createElement("button");
  button.textContent = "문의하기";
  button.style.cssText = "position:fixed;right:20px;bottom:20px;" +
    "padding:14px 20px;border:0;border-radius:28px;background:#d9a514;" +
    "color:#fff;font-size:16px;font-weight:700;cursor:pointer;z-index:9999";
  button.addEventListener("click", function () {
    const open = frame.style.display === "none";
    frame.style.display = open ? "block" : "none";
    button.textContent = open ? "닫기" : "문의하기";
  });
  document.body.append(frame, button);
})();
