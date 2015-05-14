# coding=utf-8
import datetime
import string
from nekbot import settings
from nekbot.core.commands import command
from nekbot.core.commands.control import control
from nekbot.core.commands.temp import Text, DatetimeOrDate, Bool, Int
from nekbot.core.exceptions import InvalidArgument, PrintableException
from nekbot.protocols import Message
from nekbot.storage.ejdb import ejdb

__author__ = 'Nekmo'

db = ejdb('polls')

WIDE_WITH = 40
WIDTH = 25
OPTIONS_EXAMPLES = ['rojo', 'verde', 'amarillo', 'azul', 'violeta', 'negro', 'blanco']
LETTERS = string.ascii_letters


class CancelableDatetimeOrDate(DatetimeOrDate):
    REGEX_PATTERN = '(\d{2}/\d{2}/\d{4}|n)( \d{2}\:\d{2}|)'

    def invalid(self, msg):
        if msg.body == 'n':
            return True
        return super(CancelableDatetimeOrDate, self).invalid(msg)


@control(is_groupchat=True)
@command
def addpoll(msg):
    data = {'users': {}, 'owner': msg.user.get_id(), 'groupchat': str(msg.groupchat), 'protocol': msg.protocol.name,
            'options': [], 'created_at': datetime.datetime.now()}
    msg.user.send_message('Introduzca el título para la encuesta (por ejemplo, ¿Cuál es tu color favorito?:')
    data['title'] = Text(msg).read()
    i = 0
    while True:
        option = {'votes': []}
        quest = 'Escriba la descripción (por ejemplo, %s)%s:' % (
            OPTIONS_EXAMPLES[i % len(OPTIONS_EXAMPLES)], '. Escriba "n" para no añadir más opciones' if i > 1 else '')
        msg.user.send_message(quest)
        option['description'] = Text(msg).read()
        if i > 1 and option['description'] == 'n':
            break
        data['options'].append(option)
        i += 1
    msg.user.send_message('Si desea que esta encuesta tenga una fecha límite, escríbala mediante la sintaxis '
                          'DD/MM/YYYY, de lo contrario, escriba "n".')
    dt = CancelableDatetimeOrDate(msg).read()
    if isinstance(dt, datetime.datetime):
        data['expiration_date'] = dt
    elif not (isinstance(dt, Message) and dt.body == 'n'):
        raise NotImplementedError('Invalid response for dt. Type: %s' % type(dt))
    msg.user.send_message('¿Cuántas opciones puede votar cada persona? (número)')
    data['max_votes'] = Int(msg).read()
    msg.user.send_message('¿Permitir a los usuarios cambiar su voto? [S/N]')
    data['change_vote'] = Bool(msg).read()
    msg.user.send_message('¿Ocultar los resultados hasta que termine la encuesta? [S/N]')
    data['hide_results'] = Bool(msg).read()
    msg.user.send_message('¿Los usuarios de otras salas pueden votar/ver esta encuesta? [S/N]')
    data['private'] = Bool(msg).read()
    data['id'] = len(db.find('poll')) + 1
    db.save('poll', data)
    msg.user.send_message('Su encuesta se ha creado. Los usuarios pueden votarla con {s}vote {id}.'.format(
        s=settings.SYMBOL, id=data['id']))


def poll_is_open(register):
    return register['expiration_date'] is None or register['expiration_date'] > datetime.datetime.now()


def poll_info(register, advanced=False):
    expiration_date = register['expiration_date'].strftime('%d/%m/%Y') if register['expiration_date'] is not None \
        else '???'
    body = u'#{id} {title} {expiration_date}'.format(id=register['id'], title=register['title'],
                                                     expiration_date=expiration_date)
    if advanced:
        body += ' [%s] ' % 'ABIERTA' if poll_is_open(register) else 'CERRADA'
        body += u'✔ Voto cambiable ' if register['change_vote'] else u'✘ No puede cambiar voto '
        body += u'ꙭ Voto secreto hasta cerra encuesta. ' if register['hide_results'] else u'ꙭ Puede ver los votos. '
        body += u'☹ Votos solo de esta sala. ' if register['private'] else u'☺ Votos desde cualquier sala. '
        body += u'⛃ %i votos por persona. ' % register['max_votes'] if register['max_votes'] > 1 else \
            u'⛂ Un voto por persona. '
    return body


def list_polls():
    if not len(db.find('poll')):
        return 'Oh... ¡OH! No hay encuestas para votar. ¡Crea muchas con {s}addpoll!'.format(s=settings.SYMBOL)
    response = ''
    polls_open = db.find('poll',
                         {'$or': [{'expiration_date': {'$gt': datetime.datetime.now()}},
                                  {'expiration_date': None}]}, hints={'$orderby': [('id', -1)]})
    polls_close = db.find('poll', {'expiration_date': {'$lte': datetime.datetime.now()}},
                          hints={'$orderby': [('created_at', -1)]})[:5]
    if len(polls_open):
        response += 'Encuestas abiertas: ' + u' ⚫ '.join(map(poll_info, polls_open))
    if len(polls_open) and len(polls_close):
        response += '\n'
    if len(polls_close):
        response += 'Encuestas cerradas: ' + u' ⚫ '.join(map(poll_info, polls_open))
    if len(polls_open):
        response += u'\nVea las opciones de las encuestas abiertas con: {s}vote <número>'.format(s=settings.SYMBOL)
    return response


def get_register(poll):
    registers = db.find('poll', {'id': poll})
    if not registers:
        raise InvalidArgument('Poll id is not valid.', poll, 0)
    return registers[0]


def check_groupchat(msg, register):
    if register['private'] and str(msg.groupchat) != register['groupchat']:
        raise PrintableException('Ehh... no. No puedes votar esta encuesta desde esta sala.')


def check_owner(msg, register):
    return msg.user.get_id() == register['owner']


def view_poll(msg, poll):
    register = get_register(poll)
    check_groupchat(msg, register)
    body = poll_info(register, True)
    options = ['  %s. %s' % (LETTERS[i], option['description']) for i, option in enumerate(register['options'])]
    body += '\n%s' % '\n'.join(options)
    body += (u'\nEjemplo para votar la segunda y primera opción: %svote %i b a' if register['max_votes'] > 1 else
             u'\nEjemplo para votar la segunda opción: %svote %i b') % (settings.SYMBOL, poll)
    return body


def vote_poll(msg, poll, votes):
    register = get_register(poll)
    check_groupchat(msg, register)
    user_id = msg.user.get_id()
    if register['expiration_date'] is not None and datetime.datetime.now() > register['expiration_date']:
        raise PrintableException('¡Uy! La encuesta ya está cerrada. Acabo el %s' % register['expiration_date'])
    if register['change_vote'] and user_id in register['users']:
        raise PrintableException('Espera... me suena tu cara... ¡tú ya habías votado! ¡Y en esta encuesta no puedes '
                                 'cambiar tu voto!')
    if len(votes) > register['max_votes']:
        raise PrintableException('¡Ey! No te pases... ¡Solo se puede %s!' % ('%i opciones' % register['max_votes']) if
                                 register['max_votes'] > 1 else 'una vez')
    if len(set(votes)) != len(votes):
        raise PrintableException('Espera... ¡Hay opciones repetidas! Dejaré que lo vuelvas a intentar sin hacer '
                                 'trampas ^_^')
    if user_id in register['users']:
        for vote_id in register['users']:
            register['options'][vote_id]['votes'].remove(user_id)
    register['users'][user_id] = []
    user_votes = register['users'][user_id]
    for vote in votes:
        if len(vote) != 1 or not vote in LETTERS:
            raise PrintableException('{letter}... ¡¿¡¿{letter}?!?! ¡Eso no es una opción!'.format(letter=vote))
        vote_id = LETTERS.index(vote)
        if vote_id > len(register['options']):
            raise PrintableException('{letter} no es una opción válida. Debe ser una entre: {options}'.format(
                letter=vote, options=' '.join(list(LETTERS[:register['options']]))))
        register['options'][vote_id]['votes'].append(user_id)
        user_votes.append(vote_id)
    db.save('poll', register)
    return '¡Gracias por votar!'


@control(is_groupchat=True)
@command
def vote(msg, poll=int, *args):
    if poll is int:
        msg.short_reply(list_polls())
    elif not args:
        return view_poll(msg, poll)
    else:
        return vote_poll(msg, poll, args)


@control(is_groupchat=True)
@command('voteresults', int)
def voteresults(msg, poll):
    register = get_register(poll)
    check_groupchat(msg, register)
    if poll_is_open(register) and not check_owner(msg, register):
        raise PrintableException('¡Sé paciente! Los resultados podrán verse el: %s' % register['expiration_date'])
    total = sum(map(lambda x: len(x['votes']), register['options']))
    body = '%s (%i votos)' % (poll_info(register), total)
    width = WIDE_WITH if 'wide_messages' in msg.protocol.features else WIDTH
    for option in sorted(register['options'], key=lambda x: len(x['votes']), reverse=True):
        votes = len(option['votes'])
        percentage = int((100 / (total * 1.0)) * votes) if total else 0
        body += '\n%s' % option['description']
        use_bar = int(percentage * width / 100.0)
        space_bar = width - use_bar
        body += u'\n[%s%s] %i%% (%i)' % (use_bar * u'☰', space_bar * u'⚊', percentage, votes)
    return body