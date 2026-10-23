# CAD 适配器契约

## 1. 调用方式

- 平台通过 stdin 传入 JSON spec；
- 适配器在当前工作目录输出 out.dxf 与 out.png；
- 退出码非 0 视为失败；
- 平台用 adapter_smoke 做契约验收。

## 2. 样例

- example_adapter.py：跨平台参考实现，直接复用后端 bracket/preview；
- 运行：

~~~bash
cd cad-agent-platform
.venv/bin/python tools/adapter_smoke.py --command ".venv/bin/python worker/adapters/example_adapter.py"
~~~

## 3. Windows 适配器（未验证）

### SolidWorks

- 依赖 pywin32 与 SolidWorks 许可；
- 典型调用：SldWorks.Application → OpenDoc6 → SaveAs DXF/PNG；
- 必须处理 COM 异常、进程残留、超时；
- 用 worker/adapters/example_adapter.py 的输入输出契约做壳。

### AutoCAD

- 依赖 ODA File Converter 或 AutoCAD COM；
- DWG→DXF 用 ODA，DXF 生成优先 ezdxf；
- 复杂图需处理图层、标注、图框。

### Altium AD24

- 通过 DelphiScript/COM 输出 BOM/检查结果；
- 当前仅契约，未实现真机脚本。

## 4. 验收

~~~bash
.venv/bin/python tools/adapter_smoke.py --command "<adapter command>"
~~~

要求：退出码 0、out.dxf 含 SECTION、out.png 存在。

> 说明：Windows COM 部分未在本机验证，属于外部阻塞；不要用样例适配器冒充真机结果。
