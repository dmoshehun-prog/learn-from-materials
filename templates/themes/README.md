# 六主题作用域规范

`render_page.py` 固定内联本目录六个 CSS 文件。每个文件必须以 `body[data-theme="主题名"]` 作为变量作用域，不得使用独立 `:root`，否则多个主题会互相覆盖。

| 主题名 | 中文名 | 文件 |
|---|---|---|
| `warm-paper` | 雾蓝书房 | `warm-paper.css` |
| `minimal` | 灰白画册 | `minimal.css` |
| `dark` | 深海夜读 | `dark.css` |
| `ink-wash` | 青灰宣纸 | `ink-wash.css` |
| `vintage-editorial` | 暖褐画报 | `vintage-editorial.css` |
| `paper-ink` | 石墨书页 | `paper-ink.css` |

新增主题时同时完成三件事：增加带独立作用域的 CSS、在 `render_page.py` 的 `THEMES` 中登记、在 `base.html` 的主题菜单中增加选项。运行 `verify_static.py`，确认每个主题作用域和菜单项都存在。
