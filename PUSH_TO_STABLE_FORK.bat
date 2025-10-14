#!/bin/bash
# Script per pujar al fork estable després de crear-lo a GitHub

echo "==============================================="
echo "    PUJANT AL FORK ESTABLE"
echo "==============================================="
echo ""

echo "1. Verificant remot del fork..."
git remote -v | grep stable-fork

echo ""
echo "2. Pujant branca estable al fork..."
git push stable-fork stable-v1.0

echo ""
echo "3. Establint branca per defecte..."
git push stable-fork stable-v1.0:main

echo ""
echo "==============================================="
echo "    FORK ESTABLE ACTUALITZAT!"
echo "==============================================="
echo ""
echo "Ara podeu crear el release a:"
echo "https://github.com/Blanqui04/PythonTecnica-SOME-Stable/releases/new"
echo ""