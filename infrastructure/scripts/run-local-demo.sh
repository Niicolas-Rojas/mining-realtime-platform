#!/usr/bin/env bash
set -euo pipefail

echo "== Mining Realtime Platform: demo local =="

if [ ! -d ".venv" ]; then
  echo "No existe .venv. Crea el entorno con:"
  echo "python3 -m venv .venv"
  echo "source .venv/bin/activate"
  echo "pip install -r requirements-dev.txt"
  exit 1
fi

echo "1/5 Validando pruebas..."
.venv/bin/python -m pytest

echo "2/5 Construyendo imagenes y levantando servicios..."
docker compose up --build -d

echo "3/5 Esperando a que la API responda..."
for attempt in $(seq 1 30); do
  if curl -fsS http://localhost:8000/health >/dev/null; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "La API no respondio a tiempo."
    docker compose ps
    exit 1
  fi
  sleep 2
done

echo "4/5 Generando capas Silver y Gold..."
.venv/bin/python -m processing.batch.silver_transform
.venv/bin/python -m processing.batch.gold_transform

echo "5/5 Resumen rapido:"
curl -fsS http://localhost:8000/api/v1/pipeline/metrics || true
echo

echo "Demo lista."
echo "API:       http://localhost:8000/health"
echo "Dashboard: http://localhost:8501"
echo
echo "Comandos utiles:"
echo "docker compose logs simulator --tail 30"
echo "docker compose logs ingestion --tail 30"
echo "docker compose down"
