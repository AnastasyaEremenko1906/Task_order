import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, timedelta

#test
#test11

st.set_page_config(page_title="Наряд-задание",
                   page_icon='📚',
                   layout="wide",
                   initial_sidebar_state="expanded"
                   )
st.title("Наряд - задание")
st.text("")


# ______________________________________________________________________________________________________________________
# передача ЗАРАНЕЕ НАПИСАННОГО запроса в БД
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
    except psycopg2.errors.UniqueViolation:
        connection.close()
        st.error('Данное событие уже занесено')
        st.stop()


# формирования SQL-запроса (ДОБАВЛЕНИЕ инфы в БД)
def request_append(start_date, end_date, work_type, person_fio_list, department, destination, district_coef,
                   machine_type, machine_number, any_comment):
    list_of_works = """select id from types_of_work where types_of_work='{}'""".format(work_type)
    id_of_work = pd.read_sql(list_of_works, connection)
    id_of_work = id_of_work.iat[0, 0]
    for selected_name in person_fio_list:
        list_of_fio = """select id_person from fio_person where fio='{}'""".format(selected_name)
        id_of_fio = pd.read_sql(list_of_fio, connection)

        # получаю df из 1 строки и столца; далее извлекаю значение на пересечении строки/столбца для получения № работы
        id_of_fio = id_of_fio.iat[0, 0]

        query = """INSERT INTO task_order (start_dates, end_dates, work_type, person_fio, department,
                destination, district_coef, machine_type,machine_number, any_comment) VALUES """
        query += """('{}','{}','{}','{}','{}','{}','{}', '{}', '{}', '{}'),""".format(start_date, end_date, int(id_of_work),
                                                                                      int(id_of_fio), department,
                                                                                      destination,
                                                                                      district_coef, machine_type,
                                                                                      machine_number, any_comment)
        # connection.close()
        execute_query(connection, query[:-1])
        st.success('Данные успешно сохранены!')


# формирования SQL-запроса (ПОЛУЧЕНИЕ ВСЕЙ инфы в БД)
def make_request():
    select_from_sql = """SELECT * FROM task_order taskor JOIN types_of_work typesw ON taskor.work_type = typesw.id
                                                         JOIN fio_person fio ON taskor.person_fio = fio.id_person"""
    return select_from_sql


# формирования SQL-запроса (ПОЛУЧЕНИЕ инфы по недозаполненным событиям в БД)
def make_request_non_full():
    select_non_full = """SELECT * FROM task_order taskor JOIN types_of_work typesw ON taskor.work_type = typesw.id
                                                         JOIN fio_person fio ON taskor.person_fio = fio.id_person 
    where (department='' or destination='' or machine_type='' or machine_number='');"""
    df_non_full = pd.read_sql(select_non_full, connection)
    df_non_full = df_non_full.loc[:,
                  ['id_event', 'start_dates', 'end_dates', 'types_of_work', 'fio', 'department', 'destination',
                   'district_coef', 'machine_type', 'machine_number', 'any_comment']]
    df_non_full = df_non_full.rename(columns=total_dict)
    table_len = len(df_non_full)
    if table_len == 0:
        status = 'Незавершенных событий нет'
        return [status, ""]
    else:
        status = "Незавершенные события: "
        return [status, df_non_full]


# формирования SQL-запроса (УДАЛЕНИЕ строки по id(номеру события))
def delete_row_sql(event_number):
    delete_in_sql = """DELETE FROM task_order WHERE id_event='{}'""".format(event_number)
    execute_query(connection, delete_in_sql)
    st.success('Данные успешно удалены!')


# формирования SQL-запроса (РЕДАКТИРОВАНИЕ элемента)
def change_value_sql(event_number, select_column, new_value):
    # отдельно запариваюсь с получением индексов по ФИО, видам работ
    if select_column == "ФИО сотрудника":
        select_index = """select id_person from fio_person where fio = '{}'""".format(new_value)
        id_of_fio = pd.read_sql(select_index, connection)
        new_value = id_of_fio.iat[0, 0]
    elif select_column == "Вид работы":
        select_index = """select id from types_of_work where types_of_work = '{}'""".format(new_value)
        id_of_work = pd.read_sql(select_index, connection)
        new_value = id_of_work.iat[0, 0]
    change_value_sql = """UPDATE task_order SET {} = '{}' WHERE id_event = '{}'""".format((dict_streamlit_to_sql
                                                                                           .get(select_column)),
                                                                                          new_value, event_number)
    execute_query(connection, change_value_sql)
    st.success('Данные успешно изменены!')
    st.info('Для просмотра обновленной информации перейдите на главную страницу либо нажмите на кнопку "Перейти к '
            'редактированию"')


# формирования SQL-запроса (ПОЛУЧЕНИЕ списка работ)
def list_of_works():
    list_of_works = """SELECT types_of_work FROM types_of_work"""
    df_works = pd.read_sql(list_of_works, connection)
    return df_works["types_of_work"].tolist()


# формирования SQL-запроса (ПОЛУЧЕНИЕ фио сотрудников)
def list_of_workers():
    list_of_workers = """SELECT DISTINCT fio FROM fio_person ORDER BY fio"""
    df_workers = pd.read_sql(list_of_workers, connection)
    return df_workers['fio'].tolist()


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

# сессия + ВРЕМЕННЫЕ списки + полезные плюшки
if "update_str" not in st.session_state:
    st.session_state.update_str = None
# ___________________________
types_of_work = list_of_works()
fio_list = list_of_workers()
# ___________________________
names_in_sql = ['id_event', 'start_dates', 'end_dates', 'work_type', 'person_fio', 'department', 'destination',
                'district_coef', 'machine_type', 'machine_number', 'any_comment']
names_in_streamlit = ['№ события', 'Дата начала', 'Дата окончания',
                      'Вид работы', 'ФИО сотрудника', 'Пункт оправления',
                      'Пункт назначения', 'Районный коэф-т', 'Вид техники', 'Государственный номер',
                      'Комментарий']
total_dict = {'id_event': '№ события',
              'start_dates': 'Дата начала',
              'end_dates': 'Дата окончания',
              'types_of_work': 'Вид работы',
              'fio': 'ФИО сотрудника',
              'department': 'Пункт оправления',
              'destination': 'Пункт назначения',
              'district_coef': 'Районный коэф-т',
              'machine_type': 'Вид техники',
              'machine_number': 'Государственный номер',
              'any_comment': 'Комментарий'}
dict_streamlit_to_sql = dict(zip(names_in_streamlit, names_in_sql))
dict_sql_to_streamlit = dict(zip(names_in_sql, names_in_streamlit))

# ___________________________
date_today = datetime.today()
date_min = date_today - timedelta(days=30)
date_max = date_today + timedelta(days=30)


# считываю df, редактирую названия столбцов
def my_df():
    df = pd.read_sql(make_request(), connection)
    df = df.loc[:, ['id_event', 'start_dates', 'end_dates', 'types_of_work', 'fio', 'department', 'destination',
                    'district_coef', 'machine_type', 'machine_number', 'any_comment']]
    df = df.rename(columns=total_dict)
    table_len = len(df)
    if table_len == 0:
        status = 'Наряд - задание не содержит событий. Для заполнения выберите пункт "Добавить"'
        return [status, df]
    else:
        status = "Все события: "
        return [status, df]


# ______________________________________________________________________________________________________________________
# МЕНЮ РЕДАКТИРОВАНИЯ событий
def change_data():
    my_table = my_df()[1]
    if my_table.empty:
        st.text("В настоящий момент нет доступных для редактирования событий")
    else:
        values_selection = st.selectbox('Отсортируйте таблицу по искомому типу работ: ',
                                        my_table.iloc[:, 3].unique().tolist())
        selected_rows = my_table[my_table.iloc[:, 3] == values_selection]
        st.markdown("<hr />", unsafe_allow_html=True)
        st.write("**По вашему запросу найдены события: **")
        st.write(selected_rows)
        st.markdown("<hr />", unsafe_allow_html=True)
        index_selection = selected_rows.iloc[:, 0]
        coll1, coll2 = st.columns(2)
        coll1.write("**Выберите № события для редактирования: **")
        event_number = coll1.selectbox('', index_selection.tolist())
        coll1.markdown("<hr />", unsafe_allow_html=True)
        st.write("**Для редактирования выбрано событие: **")
        st.table(my_table[my_table["№ события"] == int(event_number)])
        if st.button("Перейти к редактированию {}-ого события".format(event_number)):
            st.session_state.update_str = "Start_edit"
        if st.session_state.update_str == "Start_edit":
            st.markdown("<hr />", unsafe_allow_html=True)
            st.title("Заполните поля ниже:")
            st.text("")
            select_column = st.selectbox('Выберите столбец, значение которого нужно изменить: ', my_table.columns[1:])
            st.text("")
            st.write("Введите/выберите новое значение в ячейке ниже: ")
            if select_column == my_table.columns[1] or select_column == my_table.columns[2]:
                new_value = st.date_input("", value=None, min_value=date_min, max_value=date_max, key=3)
            elif select_column == my_table.columns[3]:
                new_value = st.selectbox("", list_of_works())
            elif select_column == my_table.columns[4]:
                new_value = st.selectbox("", fio_list)
            else:
                new_value = st.text_input("")
            st.text("")
            if st.button("Внести изменения"):
                change_value_sql(event_number, select_column, new_value)

                st.session_state.update_str = "End_edit"


# МЕНЮ ДОБАВЛЕНИЯ событий
def append_data():
    start_date = st.date_input("Дата старта :", value=None, min_value=date_min, max_value=date_max, key=1)
    end_date = st.date_input("Дата окончания :", value=None, min_value=date_min, max_value=date_max, key=2)
    work_type = st.selectbox('Выберите вид работы:', types_of_work)

    st.markdown("<hr />", unsafe_allow_html=True)

    person_fio_list = st.multiselect('Выберите сотрудника: ', fio_list)
    department = st.text_input('Введите пункт оправления')
    destination = st.text_input('Введите пункт назначения')

    st.markdown("<hr />", unsafe_allow_html=True)

    district_coef = st.text_input("Введите коэф-т")
    machine_type = st.text_input("Введите тип авто")
    machine_number = st.text_input("Введите номер авто")

    st.markdown("<hr />", unsafe_allow_html=True)
    any_comment = st.text_input("Введите комментарий к событию (если это необходимо)")
    col1, col2, col3, col4 = st.columns(4)
    button = col1.button("Добавить информацию")
    if button and len(person_fio_list) == 0:
        st.error('Для добавления введенной информации укажите ФИО сотрудника')
    elif button:
        try:
            my_table = my_df()
            request_append(start_date, end_date, work_type, person_fio_list, department, destination,
                           district_coef,
                           machine_type, machine_number, any_comment)
        except psycopg2.errors.UniqueViolation:
            st.error("Такое событие уже есть в базе")


# МЕНЮ УДАЛЕНИЯ событий в df
def delete_data():
    my_table = my_df()[1]
    if my_table.empty:
        st.text("В настоящий момент нет доступных для удаления событий")
    else:
        st.text("")
        st.text("Отсортируйте таблицу по искомому типу работ:")
        values_selection = st.selectbox('', my_table.iloc[:, 3].unique().tolist())
        selected_rows = my_table[my_table.iloc[:, 3] == values_selection]
        st.markdown("<hr />", unsafe_allow_html=True)
        st.text("По вашему запросу найдены события: ")
        st.write(selected_rows)
        st.markdown("<hr />", unsafe_allow_html=True)
        index_selection = selected_rows.iloc[:, 0]
        st.text('Выберите № события для удаления: ')
        event_number = st.selectbox("", index_selection.tolist())
        col1, col2, col3 = st.columns(3)
        button = col1.button("Удалить выбранное событие")
        if button:
            my_table = my_df()
            delete_row_sql(event_number)


# СОЗДАНИЕ МЕНЮ работы с наряд-заданием
option_menu = ["Главная страница", "Редактировать", "Удалить", "Добавить"]
st.sidebar.title("Меню работы с наряд - заданием: ")
main_menu = st.sidebar.selectbox("", option_menu)
if main_menu == option_menu[0]:
    if my_df()[0] == "Все события: ":
        st.write(make_request_non_full()[0])
        st.write(make_request_non_full()[1])
        st.markdown("<hr />", unsafe_allow_html=True)
        st.write("**Выберите интересущий фильтр:**")
        choice_filter = st.radio("", ['Показать все события', 'Показать определенные события'])
        if choice_filter == "Показать все события":
            st.write(my_df()[0])
            st.write(my_df()[1])
        elif choice_filter == "Показать определенные события":
            st.write("Отфильтруйте события:")
            col1, col2, col3, col4 = st.columns(4)
            form_filter = st.form('Параметры фильтра')
            cond_1 = col1.checkbox("По дате старта")
            cond_2 = col2.checkbox("По дате финиша")
            cond_3 = col3.checkbox("По ФИО")
            cond_4 = col4.checkbox("По виду работ")
            with form_filter:
                col_form_filter_1, col_form_filter_2 = st.columns(2)
                if cond_1:
                    start_date = col_form_filter_1.date_input("Выберите дату старта :", value=None, min_value=date_min,
                                                              max_value=date_max,
                                                              key=4)
                else:
                    start_date = False
                if cond_2:
                    end_date = col_form_filter_1.date_input("Выберите дату окончания :", value=None, min_value=date_min,
                                                            max_value=date_max,
                                                            key=4)
                else:
                    end_date = False
                if cond_3:
                    person_fio_list = col_form_filter_1.selectbox('Выберите сотрудника: ', fio_list)
                else:
                    person_fio_list = False
                if cond_4:
                    work_type = col_form_filter_1.selectbox('Выберите вид работы:', types_of_work)
                else:
                    work_type = False
                apply_filter = st.form_submit_button('Применить фильтр(ы)')
                if apply_filter:
                    filtered_df = my_df()[1]
                    if start_date:
                        filtered_df = filtered_df.loc[filtered_df['Дата начала'] == start_date]
                    if end_date:
                        filtered_df = filtered_df.loc[filtered_df['Дата окончания'] == end_date]
                    if person_fio_list:
                        filtered_df = filtered_df.loc[filtered_df['ФИО сотрудника'] == person_fio_list]
                    if work_type:
                        filtered_df = filtered_df.loc[filtered_df['Вид работы'] == work_type]
                    if len(filtered_df) == 0:
                        st.warning("По выставленным фильтрам события не найдены")
                    else:
                        st.write(filtered_df)
    else:
        st.write(my_df()[0])
        st.markdown("<hr />", unsafe_allow_html=True)
        st.write(make_request_non_full()[0])
        st.write(make_request_non_full()[1])
elif main_menu == option_menu[1]:
    change_data()
elif main_menu == option_menu[2]:
    delete_data()
elif main_menu == option_menu[3]:
    append_data()

connection.close()
