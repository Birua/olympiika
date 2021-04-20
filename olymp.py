'''
    Flask app for word game Olimpiika.
    - generates olimpiika tree automatically from sociation.org data
    - button for hints (first and last letters in a word with * for other letters)
    - button for solution
    - button for reset

    Versions History:
      0.16 -- 20/04/21 Highlight entered table cell for a new word
      0.15 -- 19/04/21 Bug fixes - trim spaces, word already entered, letter yo, exclude some 18+ words
      0.14 -- 14/04/21 Classes OOP (under development)
      0.13 -- 02/04/21 Nouns and Sociation load optimization
      0.12 -- Mobile view hotfix
      0.11 -- First successful deploy to heroku. Dated April 01, 2021

'''
from flask import Flask, redirect, request, session
import pandas as pd
import random
import math

app = Flask(__name__)
# Set the secret key to some random bytes. Keep this really secret!
app.secret_key = b'197alop_651351_ffg_2930'


class Olimpiika:
    '''
    Создает, проверяет и сохраняет олимпийки

    Args:
        steps (int):
            к-во ступеней: (1) - слово + 2 ассоциации, (2) - слово + 2 ассоциации + 4 ассоциации и т.п.
        starting_word (str):
            начальное слово, случайное (='random') по умолчанию
    Kwargs:
        difficulty (str):
            сложность ассоциаций 'easy' - 4 первых (по умолчанию) или 'hard'- весь список
    Attributes:
        steps (int):
            к-во ступеней
        starting_word (str):
            начальное слово
        difficulty (str):
            сложность ассоциаций
    Methods:
        hints():
            Подсказки с количеством букв: пример = п****р
        solution():
            Все ответы
        reset():
            Сброс
        save():
        load():
    '''
    def __init__(self, steps, starting_word='random', **kwargs):
        self.steps = steps
        self.starting_word = starting_word
        if not ("difficulty" in kwargs):
            self.difficulty = 'easy'
        else:
            self.difficulty = kwargs['difficulty']


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


def olymp_auto(nouns, sociation, inputword: str, **kwargs):
    """ Возвращает желаемое число ассоциаций по sociation.org.tsv
        Одно слово превращаем в 2 или больше через ассоциации.
    Args:
      nouns - dataframe существительных
      sociation - dataframe sociation
      inputword: str - исходное слово
    Kwargs:
      difficulty: str - сложность ассоциаций
         'easy' - 4 первых (по умолчанию) или 'hard'- весь список
      quantity: int - количество слов на выдачу
         2 - по умолчанию
      exclude: list of str
         список слов на исключение
    Returns:
      words: List of strings
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

    # Фильтрация слов 18+
    exclude18 = ['член', 'мастурбация', 'минет', 'порнография', 'стриптиз',
                 'анал', 'куннилингус', 'порно', 'презерватив', 'презервативы',
                 'секс', 'совокупление', 'хуй', 'шлюха', 'эрекция', 'эротика',
                 'сосок', 'оргия', 'клитор', 'девственность', 'возбуждение',
                 'влагалище', 'дефлорация', 'зачатие', 'фетиш',
                 'проституция',]

    Nouns = nouns
    Sociation = sociation

    aa = Sociation.loc[Sociation[0] == inputword][1]
    bb = Sociation.loc[Sociation[1] == inputword][0]

    # почистим похожие на исходное слова
    aa = aa.drop(aa[aa.str.contains(inputword[:3])].index)
    bb = bb.drop(bb[bb.str.contains(inputword[:3])].index)

    # Уберем слова, которые даны в списке исключений
    # ~ - инвертируем булины
    aa = aa[~aa.isin(exclude18)]
    bb = bb[~bb.isin(exclude18)]
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
    if len(words) >= quantity:
        words = random.sample(list(words), quantity)
    else:
        words = 'Error_404'

    return words


def olymp_gen(nouns, sociation, olymp_steps, starting_word = 'random'):
    """ Генератор олимпиек
        Превращает одно слово (или случайное) в цепочку ассоциаций
        в виде олимпийки.
    Args:
      nouns - dataframe существительных
      sociation - dataframe sociation
      olymp_steps: int - к-во ступеней: (1) - слово + 2 ассоциации, (2) - слово + 2 ассоциации + 4 ассоциации и т.п.
    Kwargs:
      starting_word: str - начальное слово, случайное по умолчанию
    Returns:
      List of strings
    """
    Nouns = nouns
    Sociation = sociation


    if starting_word == 'random':
        starting_word = Sociation.sample().values[0][0]
    # print(starting_word)

    olymp_list = [starting_word]
    i = 0
    while i <= (2**olymp_steps - 2):  # 2**3 - 2 = 6 - получаем пару ассоциаций для 6 слов
        # extend not append - because [1,2].append([3,4]) = [1,2,[3,4]]
        # [1,2].extend([3,4]) = [1,2,3,4]
        new_pair = olymp_auto(Nouns, Sociation, starting_word, quantity=2, exclude=olymp_list)
        if new_pair == 'Error_404':
            new_pair = (starting_word, 'Error_404')
            break
        olymp_list.extend(new_pair)
        i += 1
        starting_word = olymp_list[i]

    return olymp_list


def reset_olymp(olymp_steps):
    """ Сброс - создание новой случайной олимпийки.
    Args:
      olymp_steps: int - к-во ступеней: (1) - слово + 2 ассоциации, (2) - слово + 2 ассоциации + 4 ассоциации и т.п.
    Kwargs:

    Returns:
      olymp_matrix
    """
    rows, cols = (int(2 ** olymp_steps), (olymp_steps + 1))

    Nouns = pd.read_csv("static/russian_nouns.csv", header=None)
    Sociation = pd.read_csv("static/sociation.org.tsv", header=None, sep='\t')

    game_olymp = ['  ']
    # restart auto generator for Random word until it gets a full game_olymp list
    while any([x.strip() == '' for x in game_olymp]) or len(game_olymp) != 2**(olymp_steps+1) - 1:
        game_olymp = olymp_gen(Nouns, Sociation, olymp_steps, starting_word='random')
    # print(len(game_olymp), 2**(olymp_steps+1) - 1, game_olymp, [x.strip() == '' for x in game_olymp])

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

    return olymp_matrix

@app.route('/', methods=['POST', 'GET'])
def olymp_index():

    olymp_steps = 4
    session['olymp_steps'] = olymp_steps
    olymp_matrix = reset_olymp(olymp_steps)
    rows, cols = (int(2 ** olymp_steps), (olymp_steps + 1))
    session['olymp_matrix'] = olymp_matrix
    display_olymp = [[' ' for i in range(cols)] for j in range(rows)]
    for i in range(rows):
        display_olymp[i][0] = olymp_matrix[i][0]
    session['display_olymp'] = display_olymp
    session['olymp_message'] = f'<p>Приветствую Вас!</p>'
    session['olymp_highlight'] = ''

    return redirect('/olymp')

@app.route('/olymp', methods=['POST', 'GET'])
def olymp_start():

    if session.get('olymp_steps') == None:
        return redirect('/')

    olymp_steps = session.get('olymp_steps')
    rows, cols = (int(2 ** olymp_steps), (olymp_steps + 1))
    olymp_matrix = session.get('olymp_matrix')
    display_olymp = session.get('display_olymp')
    game_olymp = [j for sub in olymp_matrix for j in sub]
    game_display = [j for sub in display_olymp for j in sub]
    olymp_message = session.get('olymp_message')
    olymp_highlight = session.get('olymp_highlight')


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
    <nav>
        <div align="right">
            <font size="-1">Версия 0.16</font>
        </div>
    </nav>
    <body>
    <h1>Автоолимпийка</h1>
    
    <main>
    '''
# <link rel="stylesheet" href="{url_for('static', filename='olymp.css')}">
# <link rel="stylesheet" href="https://cryptex.games/online/045/go/stat2/stat2.css">

    if request.method == 'POST':
        if 'submit' in request.form:
            otvet = request.form['nm']
            otvet = otvet.lower()           # only lower-case symbol everywhere
            otvet = otvet.strip()           # trim all whitespace before and after a word
            otvet = otvet.replace('і','ы')  # случайній набор букві ы
        elif 'help' in request.form:
            otvet = 'help'
        elif 'reset' in request.form:
            otvet = 'reset'
        elif 'exit' in request.form:
            otvet = 'exit'
        else:
            otvet = ''

        # Работа с буквой Ё
        if 'е' in otvet and 'ё' in ''.join(game_olymp):
            for word in game_olymp:
                if word.replace('ё','е') == otvet:
                    otvet = word

        # Слово уже есть в отображаемой олимпийке
        if otvet in game_display:
            olymp_message = f'<p>{otvet} - уже есть.</p>'
            session['olymp_message'] = olymp_message
            return redirect('/olymp')

        # Слово есть в полной олимпийке
        if otvet in game_olymp:

            for i in range(rows):
                for j in range(1, cols):
                    if olymp_matrix[i][j] == otvet:
                        display_olymp[i][j] = otvet
                        session['display_olymp'] = display_olymp
                        break

            olymp_message = f'<p>+{otvet}</p>'
            session['olymp_message'] = olymp_message
            session['olymp_highlight'] = otvet

            if display_olymp == olymp_matrix:
                olymp_message = f'<p>Поздравляю!</p>'
                session['olymp_message'] = olymp_message

            return redirect('/olymp')
        # Служебные слова
        elif otvet == 'reset':
            olymp_matrix = reset_olymp(olymp_steps)
            session['olymp_matrix'] = olymp_matrix
            display_olymp = [[' ' for i in range(cols)] for j in range(rows)]
            for i in range(rows):
                display_olymp[i][0] = olymp_matrix[i][0]
            session['display_olymp'] = display_olymp

            olymp_message = f'<p>Новая олимпийка.</p>'
            session['olymp_message'] = olymp_message
            return redirect('/olymp')

        elif otvet == 'help':
            for i in range(rows):
                for j in range(1, cols):
                    if display_olymp[i][j] != olymp_matrix[i][j]:
                        display_olymp[i][j] = f'{olymp_matrix[i][j][0]}{"*" * (len(olymp_matrix[i][j])-2)}{olymp_matrix[i][j][-1]}'
            session['display_olymp'] = display_olymp
            olymp_message = f'<p>Подсказки - с количеством букв.</p>'
            session['olymp_message'] = olymp_message
            return redirect('/olymp')

        elif otvet == 'exit':
            display_olymp = olymp_matrix
            session['display_olymp'] = display_olymp
            olymp_message = f'<p>Это полная олимпийка.</p>'
            session['olymp_message'] = olymp_message
            return redirect('/olymp')

        else:
            if otvet != '':
                olymp_message = f'<p>{otvet} - нет такого слова.</p>'
                session['olymp_message'] = olymp_message
            return redirect('/olymp')


    page = f'{page_head}' \
           f'{list_to_rowspanhtml(display_olymp)}' \
           f'{olymp_message}' \
           f'''
            <br />&nbsp;<br />
            <br />&nbsp;<br />
        </main>

               <footer>
                   <div class ="container">
                   <span class ="text-muted"> {input_form} </span>
                   </div> 
               </footer>

            </body></html>'''

    # Highlight a new word in a table cell -- only 1 time!
    if olymp_highlight != '':
        olymp_highlight = f'>{olymp_highlight}<'
        # highlight color = #d5f7e2 -- update to style in the future
        highlighted_cell = f''' style="background-color:#d5f7e2;"{olymp_highlight}'''
        page = page.replace(olymp_highlight, highlighted_cell)
        session['olymp_highlight'] = ''      # delete highlight

    return page

if __name__ == '__main__':

    app.run(debug=False)
