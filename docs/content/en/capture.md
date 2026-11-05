---
id: capture
title: Capture and visual feedback
description: Capture and visual feedback
section: User guide
order: 12
revision: 1
---

## Overview {#overview}

The CLI and external MCP interface can capture one current frame. Integrated chat does not automatically receive screenshots: describe what you observe after an edit. A compiled shader is not a visual comparison.

```bash
python -m companion capture capture.png
```

Maximum dimension is 1280 pixels. Capture performs one GPU readback and may include the ReShade overlay. It is not continuous recording and performs no HDR tone mapping. A resize during capture may require a retry.

1. Prepare the scene and request a read-only capture.
2. Review the image and record settings for comparison.
3. If using an external AI client, explicitly decide whether to send that image; its provider data policy applies.

## Related topics {#related}

- [External MCP clients](doc:mcp)
- [History, storage and provider data](doc:history-privacy)
- [DX12, restoration and HUD limits](doc:dx12-hud)
