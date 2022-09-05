import os
import time
from typing import List, Dict
from bs4 import BeautifulSoup
from Config import Config
import pandas as pd
import requests
from pathlib import Path


def get_soup_from_file(filepath) -> BeautifulSoup:
    with open(filepath, "r", encoding="UTF-8") as file:
        raw_html = file.read()

    return BeautifulSoup(raw_html, "html.parser")


def get_table_from_soup(soup: BeautifulSoup) -> BeautifulSoup:
    table_selector = "body > div.app > div > div > div > div > div > div > div > div > div > div > " \
                     "div:nth-child(2) > div > div > div:nth-child(4) > div "
    return soup.select_one(table_selector)


def get_days_from_table(table: BeautifulSoup) -> List[BeautifulSoup]:
    return table.find_all("div", {"class": "monthDay__a8a"})


def get_date_from_day(day: BeautifulSoup):
    return int(day.find("p", {"class": "monthDayDate__d04"}).text)


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

    # task = task.find("div")
    elapsed_time = task.find("p").text
    text_area = task.find("div").find("a").find("span").find("div").find("span")
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
    tasks = day.find_all("div", {"class": "workItemCard__e5b"})
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


def stack_low_time_tasks(rows):
    good_rows = []
    bad_rows = []
    for key, row in rows.items():
        if row["Трудозатраты"] < 0.2:
            row["Выполненная задача"] = "Прочие"
            rows[key] = row
            bad_rows.append(row)
        else:
            good_rows.append(row)

    projects_names = set(bad_row["Проект"] for bad_row in bad_rows)

    for project_name in projects_names:
        project_row = {}
        for bad_row in bad_rows:
            if bad_row["Проект"] == project_name and not project_row:
                project_row = bad_row
            elif bad_row["Проект"] == project_name:
                project_row["Трудозатраты"] += bad_row["Трудозатраты"]
                project_row["Дата"] = bad_row["Дата"]

        if project_row["Трудозатраты"] >= 0.2:
            good_rows.append(project_row)

    return good_rows


def parse_days(days: List[BeautifulSoup], person_name):
    frame = pd.DataFrame(columns=["ФИО", "Проект", "Выполненная задача", "Значение показателя", "Трудозатраты", "Дата"])
    started = False
    rows = {}
    for day in days:
        day_date = get_date_from_day(day)

        if day_date != Config.start_date and not started:
            continue
        else:
            started = True

        day_data = parse_day(day)
        # balanced_day_data = work_time_balancer(day_data)

        for task_name, task_time in day_data.items():
            full_task_name = get_task_full_name(task_name)
            row = {"ФИО": person_name,
                   "Проект": Config.project_mapper[task_name.split("-")[0]],
                   "Выполненная задача": full_task_name,
                   "Значение показателя": None,
                   "Трудозатраты": task_time / (60 * Config.work_hours_per_day_requirement),
                   "Дата": f"{day_date if day_date >= 10 else '0' + str(day_date)}.{Config.month_and_year_suffix}"}

            if full_task_name not in rows.keys():
                rows[full_task_name] = row
            else:
                rows[full_task_name]["Трудозатраты"] += row["Трудозатраты"]
                rows[full_task_name]["Дата"] = row["Дата"]

        if day_date == Config.end_date and started:
            rows = stack_low_time_tasks(rows)
            for row in rows:
                frame = frame.append(row, ignore_index=True)
            break
    return frame


if __name__ == '__main__':
    global_frame = None
    first = True
    for filename in os.listdir(Config.data_folder):
        print(filename)
        if Path(filename).suffix == '.html':
            person_name = filename.split(".")[0]
            file_path = Config.data_folder + filename
            print(person_name)
            html_tree = get_soup_from_file(file_path)
            table = get_table_from_soup(html_tree)
            days = get_days_from_table(table)
            personal_frame = parse_days(days, person_name).sort_values(by="Дата")
            personal_frame.to_excel(f"./results/{person_name}.xlsx", index=False)
            if first:
                global_frame = personal_frame
                first = False
            else:
                global_frame = global_frame.append(personal_frame, ignore_index=True)

    global_frame.to_excel(f"./results/total_report.xlsx", index=False)