import base64
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
EMAIL = os.environ.get("AURAMATE_EMAIL", "")
PASSWORD = os.environ.get("AURAMATE_PASSWORD", "")
SESSION_FILE = Path(os.environ.get("AURAMATE_SESSION_FILE", str(ROOT / "work/auramate-session.json")))
FORTUNE_URL = os.environ.get("AURAMATE_FORTUNE_URL", "https://auramate.net/play/fortune-2026")


class CDP:
    def __init__(self, ws_url):
        assert ws_url.startswith("ws://")
        host_port, path = ws_url[5:].split("/", 1)
        host, port = host_port.split(":")
        self.sock = socket.create_connection((host, int(port)), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        resp = self.sock.recv(4096)
        if b"101" not in resp.split(b"\r\n", 1)[0]:
            raise RuntimeError(resp.decode(errors="ignore"))
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
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(header + masked)

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise EOFError
            buf += chunk
        return buf

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
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self._recv_exact(length)))
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
        msg_id = self.next_id
        self._send_frame(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        deadline = time.time() + timeout
        while time.time() < deadline:
            msg = self.recv()
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})
        raise TimeoutError(method)


def wait_http(url, timeout=12):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(url)


def start_chrome():
    args = [
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
    return subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def nav(cdp, url, wait=3):
    cdp.call("Page.navigate", {"url": url})
    time.sleep(wait)


def eval_js(cdp, expr, await_promise=False):
    return cdp.call(
        "Runtime.evaluate",
        {"expression": expr, "awaitPromise": await_promise, "returnByValue": True},
    ).get("result", {}).get("value")


def screenshot(cdp, path):
    data = cdp.call("Page.captureScreenshot", {"format": "jpeg", "quality": 88, "captureBeyondViewport": False})["data"]
    path.write_bytes(base64.b64decode(data))


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    proc = start_chrome()
    try:
        pages = wait_http(f"http://127.0.0.1:{PORT}/json/list")
        page = next((p for p in pages if p.get("type") == "page"), pages[0])
        cdp = CDP(page["webSocketDebuggerUrl"])
        cdp.call("Page.enable")
        cdp.call("Runtime.enable")
        cdp.call("Network.enable")
        if SESSION_FILE.exists():
            session = json.loads(SESSION_FILE.read_text())
            nav(cdp, "https://auramate.net", 2)
            for item in (session.get("cookie") or "").split(";"):
                if "=" in item:
                    name, value = item.strip().split("=", 1)
                    cdp.call("Network.setCookie", {"name": name, "value": value, "domain": "auramate.net", "path": "/", "secure": True})
            storage_js = f"""
(() => {{
  const localItems = {json.dumps(session.get("localStorage") or {})};
  const sessionItems = {json.dumps(session.get("sessionStorage") or {})};
  for (const [k, v] of Object.entries(localItems)) localStorage.setItem(k, v);
  for (const [k, v] of Object.entries(sessionItems)) sessionStorage.setItem(k, v);
  return {{local: Object.keys(localStorage).length, session: Object.keys(sessionStorage).length}};
}})()
"""
            eval_js(cdp, storage_js)
        else:
            if not EMAIL or not PASSWORD:
                raise RuntimeError("未找到登录信息；请设置 AURAMATE_EMAIL 和 AURAMATE_PASSWORD")
            nav(cdp, "https://auramate.com.cn", 3)
            eval_js(cdp, """
(() => {
  const btn = Array.from(document.querySelectorAll('button')).find(e => (e.innerText || '').includes('密码登录'));
  if (btn) btn.click();
  return document.body.innerText.slice(0, 300);
})()
""")
            time.sleep(1.2)
            eval_js(cdp, f"""
(() => {{
  const fire = el => {{
    el.dispatchEvent(new Event('input', {{bubbles:true}}));
    el.dispatchEvent(new Event('change', {{bubbles:true}}));
  }};
  const setValue = (el, value) => {{
    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    setter.call(el, value);
    fire(el);
  }};
  const inputs = Array.from(document.querySelectorAll('input')).filter(el => el.offsetParent !== null);
  const email = {json.dumps(EMAIL)};
  const password = {json.dumps(PASSWORD)};
  if (inputs[0]) {{ inputs[0].focus(); setValue(inputs[0], email); }}
  if (inputs[1]) {{ inputs[1].focus(); setValue(inputs[1], password); }}
  const btn = Array.from(document.querySelectorAll('button')).find(b => /登录\\s*\\/\\s*注册|登录|登陆/.test(b.innerText || '') && !/验证码/.test(b.innerText || ''));
  if (btn) btn.click();
  return {{
    text: document.body.innerText.slice(0, 500),
    inputs: inputs.map(i => i.placeholder || i.type || '')
  }};
}})()
""")
            time.sleep(6)
        nav(cdp, FORTUNE_URL, 5)
        eval_js(cdp, "window.scrollTo(0, 0)")
        time.sleep(1)
        screenshot(cdp, ASSETS / "auramate-fortune.jpg")

        # Discover a likely relationship page, then capture the first one that renders relationship content.
        candidates = [
            "https://auramate.net/play/relationship",
            "https://auramate.net/play/fate-match",
            "https://auramate.net/play/compatibility",
            "https://auramate.net/play/love",
            "https://auramate.net/play/match",
            "https://auramate.net/app",
        ]
        chosen = None
        for url in candidates:
            nav(cdp, url, 4)
            text = eval_js(cdp, "document.body.innerText.slice(0, 2000)") or ""
            if any(k in text for k in ["缘分", "合盘", "关系", "契合", "伴侣"]):
                chosen = url
                break
        if chosen:
            eval_js(cdp, "window.scrollTo(0, 0)")
            time.sleep(1)
            screenshot(cdp, ASSETS / "auramate-match.jpg")
        print(json.dumps({"ok": True, "output_dir": str(ASSETS), "match_url": chosen}, ensure_ascii=False))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
