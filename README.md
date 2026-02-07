![Banner](https://github.com/user-attachments/assets/9a1ad0c8-f90c-4bdf-8ee0-32265c110e75)
[![Tests](https://github.com/DanielBash/NerdFight/actions/workflows/python-tests.yaml/badge.svg)](https://github.com/DanielBash/NerdFight/actions/workflows/python-tests.yaml)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Stars](https://img.shields.io/github/stars/DanielBash/NerdFight)
# Nerd Fight

> Веб-сайт для мазохистов, которым не хватает школьных задач.

Nerd Fight - интернет ресурс для быстрой и интуитивной подготовки к олимпиадным соревнованиям.
Развернут на [этом](https://raw.githubusercontent.com/DanielBash/NerdFight/refs/heads/master/static/images/logo.png) веб-сайте.

## Локальный запуск
### ВАРИАНТ 1: Виртуальное окружение
1) Скачать репозиторий проекта
```bash
git clone https://github.com/DanielBash/NerdFight.git
cd NerdFight
```

2) Установить зависимости
```bash
pip install -r requirements.txt
```

3) Запустить скрипт
```bash
python main.py
```

### ВАРИАНТ 2: Docker-контейнер
1) Скачать контейнер с docker hub:
```bash
docker pull danielbashl/nerdfight:1.0
```

2) Запустить контейнер:
```bash
docker run -d -p 8000:5000 danielbashl/nerdfight:1.0
```
