# Third-Party Notices

Rayobrowse includes the following third-party open-source components. Their
license terms apply to those components only and do not affect the proprietary
Rayobrowse software itself. See LICENSE for Rayobrowse's own license terms.

---

## noVNC

**Version:** 1.6.0
**Source:** https://github.com/novnc/noVNC
**License:** Mozilla Public License 2.0 (MPL-2.0)
**Used for:** In-browser VNC viewer served on port 6080.

### Modification

Rayobrowse ships a patched version of `core/rfb.js`. The modification fixes
clipboard encoding: the VNC ServerCutText message uses Latin-1 by default, but
x11vnc passes raw UTF-8 bytes from X selections. The patch switches decoding to
UTF-8 via `TextDecoder`, restoring correct clipboard behavior for CJK and other
non-ASCII text.

The following single-line change was applied to `core/rfb.js` (relative to the
upstream noVNC 1.6.0 release):

```diff
-    const text = this._sock.rQshiftStr(length);
+    const _bytes = this._sock.rQshiftBytes(length); const text = new TextDecoder("utf-8").decode(_bytes);
```

All other noVNC files are unmodified from the upstream release.

### MPL-2.0 License Notice

In accordance with the Mozilla Public License 2.0, the source code of the
modified file is made available above (in diff form). The full MPL-2.0 license
text is available at: https://mozilla.org/MPL/2.0/

The unmodified noVNC source is available at:
https://github.com/novnc/noVNC/tree/v1.6.0

Copyright (C) 2019 The noVNC Authors

---

## websockify

**Source:** https://github.com/novnc/websockify
**License:** GNU Lesser General Public License v3.0 (LGPL-3.0)
**Used for:** WebSocket-to-TCP bridge that connects the noVNC viewer to x11vnc.

websockify is installed unmodified as a Python package inside the Docker image.
In accordance with LGPL-3.0, you may replace websockify with a compatible
version of your own by modifying the Docker image.

The full LGPL-3.0 license text is available at:
https://www.gnu.org/licenses/lgpl-3.0.html

The websockify source is available at:
https://github.com/novnc/websockify

Copyright (C) 2012-2021 Joel Martin and websockify contributors

---

## Chromium

**Source:** https://chromium.googlesource.com/chromium/src
**License:** BSD 3-Clause and multiple component licenses
**Used for:** Browser engine. Rayobrowse tracks upstream Chromium releases and
applies a focused set of patches to reduce fingerprint entropy and improve
automation compatibility.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of Google Inc. nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.

Copyright (c) 2006 The Chromium Authors. All rights reserved.

Chromium also incorporates numerous third-party components with their own
licenses. The full set of Chromium license notices is available at:
https://chromium.googlesource.com/chromium/src/+/main/LICENSE

---

## Other Python Dependencies

The Docker image installs the following packages via pip. Each is used
unmodified and subject to its own license:

| Package       | License         | Source                                      |
|---------------|-----------------|---------------------------------------------|
| aiohttp       | Apache-2.0      | https://github.com/aio-libs/aiohttp         |
| geoip2        | Apache-2.0      | https://github.com/maxmind/GeoIP2-python    |
| numpy         | BSD-3-Clause    | https://github.com/numpy/numpy              |
| playwright    | Apache-2.0      | https://github.com/microsoft/playwright     |
| pytweening    | BSD-3-Clause    | https://github.com/asweigart/pytweening     |
| PyYAML        | MIT             | https://github.com/yaml/pyyaml              |
| python-dotenv | BSD-3-Clause    | https://github.com/theskumar/python-dotenv  |
| requests      | Apache-2.0      | https://github.com/psf/requests             |
| rich          | MIT             | https://github.com/Textualize/rich          |
| screeninfo    | MIT             | https://github.com/rr-/screeninfo           |
