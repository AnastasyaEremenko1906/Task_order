import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

st.title("Наряд - задание")


# передача запроса в БД
def execute_query(connection, query):
    connection.rollback()
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except psycopg2.OperationalError as e:
        connection.close()
        st.error(f"The error '{e}' occurred")


# формирования SQL-запроса для добавления инфы в БД
def request_append(id_event, start_date, end_date, work_type, person_fio_list, department, destination, district_coef,
                   machine_type, machine_number):
    query = """INSERT INTO task_order (id_event, start_dates, end_dates, work_type, "person_FIO", department,
            destination, district_coef, machine_type,machine_number) VALUES """
    for id, person in enumerate(person_fio_list):
        query += """
        ((SELECT MAX(id_event) + {} FROM task_order),'{}','{}','{}','{}','{}','{}','{}', '{}', '{}'),""".format(
            id + 1, start_date, end_date, work_type,
            str(person), department, destination, district_coef, machine_type, machine_number)
    # connection.close()
    execute_query(connection, query[:-1])
    st.success('Данные успешно сохранены!')


# формирования SQL-запроса для получения всей инфы
def make_request():
    select_from_sql = """SELECT * FROM task_order"""
    return select_from_sql


# формирования SQL-запроса для получения инфы по незаполненным строкам
def make_request_non_full():
    select_non_full = """select * from task_order where (department='' or 'person_FIO'='' or destination='' or 
    district_coef='' or machine_type='' or machine_number=''); """
    df_non_full = pd.read_sql(select_non_full, connection)
    df_non_full = df_non_full.rename(columns={'id_event': 'Номер события',
                                            'start_dates': 'Дата, время начала работы/события',
                                            'end_dates': 'Дата, время окончания работы/события',
                                            'work_type': 'Вид выполняемой работы, задания/события',
                                            'person_FIO': 'ФИО сотрудник(а/ов)',
                                            'department': 'Пункт оправления',
                                            'destination': 'Пункт назначения',
                                            'district_coef': 'Применяемый районный коэф-т',
                                            'machine_type': 'Вид техники',
                                            'machine_number': 'Государственный номер'})

    return df_non_full


# формирования SQL-запроса для удаления инфы
def delete_row_sql(event_number):
    delete_in_sql = """DELETE FROM task_order WHERE id_event='{}'""".format(event_number)
    execute_query(connection, delete_in_sql)
    st.success('Данные успешно удалены!')


# подключение к БД
def create_connection(db_name, db_user, db_password, db_host, db_port):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        # print("Connection to PostgreSQL DB successful")
    except psycopg2.OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


connection = create_connection(
    "production", "postgres", "admin228", "192.168.10.12", "5432"
)

# ВРЕМЕННЫЕ списки + полезные плюшки
types_of_work = ["Убытие к месту проведения ТО", "Сдача анализов на ковид", "Проведение ТО", "Получение техники",
                 "Прием техники"]
fio_list = ["Петров", "Иванов", "Сидоров"]
date_today = datetime.today()
date_min = date_today - timedelta(days=30)
date_max = date_today + timedelta(days=30)


# считываю df, редактирую названия столбцов
def my_df():
    df = pd.read_sql(make_request(), connection)
    df = df.rename(columns={'id_event': 'Номер события',
                            'start_dates': 'Дата, время начала работы/события',
                            'end_dates': 'Дата, время окончания работы/события',
                            'work_type': 'Вид выполняемой работы, задания/события',
                            'person_FIO': 'ФИО сотрудник(а/ов)',
                            'department': 'Пункт оправления',
                            'destination': 'Пункт назначения',
                            'district_coef': 'Применяемый районный коэф-т',
                            'machine_type': 'Вид техники',
                            'machine_number': 'Государственный номер'})
    return df


# МЕНЮ РЕДАКТИРОВАНИЕ событий
def change_data():
    st.markdown("<hr />", unsafe_allow_html=True)
    my_table = my_df()
    values_selection = st.selectbox('Отсортируйте таблицу по нужному типу работ:',
                                    my_table.iloc[:, 3].unique().tolist())
    selected_rows = my_table[my_table.iloc[:, 3] == values_selection]
    st.write("По вашему запросу найдены события: ")
    st.write(selected_rows)
    st.markdown("<hr />", unsafe_allow_html=True)
    index_selection = selected_rows.iloc[:, 0]
    event_number = st.selectbox('Выберите номер события для редактирования: ', index_selection.tolist())
    st.button("Внести изменения")


# МЕНЮ ДОБАВЛЕНИЯ событий
def append_data():
    start_date = st.date_input("Дата старта :", value=None, min_value=date_min, max_value=date_max, key=1)
    end_date = st.date_input("Дата окончания :", value=None, min_value=date_min, max_value=date_max, key=2)
    work_type = st.selectbox('Выберите вид работы:', types_of_work)
    st.markdown("<hr />", unsafe_allow_html=True)
    person_fio_list = st.multiselect('Выберите сотрудник(а/ов): ', fio_list)
    department = st.text_input('Введите пункт оправления')
    destination = st.text_input('Введите пункт назначения')
    st.markdown("<hr />", unsafe_allow_html=True)
    district_coef = st.text_input("Введите коэф-т")
    machine_type = st.text_input("Введите тип авто")
    machine_number = st.text_input("Введите номер авто")
    button = st.button("Добавить информацию")
    if button:
        my_table = my_df()
        id_event = len(my_table) + 1
        request_append(id_event, start_date, end_date, work_type, person_fio_list, department, destination,
                       district_coef,
                       machine_type, machine_number)


# МЕНЮ УДАЛЕНИЯ событий в df
def delete_data():
    st.markdown("<hr />", unsafe_allow_html=True)
    my_table = my_df()
    values_selection = st.selectbox('Отсортируйте таблицу по нужному типу работ:',
                                    my_table.iloc[:, 3].unique().tolist())
    selected_rows = my_table[my_table.iloc[:, 3] == values_selection]
    st.write("По вашему запросу найдены события: ")
    st.write(selected_rows)
    st.markdown("<hr />", unsafe_allow_html=True)
    index_selection = selected_rows.iloc[:, 0]
    event_number = st.selectbox('Выберите номер события для удаления: ', index_selection.tolist())
    button = st.button("Удалить выбранное событие")
    if button:
        my_table = my_df()
        delete_row_sql(event_number)


# СОЗДАНИЕ МЕНЮ работы с наряд-заданием
option_menu = ["Главная страница", "Редактировать", "Добавить", "Удалить"]
st.sidebar.title("Меню работы с наряд - заданием: ")
main_menu = st.sidebar.selectbox("", option_menu)
if main_menu == option_menu[1]:
    change_data()
elif main_menu == option_menu[2]:
    append_data()
elif main_menu == option_menu[3]:
    delete_data()
else:
    st.write("Все события: ")
    st.write(my_df())
    st.markdown("<hr />", unsafe_allow_html=True)
    st.write("Незавершенные события: ")
    st.write(make_request_non_full())

connection.close()
