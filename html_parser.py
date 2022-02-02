from typing import List, Dict
from bs4 import BeautifulSoup
from Config import Config
import pandas as pd
import requests


def get_soup_from_file(filepath) -> BeautifulSoup:
    with open(filepath, "r", encoding="UTF-8") as file:
        raw_html = file.read()

    return BeautifulSoup(raw_html, "html.parser")


def get_table_from_soup(soup: BeautifulSoup) -> BeautifulSoup:
    table_selector = "body > div.app.errorPage_796 > div > div > div > div > div > div > div > div > div > div > " \
                     "div:nth-child(2) > div > div > div:nth-child(4) > div "
    return soup.select_one(table_selector)


def get_days_from_table(table: BeautifulSoup) -> List[BeautifulSoup]:
    return table.find_all("div", {"class": "monthDay__ad9"})


def get_date_from_day(day: BeautifulSoup):
    return int(day.find("p", {"class": "monthDayDate__411"}).text)


def parse_work_time_from_string(work_time: str) -> int:
    tokens = work_time.split()
    total_minutes = 0
    for token in tokens:
        time_value = int(token[:-1])
        time_multiplier = token[-1]
        total_minutes += time_value * Config.time_multiplier_mapper[time_multiplier]
    return total_minutes


def parse_task(task: BeautifulSoup) -> Dict:
    """

    :param task:
    :type task:
    :return: Словарь, где ключ - название задачи, а значение - трудозатраты в МИНУТАХ
    :rtype:
    """
    task = task.find("div")

    elapsed_time = task.find("p").text

    text_area = task.find("a").find("span").find("div").find("span")
    task_name = text_area.text
    return {task_name: parse_work_time_from_string(elapsed_time)}


def tasks_data_normalization(tasks_data: List[Dict]):
    normalized_tasks_data = {}
    for task_data in tasks_data:
        key = next(iter(task_data))
        value = task_data[key]
        if key in normalized_tasks_data.keys():
            normalized_tasks_data[key] += value
        else:
            normalized_tasks_data[key] = value
    return normalized_tasks_data


def parse_day(day: BeautifulSoup):
    tasks = day.find_all("div", {"class": "workItemCard__14a"})
    raw_tasks_data = [parse_task(task) for task in tasks]
    return tasks_data_normalization(raw_tasks_data)


def get_task_full_name(task_name):
    full_task_name = requests.get(f"https://utrack.uriit.ru/api/issues/{task_name}?fields=summary",
                                  headers=Config.youtrack_headers).json()["summary"]
    return full_task_name


def work_time_balancer(day_tasks: Dict):
    task_count = len(day_tasks.values())
    time_spent = sum(day_tasks.values())
    day_time_standard_in_minutes = Config.work_hours_per_day_requirement * 60

    if time_spent == 0 or time_spent == day_time_standard_in_minutes:
        return day_tasks

    time_difference = day_time_standard_in_minutes - time_spent
    additional_time_per_task = time_difference / task_count

    for key in day_tasks.keys():
        day_tasks[key] += additional_time_per_task

    return day_tasks


def parse_days(days: List[BeautifulSoup]):
    frame = pd.DataFrame(columns=["ФИО", "Проект", "Выполненная задача", "Значение показателя", "Трудозатраты", "Дата"])
    started = False
    for day in days:
        day_date = get_date_from_day(day)

        if day_date != Config.start_date and not started:
            continue
        else:
            started = True

        day_data = parse_day(day)
        balanced_day_data = work_time_balancer(day_data)
        for task_name, task_time in balanced_day_data.items():
            frame = frame.append({"ФИО": Config.person_name,
                                  "Проект": Config.project_mapper[task_name.split("-")[0]],
                                  "Выполненная задача": get_task_full_name(task_name),
                                  "Значение показателя": None,
                                  "Трудозатраты": task_time / 60,
                                  "Дата": f"{day_date}.{Config.month_and_year_suffix}"},
                                 ignore_index=True)

        if day_date == Config.end_date and started:
            break
    return frame


if __name__ == '__main__':
    html_tree = get_soup_from_file(Config.filename)
    table = get_table_from_soup(html_tree)
    days = get_days_from_table(table)
    result_frame = parse_days(days)
    result_frame.to_excel(f"./results/{Config.person_name}.xlsx", index=False)
