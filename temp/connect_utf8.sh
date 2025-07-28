#!/bin/bash
echo "Connectant a PostgreSQL amb encoding UTF8..."
export PGCLIENTENCODING=UTF8
psql -h 172.26.5.159 -p 5433 -d documentacio_tecnica -U administrador --client-encoding=UTF8
