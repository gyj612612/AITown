# Steam Upload Notes

This folder contains `SteamPipe` template files for shipping a Windows build of `AITown`.

## Expected Paths

- packaged Windows build output: `release/windows`
- packaging script: `scripts/build_windows.ps1`

## Typical Workflow

1. Build the Windows package:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1 -Version 1.0.0 -SteamAppId <APP_ID>
```

2. Edit `steam/app_build_aitown.vdf` and update:

- `appid`
- `desc`
- `setlive`

3. Upload with `steamcmd`:

```bash
steamcmd +login <account> +run_app_build "..\\steam\\app_build_aitown.vdf" +quit
```

## Notes

- `steam_appid.txt` is only for local testing and is not required for a final release package.
- Run `python scripts/release_check.py` before publishing a build.
- The build script uses an isolated Python 3.11 environment to avoid packaging unnecessary local dependencies.
