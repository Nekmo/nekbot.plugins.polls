# coding=utf-8
import datetime
from nekbot import settings
from nekbot.core.commands import command
from nekbot.core.commands.control import control
from nekbot.core.commands.temp import Text, DatetimeOrDate, Bool
from nekbot.protocols import Message
from nekbot.storage.ejdb import ejdb

__author__ = 'Nekmo'

db = ejdb('polls')

OPTIONS_EXAMPLES = ['rojo', 'verde', 'amarillo', 'azul', 'violeta', 'negro', 'blanco']

class CancelableDatetimeOrDate(DatetimeOrDate):
    REGEX_PATTERN = '(\d{2}/\d{2}/\d{4}|n)( \d{2}\:\d{2}|)'

    def invalid(self, msg):
        if msg.body == 'n':
            return True
        return super(CancelableDatetimeOrDate, self).invalid(msg)


@control(is_groupchat=True)
@command
def addpoll(msg):
    data = {'users': {}, 'owner': msg.user.get_id(), 'groupchat': msg.groupchat.id, 'protocol': msg.protocol.name,
            'options': []}
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


def list_polls():
    pass


def view_poll(poll):
    pass


def vote_poll(msg, poll, args):
    pass


@control(is_groupchat=True)
@command
def vote(msg, poll=int, *args):
    if not poll:
        return list_polls()
    elif poll and not args:
        return view_poll(poll)
    else:
        return vote_poll(msg, poll, args)