# -------------------------------------------------------------------------- #
# IMPORTAÇÕES


# tkinter
from tkinter import Tk, Frame, Label, Button
from tkinter import PhotoImage, Listbox, Variable
from tkinter.messagebox import showerror, showinfo
from tkinter.ttk import Style, Combobox

# JustWatch
from justwatch import JustWatch

# random
from random import choice

# requests
from requests import get
from requests.exceptions import HTTPError, ConnectionError

# os
from os import remove

# pillow
from PIL import Image, ImageTk

# webbrowser
from webbrowser import open as op

# atexit
from atexit import register

# sys
from sys import exit


# -------------------------------------------------------------------------- #
# CONSTANTES


# Cores
COLOR1 = '#292929'  # Fundo
COLOR2 = '#c7c5c5'  # Janela
COLOR3 = '#fffbef'  # Letra

# Caminho do poster para ser deletado no final
POSTER_PATH = './poster.jpg'

# Arquivo com as sugestões dadas
SUGESTIONS_FILE = './sugetions.txt'

# URLs
BASE_URL = 'https://www.justwatch.com'
BASE_IMAGE_URL = 'https://images.justwatch.com'


# Dicionário mapeia os streammings para os códigos
# deles na url do JustWatch
PROVIDERS_DICT = {
    'Disney-Plus': 'dnp', 'GloboPlay': 'gop',
    'HBO-MAX': 'hbm', 'Netflix': 'nfx',
    'Prime-Video': 'prv', 'Star-Plus': 'srp'
}


# Mapeia série e filme (português) para o que vai na url
CONTENT_TYPES_DICT = {'Série': 'show', 'Filme': 'movie'}


# Mapeia os géneros
GENRES_DICT = {
   'Ação & Aventura': 'act', 'Comédia': 'cmy', 'Documentário': 'doc',
   'Fantasia': 'fnt', 'Terror': 'hrr', 'Música & Musical': 'msc',
   'Romance': 'rma', 'Esportes & Fitness': 'spt', 'Western': 'wsn',
   'Animação': 'ani', 'Crime': 'crm',
   'Drama': 'drm', 'História': 'hst', 'Família': 'fml',
   'Mistério & Thriller': 'trl', 'Ficção Científica': 'scf',
   'Guerra & Militar': 'war', 'Reality TV': 'rly'
}


# Streammings, filme/série e géneros
# para os Combobox e Listbox
stream_list = [key for key in PROVIDERS_DICT]
content_type_list = [key for key in CONTENT_TYPES_DICT]
genre_list = [key for key in GENRES_DICT]


[
    item.insert(0, 'TODOS')
    for item in
    (stream_list, content_type_list, genre_list)
]


# Lista de Rating do imdb
rating_list = [
    0.0, 1.0, 2.0, 3.0, 4.0, 5.0,
    6.0, 7.0, 8.0, 9.0, 10.0
]

rating_list.insert(0, 'QUALQUER')

global poster_img, button_img
global thumbs_up_img, cool_img, imdb_img


# -------------------------------------------------------------------------- #
# FUNÇÕES


def remove_poster():
    """Cuida de remover o poster baixado."""
    try:
        remove(POSTER_PATH)
    except OSError:
        pass


def delete_sugestions():
    """Cuida de remover arquivo com sugestões passadas."""
    try:
        remove(SUGESTIONS_FILE)
        showinfo('Sucesso', 'Sugestões deletadas com sucesso')
    except OSError:
        showinfo('', 'Não possui sugestões gravadas ainda')


def mount_query(streamming_listbox, genres_select, items):
    """Cuida de montar a requisição."""

    # Aqui, destroi para não acontecer de os labels ficarem colados
    # ao apertar botão novamente.
    [widget.destroy() for widget in output_frame.winfo_children()]

    # Acho que não é necessario, o poster é sobsecrito aqui
    # mas acho que não faz mal também kkk!
    remove_poster()

    # Cria listas de streammings escolhidos e géneros escolhidos.
    streammings_list = [
        streamming_listbox.get(i)
        for i in streamming_listbox.curselection()
    ]

    genres_list = [
        genres_select.get(i)
        for i in genres_listbox.curselection()
    ]

    if 'TODOS' in streammings_list or not streammings_list:
        # Lista
        streamming = list(PROVIDERS_DICT.values())
    else:
        # Itens enviados como lista
        streamming = [PROVIDERS_DICT[i] for i in streammings_list]

    if 'TODOS' in genres_list or not genres_list:
        # Lista
        genres = list(GENRES_DICT.values())
    else:
        # Itens enviados como lista
        genres = [GENRES_DICT[i] for i in genres_list]

    if items[0] == 'TODOS' or items[0] == '':
        # Lista
        types = list(CONTENT_TYPES_DICT.values())
    else:
        # Item enviado como lista
        types = [CONTENT_TYPES_DICT[items[0]]]

    # Aqui, pega de qualquer rating, ou do
    # rating especificado até ao rating de 10.0
    if items[1] == 'QUALQUER' or items[1] == '':
        rating = {
            "imdb:score": {
                "min_scoring_value": 0.0,
                "max_scoring_value": 10.0
            }
        }
    else:
        rating = {
            "imdb:score": {
                "min_scoring_value": float(items[1]),
                "max_scoring_value": 10.0
            }
        }

    query(streamming, types, genres, rating)


def query(streamming, types, genres, rating):
    """Cuida de fazer a consulta"""
    try:
        just_watch = JustWatch(country='BR')

        results = just_watch.search_for_item(
            providers=streamming,
            content_types=types,
            genres=genres,
            scoring_filter_types=rating,
            page_size=100
        )
    except ConnectionError:
        showerror('', 'Verifique sua conexão e tente mais tarde')
        exit()
    except HTTPError:
        showerror('', 'Erro inesperado na requisição. Tente mais tarde')
        exit()
    else:
        parse_results(results)


def parse_results(results):
    """Cuida de pegar os dados."""

    '''
    Aqui, dependendo da combinação (género, filme/serie etc), pode
    não achar algum item. Exemplo, se colocar: GloboPlay, Documentário,
    Série e classificação a partir de 6.0, dá erro de KeyError, porque
    (neste caso) não tem poster. Mas quem garante que o globoplay tem
    documentários? kk.. Então, para não usar um try/except para cada item,
    fiz assim kk.
    '''
    try:
        # Pega os títulos
        titles = [item['title'] for item in results['items']]

        # Pega os links para o filme ou seŕie
        links = [
            f"{BASE_URL}{item['full_path']}"
            for item in results['items']
        ]

        # Pega o link para o poster do tamanho especificado.
        # Aqui tamanho é s332
        posters = [
            f"{BASE_IMAGE_URL}{item['poster'].replace('{profile}', 's332')}"
            for item in results['items']
        ]

        '''
        Aqui, quero pegar o rating do imdb. Mas o json é muito complicado kk.
        Tem dicionário dentro de lista com lista dentro de dicionário.
        Para piorar, o dicionário onde está o rating do imdb é
        {'provider_type': 'imdb:score', 'value': 8.5}, e este dicionário está
        em posições diferentes para cada lista kk. E não posso pegar só pelo
        provider_type, pois tem outros dicionários com provider_type cujos
        valores não são imdb:score.
        Então, score_list, pega a lista de listas com os dicionários.
        Depois imdb_list, pega da lista de listas o rating (na chave value),
        se o valor da chave provider_type for imdb:score
        '''
        scorelist = [
            results['items'][score]['scoring']
            for score in range(len(results['items']))
        ]

        imdb_scores = list()
        for item in range(len(scorelist)):
            for provider in scorelist[item]:
                if provider['provider_type'] == 'imdb:score':
                    imdb_scores.append(provider['value'])
    except KeyError:
        showinfo(
            '',
            'Não foram emcontrados itens com a combinação' \
            ' de parâmetros especificados'
        )
        return
    else:
        # Dicionario que mapeia os titulos ao link.
        # Ex: 'Tulsa King': 'https://....serie/tulsa-king'
        title_link_dict = {
            key: value
            for (key, value)
            in zip(titles, links)
        }

        # Dicionario que mapeia titulos para o link do poster
        title_poster_dict = {
            key: value
            for (key, value)
            in zip(titles, posters)
        }

        # Dicionário que mapeia títulos ao rating do imdb
        title_score_dict = {
            key: value
            for (key, value)
            in zip(titles, imdb_scores)
        }

        pick_sugestion(
            title_link_dict,
            title_poster_dict,
            title_score_dict
        )


def was_sugested(title):
    """
    Cuida de varrer o arquivo
    para vêr se título já foi sugerido.
    """

    '''
    Retornos
    1 - Arquivo existe e título já foi seugerido.
    2 - Arquivo existe e título ainda não foi sugerido.
    3 - Arquivo não existe ainda. Será criado e título será escrito.
    '''
    try:
        with open(SUGESTIONS_FILE, 'r', encoding='utf-8') as f:
            found = False
            for line in f:
                if title in line:
                    found = True
            if found:
                return 1
            else:
                return 2
    except IOError:
        # Aqui, arquivo estará vazio ainda.
        with open(SUGESTIONS_FILE, 'w', encoding='utf-8') as f:
            f.write(f'{title}\n')
            return 3


def pick_sugestion(
    title_link_dict,
    title_poster_dict,
    title_score_dict
):
    """Escolhe o título para sugerir"""
    title, link = choice(list(title_link_dict.items()))
    exists = was_sugested(title)

    count = 0
    while exists == 1:
        count += 1
        if count == 5:
            showinfo(
                '',
                'Estamos com problemas em sugerir algo novo.' \
                ' Experimente deletar sugeridos, ou alterar os parâmetros' \
                ' para a sugestão. Iremos terminar o programa.'
            )
            exit()
        title, link = choice(list(title_link_dict.items()))
        exists = was_sugested(title)

    if exists == 2:
        # Arquivo existe, mas título não foi sugerido ainda.
        # Será escrito aqui no arquivo.
        with open(SUGESTIONS_FILE, 'a', encoding='utf-8') as f:
            f.write(f'{title}\n')

    poster = get(title_poster_dict[title])

    '''
    Aqui, conto com que se não deu erro na função query, não será
    aqui meros segundos depois que a conexão falhará. Por isso não
    uso aqui try/except. Mas concerteza que pode acontecer né? kkk!!
    '''
    with open(POSTER_PATH, 'wb') as f:
        [f.write(chunk) for chunk in poster]

    show_output(title, link, title_poster_dict, title_score_dict)


def show_output(title, link, title_link_dict, title_score_dict):
    """Mostra o resultado."""
    global poster_img, button_img
    global thumbs_up_img, cool_img, imdb_img

    thumbs_up_img = Image.open('icones/thumbs-up.png')
    thumbs_up_img = thumbs_up_img.resize((25, 25))
    thumbs_up_img = ImageTk.PhotoImage(thumbs_up_img)

    label = Label(
        output_frame, text='Vamos Assistir:....',
        font=('Roboto 10 bold'), anchor='center',
        bg=COLOR1, fg=COLOR3
    )
    label.place(x=150, y=0)

    title_label = Label(
        output_frame, text=f' {title}?',
        font=('Roboto 10 bold'), anchor='nw', image=thumbs_up_img,
        bg=COLOR1, fg=COLOR3, compound='left'
    )
    title_label.place(x=80, y=25)

    imdb_img = Image.open('icones/imdb.png')
    imdb_img = imdb_img.resize((15, 15))
    imdb_img = ImageTk.PhotoImage(imdb_img)

    imdb_rating_label = Label(
        output_frame, image=imdb_img, compound='left',
        text=f'   Classificação:   {title_score_dict[title]:.1f}',
        font=('Roboto 8 bold'), anchor='nw',
        bg=COLOR1, fg=COLOR3
    )
    imdb_rating_label.place(x=150, y=55)

    poster_img = Image.open(POSTER_PATH)
    poster_img = ImageTk.PhotoImage(poster_img)

    poster_img_label = Label(
        output_frame, text='',
        image=poster_img
    )
    poster_img_label.place(x=50, y=80)

    cool_img = Image.open('icones/cool.png')
    cool_img = cool_img.resize((25, 25))
    cool_img = ImageTk.PhotoImage(cool_img)

    link_label = Label(
        output_frame, text='   Veja mais informações!   ',
        font=('Roboto 10 bold'), fg=COLOR3,
        bg=COLOR1, image=cool_img, compound='left'
    )
    link_label.place(x=120, y=560)

    button_img = Image.open('icones/button.png')
    button_img = button_img.resize((45, 45))
    button_img = ImageTk.PhotoImage(button_img)

    link_label_button = Label(
        output_frame, text='',
        image=button_img,
        cursor='hand2',
        bg=COLOR1
    )
    link_label_button.place(x=180, y=610)
    link_label_button.bind(
        '<Button-1>',
        lambda open_link: callback(link)
    )


def callback(url):
    """Cuida de abrir o link"""
    op(url)


# -------------------------------------------------------------------------- #
# JANELA


window = Tk()
window.title('')
window.geometry('1000x720')
window.resizable(0, 0)
window.configure(bg=COLOR2)


style = Style(window)
style.theme_use('clam')


# -------------------------------------------------------------------------- #
# FRAMES


title_frame = Frame(
    window, width=1000,
    height=48, bg=COLOR1
)
title_frame.grid(
    row=0, column=0,
    sticky='nsew'
)

input_frame = Frame(
    window, width=448,
    height=670, bg=COLOR1
)
input_frame.place(x=0, y=50)

output_frame = Frame(
    window, width=552,
    height=670, bg=COLOR1
)
output_frame.place(x=450, y=50)


# -------------------------------------------------------------------------- #
# CONFIGURANDO TITLE_FRAME


glasses_img = PhotoImage(file='icones/glasses.png')
sad_img = PhotoImage(file='icones/sad.png')

title_label = Label(
    title_frame, text='  Assistir o quê?? SOCORRO!!!',
    image=glasses_img, compound='left',
    font=('Roboto 20 bold'),
    anchor='nw', bg=COLOR1,
    fg=COLOR3
)
title_label.place(x=10, y=10)

sad_label = Label(
    title_frame, text='',
    image=sad_img, compound='right',
    bg=COLOR1
)
sad_label.place(x=420, y=10)


# -------------------------------------------------------------------------- #
# CONFIGURANDO INPUT_FRAME


# Streammings
streammings_label = Label(
    input_frame, text='Streamming',
    font=('Roboto 12 bold'), anchor='nw',
    bg=COLOR1, fg=COLOR3
)
streammings_label.place(x=30, y=20)


stream = Variable(value=stream_list)
streamming_listbox = Listbox(
    input_frame,
    font=('Roboto 10'),
    listvariable=stream,
    selectmode='multiple',
    exportselection=0
)
streamming_listbox.place(x=30, y=60)


# Tipos (filme/serie)
types_label = Label(
    input_frame, text='Filme/Série',
    font=('Roboto 12 bold'), anchor='nw',
    bg=COLOR1, fg=COLOR3
)
types_label.place(x=30, y=270)

types_combobox = Combobox(
    input_frame, width=17,
    font=('Roboto 10'),
    values=content_type_list,
    state='readonly'
)
types_combobox.place(x=30, y=310)


# Género (ação/terror etc)
genres_label = Label(
    input_frame, text='Género',
    font=('Roboto 12 bold'), anchor='nw',
    bg=COLOR1, fg=COLOR3
)
genres_label.place(x=200, y=20)

genre = Variable(value=genre_list)
genres_listbox = Listbox(
    input_frame,
    font=('Roboto 10'),
    listvariable=genre,
    selectmode='multiple',
    exportselection=0
)
genres_listbox.place(x=200, y=60)


# Rating Imdb
rating_label = Label(
    input_frame, text='Rating (A partir de)',
    font=('Roboto 12 bold'), anchor='nw',
    bg=COLOR1, fg=COLOR3
)
rating_label.place(x=200, y=270)

rating_combobox = Combobox(
    input_frame, width=17,
    font=('Roboto 10'),
    values=rating_list,
    state='readonly'
)
rating_combobox.place(x=200, y=310)


# Botão para pegar o item
find_img = PhotoImage(file='icones/find.png')

find_button = Button(
    input_frame, text='SUGERIR', font=('Roboto 8 bold'),
    relief='ridge', overrelief='sunken',
    bg=COLOR1, fg=COLOR3, activebackground=COLOR1,
    activeforeground=COLOR3, image=find_img, cursor='hand2',
    compound='left', anchor='nw', command=lambda: mount_query(
        streamming_listbox, genres_listbox,
        [types_combobox.get(), rating_combobox.get()]
    )
)
find_button.place(x=145, y=400)


# Botão para deletar arquivo
# com sugestões passadas
trash_img = Image.open('icones/trash.png')
trash_img = trash_img.resize((15, 15))
trash_img = ImageTk.PhotoImage(trash_img)

delete_sugested_button = Button(
    input_frame, text='  DELETAR SUGERIDOS', font=('Roboto 8 bold'),
    relief='ridge', overrelief='sunken',
    bg=COLOR1, fg=COLOR3, activebackground=COLOR1,
    activeforeground=COLOR3, image=trash_img,
    compound='left', anchor='nw', command=delete_sugestions
)
delete_sugested_button.place(x=110, y=450)


# -------------------------------------------------------------------------- #
# LOOP


# Remove o poster baixado quando sair do app
register(remove_poster)

window.mainloop()


# -------------------------------------------------------------------------- #
