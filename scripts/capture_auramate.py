#!/usr/bin/env python3
"""Log in with Chrome and capture live AuraMate product pages."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import json
import os
import socket
import struct
import subprocess
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(os.environ.get("AURAMATE_CAPTURE_DIR", str(ROOT / "work/assets"))).expanduser().resolve()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = int(os.environ.get("AURAMATE_CDP_PORT", "9337"))
PROFILE = os.environ.get("AURAMATE_CDP_PROFILE", "/private/tmp/auramate-gzh-month-cdp")
CREDENTIALS_FILE = Path(
    os.environ.get("AURAMATE_CREDENTIALS_FILE", str(ROOT / "scripts/auramate_credentials.local.json"))
).expanduser()
FORTUNE_URL = os.environ.get("AURAMATE_FORTUNE_URL", "https://auramate.com.cn/play/fortune-2026")
MATCH_CANDIDATES = [
    "https://auramate.com.cn/play/fate-match",
    "https://auramate.com.cn/play/relationship",
    "https://auramate.com.cn/play/compatibility",
    "https://auramate.com.cn/play/love",
    "https://auramate.com.cn/play/match",
    "https://auramate.com.cn/app",
]


class CDP:
    def __init__(self, ws_url):
        assert ws_url.startswith("ws://")
        host_port, path = ws_url[5:].split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode())
        response = self.sock.recv(4096)
        if b"101" not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(response.decode(errors="ignore"))
        self.next_id = 0

    def _send_frame(self, payload):
        data = payload.encode()
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        elif len(data) < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", len(data)))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", len(data)))
        mask = os.urandom(4)
        header.extend(mask)
        header.extend(bytes(value ^ mask[index % 4] for index, value in enumerate(data)))
        self.sock.sendall(header)

    def _recv_exact(self, size):
        data = b""
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise EOFError
            data += chunk
        return data

    def recv(self):
        chunks = []
        while True:
            first, second = self._recv_exact(2)
            opcode = first & 0x0F
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            if second & 0x80:
                mask = self._recv_exact(4)
                payload = bytes(value ^ mask[index % 4] for index, value in enumerate(self._recv_exact(length)))
            else:
                payload = self._recv_exact(length)
            if opcode == 8:
                raise EOFError
            if opcode in (1, 0):
                chunks.append(payload)
            if first & 0x80:
                return json.loads(b"".join(chunks).decode())

    def call(self, method, params=None, timeout=20):
        self.next_id += 1
        message_id = self.next_id
        self._send_frame(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self.recv()
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})
        raise TimeoutError(method)


def wait_http(url, timeout=12):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.loads(response.read())
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(url)


def load_credentials():
    email = os.environ.get("AURAMATE_EMAIL", "")
    password = os.environ.get("AURAMATE_PASSWORD", "")
    if email and password:
        return email, password
    if CREDENTIALS_FILE.is_file():
        data = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
        return data.get("email", ""), data.get("password", "")
    return "", ""


def start_chrome():
    arguments = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        f"--remote-debugging-port={PORT}",
        f"--user-data-dir={PROFILE}",
        "--window-size=1280,1180",
        "about:blank",
    ]
    return subprocess.Popen(arguments, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def evaluate(cdp, expression):
    return cdp.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
    ).get("result", {}).get("value")


def navigate(cdp, url, wait=3):
    cdp.call("Page.navigate", {"url": url})
    time.sleep(wait)


def page_state(cdp):
    return evaluate(cdp, """
(() => ({
  url: location.href,
  title: document.title,
  text: document.body.innerText.slice(0, 2400),
  loginInput: Array.from(document.querySelectorAll('input[type=password]')).some(el => el.offsetParent !== null)
}))()
""") or {}


def login(cdp, email, password):
    if not email or not password:
        raise RuntimeError(f"未找到 AuraMate 登录信息；请设置环境变量或本机文件 {CREDENTIALS_FILE}")
    navigate(cdp, "https://auramate.com.cn", 3)
    evaluate(cdp, """
(() => {
  const compact = element => (element.innerText || '').replace(/\\s/g, '');
  const button = Array.from(document.querySelectorAll('button')).find(el => compact(el) === '登录');
  if (button) button.click();
})()
""")
    time.sleep(1.5)
    evaluate(cdp, """
(() => {
  const button = Array.from(document.querySelectorAll('button')).find(el => (el.innerText || '').includes('密码登录'));
  if (button) button.click();
})()
""")
    time.sleep(1)
    evaluate(cdp, f"""
(() => {{
  const setValue = (element, value) => {{
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(element, value);
    element.dispatchEvent(new Event('input', {{bubbles:true}}));
    element.dispatchEvent(new Event('change', {{bubbles:true}}));
  }};
  const inputs = Array.from(document.querySelectorAll('input')).filter(element => element.offsetParent !== null);
  if (inputs[0]) setValue(inputs[0], {json.dumps(email)});
  if (inputs[1]) setValue(inputs[1], {json.dumps(password)});
  const compact = element => (element.innerText || '').replace(/\\s/g, '');
  const button = Array.from(document.querySelectorAll('button')).find(el => ['登录', '登录/注册'].includes(compact(el)));
  if (button) button.click();
}})()
""")
    time.sleep(6)


def require_product_page(cdp, label):
    state = page_state(cdp)
    if state.get("loginInput") or "/login" in state.get("url", ""):
        raise RuntimeError(f"{label}仍停留在登录页，拒绝生成截图")
    if not state.get("text", "").strip():
        raise RuntimeError(f"{label}页面为空，拒绝生成截图")
    return state


def screenshot(cdp, path):
    encoded = cdp.call(
        "Page.captureScreenshot",
        {"format": "jpeg", "quality": 88, "captureBeyondViewport": False},
    )["data"]
    path.write_bytes(base64.b64decode(encoded))


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    email, password = load_credentials()
    process = start_chrome()
    try:
        pages = wait_http(f"http://127.0.0.1:{PORT}/json/list")
        page = next((item for item in pages if item.get("type") == "page"), pages[0])
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        login(cdp, email, password)

        navigate(cdp, FORTUNE_URL, 5)
        fortune_state = require_product_page(cdp, "财运分析")
        evaluate(cdp, "window.scrollTo(0, 0)")
        time.sleep(1)
        screenshot(cdp, ASSETS / "auramate-fortune.jpg")

        match_state = None
        for url in MATCH_CANDIDATES:
            navigate(cdp, url, 4)
            state = page_state(cdp)
            if any(keyword in state.get("text", "") for keyword in ["缘分", "合盘", "关系", "契合", "伴侣"]):
                match_state = require_product_page(cdp, "缘分测算")
                break
        if not match_state:
            raise RuntimeError("未找到可用的缘分测算产品页，拒绝沿用旧截图")
        evaluate(cdp, "window.scrollTo(0, 0)")
        time.sleep(1)
        screenshot(cdp, ASSETS / "auramate-match.jpg")

        manifest = {
            "source": "live-chrome",
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "fortune": {"url": fortune_state.get("url"), "file": "auramate-fortune.jpg"},
            "match": {"url": match_state.get("url"), "file": "auramate-match.jpg"},
        }
        (ASSETS / "auramate-capture.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"ok": True, "output_dir": str(ASSETS), "manifest": manifest}, ensure_ascii=False))
    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    main()
