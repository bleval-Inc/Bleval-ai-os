# Executive agent launchers

Run Jenson as the executive coordinator with:

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\run_jenson.ps1
```

Run ValtaPrime as the House of Valta executive coordinator with:

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\run_valtaprime.ps1
```

Run Yamako as the founder's chief of staff with:

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\run_yamako.ps1
```

You can also pass a custom task to any launcher:

```powershell
powershell -ExecutionPolicy Bypass -File .\Tools\run_jenson.ps1 -Task "Review the project roadmap and produce an executive summary"
```
