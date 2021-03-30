from flask import Flask, redirect, request
import pandas as pd
# import numpy as np
import random
import math

app = Flask(__name__)


def list_to_rowspanhtml(olymp_list):
    ''' Turns 2d list e.g. [(1,2,3),(4,5,6),(7,8,9),(10,11,12)]
        into html table with rowspan for OlympGame
        1
        4  2  3
        7  8
        10
    '''
    # olymp_list = [(1,2,3),(4,5,6),(7,8,9),(10,11,12)]
    htmltable = '''<table border = 1> 
    <tbody>'''
    for i, row in enumerate(olymp_list):
        htmltable += '''
        <tr>
        '''
        for j, element in enumerate(row):
            # Column = j = row.index(element)
            # Row = i = olymp_list.index(row)
            if j > 0 and i == 0:
                # Колонка больше 1-й и первая строка - надо объединять по вертикали
                htmltable += f'<td rowspan={int(2**j)}>{element}</td>'
            elif j > 0 and i % int(2**j) == 0:
                # Колонка больше 1-й и строки для элементов частичного объединения по вертикали
                htmltable += f'<td rowspan={int(2**j)}>{element}</td>'
            elif j == 0:
                # Первая колонка - выводим все
                htmltable += f'<td>{element}</td>'
        htmltable += '''
        </tr>'''
    htmltable += '''
    </tbody>
</table>'''
    return htmltable


def olymp_auto(inputword: str, **kwargs):
    """ Возвращает желаемое число ассоциаций по sociation.org.tsv
        Одно слово превращаем в 2 или больше через ассоциации.
    Args:
      inputword: str - исходное слово
    Kwargs:
      difficulty: str - сложность ассоциаций
         'easy' - 4 первых (по умолчанию) или 'hard'- весь список
      quantity: int - количество слов на выдачу
         2 - по умолчанию
      exclude: list of str
         список слов на исключение
    Returns:
      List of strings
    """
    # Lets define default keyword arguments and assign to variables
    if not ("difficulty" in kwargs):
        difficulty = 'easy'
    else:
        difficulty = kwargs['difficulty']
    if not ("quantity" in kwargs):
        quantity = 2
    else:
        quantity = kwargs['quantity']
    if not ("exclude" in kwargs):
        exclude = []
    else:
        exclude = kwargs['exclude']

    aa = Sociation.loc[Sociation[0] == inputword][1]
    bb = Sociation.loc[Sociation[1] == inputword][0]

    # почистим похожие на исходное слова
    aa = aa.drop(aa[aa.str.contains(inputword[:3])].index)
    bb = bb.drop(bb[bb.str.contains(inputword[:3])].index)

    # Уберем слова, которые даны в списке исключений
    # ~ - инвертируем булины
    aa = aa[~aa.isin(exclude)]
    bb = bb[~bb.isin(exclude)]

    # Составляем список с учетом сложности
    if difficulty == 'easy':
        # только существительные
        aa = aa[aa.isin(Nouns[0])]
        bb = bb[bb.isin(Nouns[0])]
        # по 4 слова из кажого списка
        words = aa[0:4].append(bb[0:4])
        words = words.drop_duplicates()
    else:
        words = aa.append(bb)
        words = words.drop_duplicates()

    # Выбираем случайные слова из списка
    if len(words) > 2:
        words = random.sample(list(words), quantity)
    elif len(words) > 0:
        words = list(words)
    else:
        words = 'Error_404'

    return words


def olymp_gen(olymp_steps, starting_word = 'random'):
    """ Генератор олимпиек
        Превращает одно слово (или случайное) в цепочку ассоциаций
        в виде олимпийки.
    Args:
      olymp_steps: int - к-во ступеней: (1) - слово + 2 ассоциации, (2) - слово + 2 ассоциации + 4 ассоциации и т.п.
    Kwargs:
      starting_word: str - начальное слово, случайное по умолчанию
    Returns:
      List of strings
    """
    if starting_word == 'random':
        starting_word = Sociation.sample().values[0][0]
    # print(starting_word)

    olymp_list = [starting_word]
    i = 0
    while i <= (2**olymp_steps - 2):  # 2**3 - 2 = 6 - получаем пару ассоциаций для 6 слов
        # extend not append - because [1,2].append([3,4]) = [1,2,[3,4]]
        # [1,2].extend([3,4]) = [1,2,3,4]
        new_pair = olymp_auto(starting_word, quantity=2, exclude=olymp_list)
        if new_pair == 'Error_404':
            new_pair = (starting_word, 'Error_404')
            break
        olymp_list.extend(new_pair)
        i += 1
        starting_word = olymp_list[i]

    return olymp_list


def reset_olymp():
    global game_olymp
    global olymp_matrix
    global display_olymp

    rows, cols = (int(2 ** olymp_steps), (olymp_steps + 1))

    game_olymp = olymp_gen(olymp_steps, starting_word='random')

    olymp_matrix = [[' ' for i in range(cols)] for j in range(rows)]
    # Превращаем строку в 2д матрицу
    i = 0
    j = 0
    for word in game_olymp:
        nomer = game_olymp.index(word) + 1
        for x in range(int(rows / 2 ** int(math.log2(nomer)))):
            olymp_matrix[i][j] = word
            i += 1
        if i > rows - 1:
            i = 0
            j += 1

    # Инвертируем матрицу
    for i in range(rows):
        olymp_matrix[i] = olymp_matrix[i][::-1]

    display_olymp = [[' ' for i in range(cols)] for j in range(rows)]

    for i in range(rows):
        display_olymp[i][0] = olymp_matrix[i][0]
        if olymp_matrix[i][0].strip() == '':
            reset_olymp()
    return

@app.route('/', methods=['POST', 'GET'])
def olymp_index():
    global olymp_message
    global game_olymp
    global olymp_matrix
    global display_olymp
    global olymp_steps

    global Nouns
    global Sociation

    Nouns = pd.read_csv("static/russian_nouns.csv", header=None)
    Sociation = pd.read_csv("static/sociation.org.tsv", header=None, sep='\t')

    olymp_steps = 4
    rows, cols = (int(2**olymp_steps), (olymp_steps + 1))
    game_olymp = [' ']
    olymp_matrix = [[' ' for i in range(cols)] for j in range(rows)]
    display_olymp = [[' ' for i in range(cols)] for j in range(rows)]

    reset_olymp()
    olymp_message = '<p>Приветствую Вас!</p>'
    return redirect('/olymp')

@app.route('/olymp', methods=['POST', 'GET'])
def olymp_start():
    global olymp_message
    global game_olymp
    global olymp_matrix
    global display_olymp
    global olymp_steps

    rows, cols = (int(2 ** olymp_steps), (olymp_steps + 1))

    input_form = '''
      <form action = "/olymp" method = "post">
         <p>Введите слово:
            <input type = "text" name = "nm" autofocus />
            <input type = "submit" name = "submit" value = "отправить" />
            <input type = "submit" name = "help" value = "подсказки" />            
            <input type = "submit" name = "exit" value = "ответы" />
            <input type = "submit" name = "reset" value = "сброс" /></p>
      </form>'''

    page_head = '''<!doctype html>
    <html lang="ru">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Олимпийка</title>
        
        <link rel="stylesheet" href="static/bootstrap.css">
        <link rel="stylesheet" href="static/olymp2.css">
        
        <style>

        </style>
    </head>
    <body>
    <h1>Олимпийка</h1>
    
    <main>
    '''
# <link rel="stylesheet" href="{url_for('static', filename='olymp.css')}">
# <link rel="stylesheet" href="https://cryptex.games/online/045/go/stat2/stat2.css">

    if request.method == 'POST':
        if 'submit' in request.form:
            otvet = request.form['nm']
            otvet = otvet.lower()
        elif 'help' in request.form:
            otvet = 'help'
        elif 'reset' in request.form:
            otvet = 'reset'
        elif 'exit' in request.form:
            otvet = 'exit'
        else:
            otvet = ''


        if otvet in game_olymp:

            for i in range(rows):
                for j in range(1, cols):
                    if olymp_matrix[i][j] == otvet:
                        display_olymp[i][j] = otvet
                        break

            olymp_message = f'<p>+{otvet}</p>'

            if display_olymp == olymp_matrix:
                olymp_message = f'<p>Поздравляю!</p>'

            return redirect('/olymp')

        elif otvet == 'reset':
            reset_olymp()
            olymp_message = f'<p>Новая олимпийка.</p>'

            return redirect('/olymp')

        elif otvet == 'help':
            for i in range(rows):
                for j in range(1, cols):
                    if display_olymp[i][j] != olymp_matrix[i][j]:
                        display_olymp[i][j] = f'{olymp_matrix[i][j][0]}{"*" * (len(olymp_matrix[i][j])-2)}{olymp_matrix[i][j][-1]}'
            olymp_message = f'<p>Подсказки - с количеством букв.</p>'
            return redirect('/olymp')

        elif otvet == 'exit':
            display_olymp = olymp_matrix
            olymp_message = f'<p>Это полная олимпийка.</p>'
            return redirect('/olymp')

        else:
            if otvet != '':
                olymp_message = f'<p>{otvet} - нет такого слова.</p>'
            return redirect('/olymp')


    page = f'{page_head}' \
           f'{list_to_rowspanhtml(display_olymp)}' \
           f'{olymp_message}' \
           f'''</main>

               <footer>
                   <div class ="container">
                   <span class ="text-muted"> {input_form} </span>
                   </div> 
               </footer>

               </body></html>'''

    return page

if __name__ == '__main__':

    app.run(debug=True)
