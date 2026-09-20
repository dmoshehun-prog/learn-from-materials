# 主题作用域规范

`render_page.py` 固定内联本目录的每个 CSS 文件（列表见 `render_page.py::THEMES`，为**唯一真源**）。
每个文件必须以 `body[data-theme="主题名"]` 作为变量作用域，不得使用独立 `:root`，否则多个主题会互相覆盖。

| 主题名 | 中文名 | 文件 |
|---|---|---|
| `warm-paper` | 雾蓝书房 | `warm-paper.css` |
| `minimal` | 灰白画册 | `minimal.css` |
| `dark` | 深海夜读 | `dark.css` |

新增主题时同时完成四件事：增加带独立作用域的 CSS、在 `render_page.py` 的 `THEMES` 中登记、
在 `base.html` 的主题菜单中增加 `<option>`、**并同步 `scripts/verify-page.js` 的 `knownThemes`**。
运行 `verify_static.py`，确认每个主题作用域和菜单项都存在。

> **坑位**：`verify-page.js` 的 `knownThemes` 曾列出 6 个主题（`ink-wash` / `vintage-editorial` / `paper-ink` 并不存在），
> 导致它在 `selectOption` 上 30s 超时、报「测试异常」。静态校验（以 `THEMES` 为准）反而是对的。
> 任何新增/删减主题，都要以 `render_page.py::THEMES` 为基准同步所有消费方。
