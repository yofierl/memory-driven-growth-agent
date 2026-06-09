$ErrorActionPreference = "Stop"

$directories = @(
  "app",
  "app/api",
  "app/agent",
  "app/agent/nodes",
  "app/agent/prompts",
  "app/core",
  "app/models",
  "app/repositories",
  "app/schemas",
  "app/services",
  "tests",
  "tests/test_api",
  "tests/test_nodes",
  "tests/test_services",
  "frontend/src",
  "frontend/src/components",
  "frontend/src/hooks",
  "frontend/src/pages",
  "frontend/src/services"
)

foreach ($directory in $directories) {
  New-Item -ItemType Directory -Force -Path $directory | Out-Null
}

$pythonPackages = @(
  "app",
  "app/api",
  "app/agent",
  "app/agent/nodes",
  "app/core",
  "app/models",
  "app/repositories",
  "app/schemas",
  "app/services"
)

foreach ($package in $pythonPackages) {
  $initPath = Join-Path $package "__init__.py"
  if (-not (Test-Path $initPath)) {
    Set-Content -Path $initPath -Value '"""Package marker for Memory-Driven Growth Agent."""' -Encoding utf8
  }
}

$mainPath = "app/main.py"
if (-not (Test-Path $mainPath)) {
  @'
from fastapi import FastAPI

app = FastAPI(title="Memory-Driven Growth Agent")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
'@ | Set-Content -Path $mainPath -Encoding utf8
}

Write-Host "Project skeleton initialized."
