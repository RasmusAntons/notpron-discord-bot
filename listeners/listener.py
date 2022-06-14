import globals
from abc import ABC, abstractmethod


class Listener(ABC):
    def __init__(self):
        super(Listener, self).__init__()


class MessageListener(Listener):
    def __init__(self):
        super(MessageListener, self).__init__()
        globals.bot.message_listeners.add(self)

    @abstractmethod
    async def on_message(self, msg):
        pass


class ReactionListener(Listener):
    def __init__(self):
        super(ReactionListener, self).__init__()
        globals.bot.reaction_listeners.add(self)

    @abstractmethod
    async def on_reaction_add(self, reaction, user):
        pass

    @abstractmethod
    async def on_reaction_remove(self, reaction, user):
        pass


class RawReactionListener(Listener):
    def __init__(self):
        super(RawReactionListener, self).__init__()
        globals.bot.raw_reaction_listeners.add(self)

    @abstractmethod
    async def on_raw_reaction_add(self, channel, member, payload):
        pass

    @abstractmethod
    async def on_raw_reaction_remove(self, channel, member, payload):
        pass


class MessageEditListener(Listener):
    @abstractmethod
    async def on_message_edit(self, message, cached_message=None):
        pass


class MessageDeleteListener(Listener):
    def __init__(self):
        super(MessageDeleteListener, self).__init__()
        globals.bot.message_delete_listeners.add(self)

    @abstractmethod
    async def on_message_delete(self, message_id, channel, guild, cached_message=None):
        pass


class ReadyListener(Listener):
    def __init__(self):
        super(ReadyListener, self).__init__()
        globals.bot.ready_listeners.add(self)

    @abstractmethod
    async def on_ready(self):
        pass


class MemberJoinListener(Listener):
    def __init__(self):
        super(MemberJoinListener, self).__init__()
        globals.bot.member_join_listeners.add(self)

    @abstractmethod
    async def on_member_join(self, member):
        pass
