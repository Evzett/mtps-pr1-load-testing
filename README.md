# Практическая работа №1. Тестирование производительности

Объект тестирования — **JSONPlaceholder** (https://jsonplaceholder.typicode.com), публичный fake REST API
из списка [public-apis](https://github.com/public-apis/public-apis) (раздел Test Data).
6 ресурсов (`posts`, `comments`, `albums`, `photos`, `todos`, `users`), методы GET/POST/PUT/PATCH/DELETE.

Инструменты: Postman/Newman (функциональные тест-кейсы), Artillery 2 (нагрузочное тестирование), Python + matplotlib (анализ).

## Структура

```
postman/gen_collection.py                         генератор коллекции (18 тест-кейсов TC-01…TC-18)
postman/JSONPlaceholder.postman_collection.json   коллекция Postman (импорт в Postman или запуск в Newman)
postman/test_cases.csv                            таблица тест-кейсов
artillery/scenarios.yml                           сценарии нагрузки S1–S5 и критерии успешности (SLA)
artillery/profiles/p0_smoke.yml                   smoke-проверка (10 с)
artillery/profiles/p1_smooth.yml                  П1 «Плавный»: нарастание 2 мин, плато 2 мин, спад 2 мин
artillery/profiles/p2_fast.yml                    П2 «Быстрый»: нарастание 30 с, плато 60 с, спад 30 с
artillery/profiles/p3_spike.yml                   П3 «Пиковый»: всплеск за 10 с до ~32 RPS
artillery/profiles/p4_steps.yml                   П4 «Ступенчатый»: 2→4→6→8→4→2 ВП/с по 45 с
analyze.py                                        сводные метрики и графики
results/                                          результаты прогонов (JSON, отчёты, графики)
```

## Запуск

```bash
npm install

# функциональные тест-кейсы (Newman = CLI Postman)
npx newman run postman/JSONPlaceholder.postman_collection.json -r cli,htmlextra \
    --reporter-htmlextra-export results/newman_report.html

# нагрузочное тестирование: профиль задаётся через --config
npx artillery run --config artillery/profiles/p1_smooth.yml --output results/p1_smooth.json artillery/scenarios.yml
npx artillery run --config artillery/profiles/p2_fast.yml   --output results/p2_fast.json   artillery/scenarios.yml
npx artillery run --config artillery/profiles/p3_spike.yml  --output results/p3_spike.json  artillery/scenarios.yml
npx artillery run --config artillery/profiles/p4_steps.yml  --output results/p4_steps.json  artillery/scenarios.yml

# анализ и графики
pip install matplotlib
python analyze.py
```

> Если в сети не работает IPv6, Node.js может зависать на подключении. Помогает
> `NODE_OPTIONS="--dns-result-order=ipv4first --no-network-family-autoselection"`.

Критерии успешности (задаются в `artillery/scenarios.yml`, плагин `ensure`):
95-й процентиль времени ответа < 1500 мс, доля ошибок < 1 %.
