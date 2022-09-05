import os


class Config:
    data_folder = "./youtrack_export/"
    month_and_year_suffix = "08.2022"
    start_date = 1
    end_date = 31
    work_hours_per_day_requirement = 8
    time_multiplier_mapper = {"ч": 60,
                              "м": 1,
                              "д": work_hours_per_day_requirement * 60}

    project_mapper = {"CB": "6.2 Оценка баланса углерода в природных экосистемах округа",
                      "Other": "Вне проектов",
                      "VDL": "6.2 Оценка и прогнозирование показателей эффективности деятельности ведущих "
                             "должностных лиц",
                      "WC": "Аналитика и разработка математических моделей",
                      "Search": "1.2.3 Совершенствование процессов мониторинга противоправной информации "
                                "в сети Интернет (АИС Поиск)",
                      "SWOYS": "SWOYS",
                      "BI": "Аналитика и разработка математических моделей",
                      "UO": "Ugra Open (МСП)",
                      "Staff": "ИС Кадры",
                      "NLPOGV": "Вне проектов",
                      "ANK": "АНК",
                      "IDD": "Интеграция СЭД Дело и Директум",
                      "investment": "Инвест. проекты"}

    youtrack_access_token = os.environ.get("YOUTRACK_TOKEN")
    youtrack_headers = {"Authorization": f"Bearer {youtrack_access_token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json"}

