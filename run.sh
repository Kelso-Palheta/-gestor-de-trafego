#!/bin/bash

# Acessa a pasta raiz do projeto onde está o .env e o main.py
cd /Users/kelsopalheta/Developer/gestor-de-trafego

# Ativa o ambiente virtual do Python isolado
source venv/bin/activate

# Executa o Cérebro do Gestor de Tráfego e salva o histórico no arquivo gestor.log
python main.py >> automacao.log 2>&1
