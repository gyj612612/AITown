# Steam 上传说明

本目录提供 `SteamPipe` 模板文件，配合 `steamcmd` 上传构建。

## 目录约定

- 本地打包输出：`release/windows`
- 构建脚本：`scripts/build_windows.ps1`

## 使用步骤

1. 先构建：
   - `powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version 1.0.0 -SteamAppId <你的AppID>`
2. 修改 `steam/app_build_aitown.vdf` 中的：
   - `appid`
   - `desc`
   - `setlive`
3. 使用 `steamcmd` 执行：
   - `steamcmd +login <account> +run_app_build "..\\steam\\app_build_aitown.vdf" +quit`

## 注意

- `steam_appid.txt` 仅用于本地测试，正式包可去掉。
- 提交前先执行 `python scripts/release_check.py`。
- 构建脚本默认走隔离Python 3.11环境，避免打包体积异常膨胀。
