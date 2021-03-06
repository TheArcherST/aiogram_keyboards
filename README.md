Aiogram keyboards
=================

The package helps you construct and use inline or text keyboards.


Simple usage
------------

Let's start with example

```python

from aiogram_keyboards import Keyboard, Button

class MainMenu(Keyboard):
    settings = Button('Settings')
    help = Button('Help')

```

So, you can construct your markups by class,
inhered from `Keyboard`. But how you can use
it? You can get full markup and set handler
on any button in your menu. Example:

```python

bot = Bot(TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_handler(message):
    await message.answer(
        "Hi, im message with keyboard powered on aiogram_keyboards",
        reply_markup=MainMenu.get_markup()
    )


@dp.message_handler(MainMenu.settings.filter())
async def settings_handler(message):
    await message.answer("I know that you press on settings button!")


```

> Note:
> You can create button aliases. it means
> that button will be have same functional,
> only names were different. To create an
> alias, use func `button.alias(...)`

If you need in inline keyboard markup, not 
text, all that you need: instead method
`get_markup`, use method `get_inline_markup`, 
no changes in filter usage.

But you can ask, what is callback data of the 
button callback query? Callback data creating 
from prefix and MD5 text hash. Default prefix
is `::keyboard::` (in Button.CALLBACK_ROOT), 
and I not recommend changing it. But if you 
change, one condition: it must end on colon. 

How you can set up module middleware to void
all functional, let's look in following code:

```python

from aiogram_keyboards import setup_aiogram_keyboards


setup_aiogram_keyboards(dp)

```

What I did? I'm set up specify middleware, that 
skip states if sent text or callback found in 
any button pattern.

> Note:
> You can configure if button call raise state
> skip. Just give to button argument 
> `ignore_state` to initialization method. Also 
> you can set default call answer on button in
> argument `on_call`.


Data keyboards
--------------

You can make keyboards with need data in buttons.
Look at the following example:

```python

class DataKeyboardEx(Keyboard):
    __ignore_state__ = False
    
    hour = Button('Hour', data='h')
    minute = Button('Minute', data='m')
    second = Button('Second', data='s')

```

So, you can same get inline or keyboard markup.
If markup inline, data were in `call.data`, 
if text markup, in `message.text`.
Field `__ignore_state__` is default value of 
ignore_state for all buttons in keyboard. In 
data keyboards, if you use states, it must be 
set to False.

> Note: you can make fully messages from keyboards.
> Just write into field `__text__` message text and
> call method `Keyboard.process`.


Inheritance
-----------

You can merge two keyboards via inherit. For example,
you can have one undo keyboard and many data keyboards,
and you don't need to assign undo button every time,
use following feature:

```python

from aiogram_keyboards import Orientation


class CancelKeyboard(Keyboard):
    __orientation__ = Orientation.BOTTOM
    
    cancel = Button('Cancel')


class DataKeyboardEx(CancelKeyboard):
    __ignore_state__ = False
    
    hour = Button('Hour', data='h')
    minute = Button('Minute', data='m')
    second = Button('Second', data='s')

```

In code above, field `__orientation__` with value
`Orientation.BOTTOM` means that this keyboard must be
at the bottom if join to another. But this param you 
can set to any button, `Keyboard.__orientation__` field
just sets default value.

> Note: you can fast bind your keyboards/buttons, use
> method `bind` or operator `>>`. For example: 
> `CancelKeyboard.cancel >> MainMenuKeyboard`, binds 
> that cancel button must process MainMenuKeyboard.


Dialog (beta)
-------------

You can construct dialog by class and other objects. You
can set convertor for all values what bot collect during
dialog process. For example, you need to user enter his 
name and age, code:

```python

from aiogram_keyboards.dialog import Dialog, Text, Integer


class MainDialog(Dialog):
    name: Text = "Enter your name"
    age: Integer = "Enter your age"

    
@MainDialog.entry_point(commands=['start'])
async def main_dialog_handler(result: MainDialog):
    pass

```

And... it's already works! If we run command `/start`,
we will see processing dialog. To fetch dialog results,
just explore `result` variable. You can collect is so:

```python

@MainDialog.entry_point(commands=['start'])
async def main_dialog_handler(result: MainDialog):
    print(f'User name: {result.name.result}')
    # User name: <msg : str>
    
    print(f'User age: {result.age.result}')
    # User age <msg : int>

```

Also objects `result.name` and `result.age` have param
`obj`, is telegram object, what user sent as answer on 
question.

While handle answer, convertor tries to cast text to 
type that you provide as annotation dialog, but if 
he got troubles, question just repeating.

Let's explore patterns that helps you to write your 
dialog fastly

```python

class MainDialog(Dialog):
    name: Text = "Enter your name"
    age: Integer = "Enter your age"

```

Here is a dialog object from example above, but you can
use instead text Keyboard object. But this keyboard must 
contain not None `__text__` field.

```python

class DialogKeyboardEx(Keyboard):
    __text__ = "Enter your name"
    use_my_username = Button('Use my username')

    
class MainDialog(Dialog):
    name: Text = DialogKeyboardEx
    age: Integer = "Enter your age"

```

But this implementation looks bad, to just change message
text you must edit keyboard, and all usages of keyboard will
be use only this text. To solve it, use Keyboard method 
`customize` or operator `|` (method `__or__`)

```python

class DialogKeyboardEx(Keyboard):
    use_my_username = Button('Use my username')

    
class MainDialog(Dialog):
    name: Text = DialogKeyboardEx | "Enter your name"
    age: Integer = "Enter your age"

```

It's have same functionality.

Also, method operator `__or__`, if handle Keyboard, append all
buttons and inherit text, if target keyboard text is None.
For example, if on all steps you need in `Cancel` button, you can
implement it so:

```python

class CancelKeyboard(Keyboard):
    cancel = Button('Cancel')


class DialogKeyboardEx(Keyboard):
    use_my_username = Button('Use my username')

    
class MainDialog(Dialog):
    name: Text = CancelKeyboard | DialogKeyboardEx | "Enter your name"
    age: Integer = CancelKeyboard | "Enter your age"

```

Now we just add everywhere a `Cancel` buttons.
