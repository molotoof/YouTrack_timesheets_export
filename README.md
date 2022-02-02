Данный скрипт предназначен для формирования ежемесячного отчета по сотруднику.

Функционал:
1. Парсит html странницы https://utrack.uriit.ru/timesheets?date=2022-01-31&mode=month&author=d08b900d-2abb-44f6-9774-7b1bcea3bc8b&projects=&q=&types=
2. Извлекает название задач, потраченного времени и проектов.
3. "Довирает" недостающие часы (раввномерно накидывает недостающие часы на задачи дня)
4. Формирует xlsx по форме отчета.

Как пользоваться:
1. Настроить Config.py
2. Получить токен доступа к API и внести его в .env
3. Получить полностью отрендеренный html аналогичной страницы https://utrack.uriit.ru/timesheets?date=2022-01-31&mode=month&author=d08b900d-2abb-44f6-9774-7b1bcea3bc8b&projects=&q=&types=
4. Запустить скрипт
5. ???
6. Profit! Скопировать информацию из эксельки и вставить в директум.

TODO:
1. Не собирать html ручками, а парсить через selenium
2. Проходиться по списку сотрудников и получать цельную эксельку на выходе