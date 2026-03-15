# Steam发布清单（Windows）

## 1. 功能完成度

- 主线可通关（3章）
- 失败结算可触发
- 存档/读档稳定
- 键鼠输入完整且有帮助提示

## 2. 技术验收

- `python -m pytest` 全通过
- `python scripts/smoke_test.py` 通过
- `python -m ruff check .` 通过
- `python scripts/release_check.py` 通过
- 打包产物可在无Python环境启动
- `release/windows` 体积在预期范围内（当前约 34MB）

## 3. 法务与素材

- 第三方素材许可证已收录至 `assets/licenses/`
- 第三方依赖和素材归档见 `THIRD_PARTY_LICENSES.md`
- Steam商店页中补充素材来源与授权说明

## 4. SteamPipe上传

1. 构建：`powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version 1.0.0`
2. 编辑：`steam/app_build_aitown.vdf`（appid、desc、setlive）
3. 上传：`steamcmd +login <account> +run_app_build "..\\steam\\app_build_aitown.vdf" +quit`
4. 在Steam后台验证分支并发布

## 5. 推荐商店页素材

- 胶囊图（616x353, 460x215）
- 5-8张截图（含UI和剧情推进）
- 1段30-60秒预告视频
- 明确玩法描述：AI角色、城镇演化、经营建造
