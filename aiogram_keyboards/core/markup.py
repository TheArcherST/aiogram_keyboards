from typing import Callable, overload, Literal, Awaitable, Union

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, InlineKeyboardButton, KeyboardButton, Message

from ..configuration import get_dp, logger, context

from .button import Button, DefinitionScope
from .helpers import MarkupType, Orientation, MarkupScope
from .dialog_meta import meta_able_alias, DialogMeta
from .utils import BoolFilter, _hash_text
from .tools.handle import handle


class MarkupBehavior:
    def __init__(self,
                 handler: Callable[[DialogMeta], Awaitable[None]] = None):

        self._handler = handler

    @property
    def handler(self):

        async def new(obj):
            button = await Button.from_telegram_object(obj)

            meta = DialogMeta(obj,
                              button=button)

            result = await self._handler(meta)

            return result

        return new


class Markup:
    def __init__(self,
                 buttons: list[Button] = None,
                 text: Union[str, Callable[[DialogMeta], Awaitable[str]]] = None,
                 orientation: str = Orientation.UNDEFINED,
                 ignore_state: bool = False,
                 width: int = 1,
                 one_time_keyboard: bool = True,
                 definition_scope: DefinitionScope = None):

        if buttons is None:
            buttons = []

        self.buttons = buttons
        self.text = text
        self.width = width
        self.one_time_keyboard = one_time_keyboard

        self._definition_scope = definition_scope

        self.synchronize_buttons(orientation=orientation,
                                 ignore_state=ignore_state,
                                 definition_scope=self.definition_scope)

    def apply_behavior(self, behavior: MarkupBehavior) -> None:
        if behavior.handler is not None:
            factory = handle(self.filter())
            factory(behavior.handler)

    def handle(self, func: Callable, *filters) -> None:
        create_handler = handle(self.filter(), *filters)
        create_handler(func)

        return None

    @property
    def definition_scope(self):
        result = self._definition_scope

        if result is None:
            if context.state is not None:
                state = context.state
                self._definition_scope = DefinitionScope(state=state)
            else:
                state = context.state or self.hex_hash()

            result = DefinitionScope(state=state)

        return result

    @definition_scope.setter
    def definition_scope(self, value: DefinitionScope):
        if value is None:
            return

        self._definition_scope = value

    @overload
    def synchronize_buttons(self, *,
                            soft: bool = True,
                            orientation: str = None,
                            ignore_state: bool = None,
                            definition_scope: DefinitionScope = None,
                            **kwargs) -> None:

        ...

    def synchronize_buttons(self, soft: bool = True, **kwargs) -> None:

        """Synchronize buttons method

        Provide this params to all buttons in markup.

        Also, here automatically calls buttons struct.

        """

        for i in self.buttons:
            for key, value in kwargs.items():
                actual = getattr(i, key)

                if soft and actual is not None:
                    continue
                else:
                    setattr(i, key, value)

        self.struct_buttons()

        return None

    def struct_buttons(self) -> None:
        """Struct buttons method

        Struct buttons list by `orientation`.

        """

        self.buttons = sorted(self.buttons,
                              key=lambda button: button.orientation)

        return None

    def sort(self, key: Callable[[Button], bool]):
        """Sort method

        Sort buttons by key.

        Note: Sorting overwrite orientation order!

        """

        # TODO: compare orientation order and sort.
        # Make able to sort only one orientation
        # group, UNDEFINED by default.

        seq = sorted(self.buttons, key=key)
        self.buttons = list(seq)

        return None

    @overload
    def get_markup(self, markup_type: Literal['TEXT', None]) -> ReplyKeyboardMarkup:
        ...

    @overload
    def get_markup(self, markup_type: Literal['INLINE']) -> InlineKeyboardMarkup:
        ...

    def get_markup(self,
                   markup_type: Literal['TEXT', 'INLINE'] = None):

        """Get markup method

        Get TEXT or INLINE markup

        """

        if markup_type is None:
            markup_type = MarkupType.TEXT

        if markup_type == MarkupType.TEXT:
            markup = ReplyKeyboardMarkup(row_width=self.width,
                                         one_time_keyboard=self.one_time_keyboard,
                                         resize_keyboard=True)

            for i in self.buttons:
                markup.add(KeyboardButton(i.text))

        elif markup_type == MarkupType.INLINE:
            markup = ReplyKeyboardMarkup(row_width=self.width)

            for i in self.buttons:
                markup.add(InlineKeyboardButton(i.text, callback_data=i.data))

        else:
            raise KeyError(f'Unknown markup_type {markup_type}')

        return markup

    async def process(self,
                      raw_meta: meta_able_alias,
                      markup_scope: Literal['m', 'c', 'm+c'] = None) -> Message:

        """Process method

        Process markup in chat, mentioned in `meta` object.
        Markup scope makes able to hard set keyboard_type.

        :param raw_meta: meta of chat
        :param markup_scope: scope of markup processing
        :returns: Message object

        """

        if markup_scope is None:
            markup_scope = 'm+c'

        meta = DialogMeta(raw_meta)
        excepted_markup_type = MarkupScope.cast_to_type(markup_scope, ignore_error=True)

        if meta.markup_type in excepted_markup_type:
            markup_type = meta.markup_type
        else:
            markup_type = excepted_markup_type

        if markup_type == MarkupType.UNDEFINED:
            markup_type = MarkupType.TEXT

        dp = get_dp()
        reply_markup = self.get_markup(markup_type)

        logger.debug(f"Processing markup `{self.__class__.__name__}` at {meta.chat_id}:{meta.user_id}")

        if isinstance(self.text, str):
            text = self.text
        else:
            text = await self.text(meta)

        if markup_type == MarkupType.TEXT:
            response = await dp.bot.send_message(meta.chat_id, text, reply_markup=reply_markup)

        elif markup_type == MarkupType.INLINE:
            response = await dp.bot.edit_message_text(meta.chat_id,
                                                      text,
                                                      reply_markup=reply_markup,
                                                      message_id=meta.active_message_id)

        else:
            raise KeyError(f"Can't process markup with type {markup_type}")

        # Prepare to markup handle

        await self.definition_scope.set_state(raw_meta)

        return response

    def filter(self):
        """Filter for KeyBoard

        Creates filter that union all KeyBoard buttons,
        use it to handle data buttons.

        """

        result = BoolFilter(False)

        for i in self.buttons:
            result = result.__or__(i.filter())

        return result

    def hex_hash(self) -> str:
        summary = ''

        for i in self.buttons:
            summary += str(i.__content_hash__())

        result = _hash_text(summary)

        return result

    def __hash__(self) -> int:
        result = int(self.hex_hash(), 16)

        return result
