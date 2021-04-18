import globals


def populate_word_game():
    questions = []
    for line in open('res/uwuwords.txt'):
        question, answer = line.split(';')[:2]
        questions.append({'question': question, 'answer': answer, 'language': 'english'})

    coll = globals.bot.db['word_game']
    coll.insert_many(questions)
