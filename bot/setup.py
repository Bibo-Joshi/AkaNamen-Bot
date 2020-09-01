#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This module contains functions for setting up to bot at start up."""
from typing import List, Union

from telegram import BotCommand, Update
from telegram.ext import Dispatcher, TypeHandler, CommandHandler, CallbackQueryHandler, \
    InlineQueryHandler, Filters
from bot import (ORCHESTRA_KEY, PENDING_REGISTRATIONS_KEY, DENIED_USERS_KEY, ADMIN_KEY,
                 REGISTRATION_PATTERN, INLINE_HELP)

from bot.editing import EDITING_HANDLER
from bot.cancel_membership import CANCEL_MEMBERSHIP_HANDLER
from bot.ban import build_banning_handler
from bot.check_user_status import schedule_daily_job
import bot.registration as registration
import bot.commands as commands
import bot.inline as inline
import bot.highscore as highscore
import bot.error as error
import bot.game as game

from components import Orchestra

BOT_COMMANDS: List[BotCommand] = [
    BotCommand('spiel_starten', 'Startet ein neues Spiel'),
    BotCommand('spiel_abbrechen', 'Bricht das aktuelle Spiel ab'),
    BotCommand('daten_anzeigen', 'Zeigt Deine gespeicherten Daten an'),
    BotCommand('daten_bearbeiten', 'Daten wie Adresse und Foto ändern'),
    BotCommand('highscore', 'Zeigt den aktuellen Highscore an'),
    BotCommand('hilfe', 'Zeigt ein paar generelle Hinweise zum Bot'),
    BotCommand('kontakt_abrufen', 'Kontaktdaten anderer AkaBlasen abrufen'),
    BotCommand('start', 'Startet den Bot'),
    BotCommand('abmelden', 'Vom Bot abmelden und alle Daten löschen'),
]
"""List[:class:`telegram.BotCommand`]: A list of commands of the bot."""


def register_dispatcher(disptacher: Dispatcher, admin: Union[int, str]) -> None:
    """
    Adds handlers. Convenience method to avoid doing that all in the main script.
    Also sets the bot commands and makes sure ``dispatcher.bot_data`` is set up correctly.

    Args:
        disptacher: The :class:`telegram.ext.Dispatcher`.
        admin: The admins chat id.
    """
    # Handlers

    # Registration status
    disptacher.add_handler(TypeHandler(Update, registration.check_registration_status), group=-1)

    # Game Conversation
    # Must be first so that the fallback can catch unrelated messages
    disptacher.add_handler(game.GAME_HANDLER)

    # Registration process
    # We need the filter here in order to not catch /start with deep linking parameter used for
    # inline help
    disptacher.add_handler(
        CommandHandler('start', registration.start, filters=Filters.text('/start')))
    disptacher.add_handler(
        CallbackQueryHandler(registration.request_registration, pattern=REGISTRATION_PATTERN))
    disptacher.add_handler(registration.ACCEPT_REGISTRATION_HANDLER)
    disptacher.add_handler(registration.DENY_REGISTRATION_HANDLER)

    # Edit user data
    disptacher.add_handler(EDITING_HANDLER)

    # Cancel membership
    disptacher.add_handler(CANCEL_MEMBERSHIP_HANDLER)

    # Banning members
    disptacher.add_handler(build_banning_handler(int(admin)))

    # Simple commands
    disptacher.add_handler(CommandHandler(['hilfe', 'help'], commands.help_message))
    disptacher.add_handler(CommandHandler('daten_anzeigen', commands.show_data))
    disptacher.add_handler(CommandHandler('kontakt_abrufen', commands.start_inline))
    disptacher.add_handler(
        CommandHandler('start',
                       commands.start_inline,
                       filters=Filters.text(f'/start {INLINE_HELP}')))

    # Inline Mode
    disptacher.add_handler(InlineQueryHandler(inline.search_users))
    disptacher.add_handler(inline.SEND_VCARD_HANDLER)

    # Highscores
    disptacher.add_handler(CommandHandler('highscore', highscore.show_highscore))
    disptacher.add_handler(highscore.HIGHSCORE_HANDLER)

    # Error Handler
    disptacher.add_error_handler(error.handle_error)

    # Set commands
    disptacher.bot.set_my_commands(BOT_COMMANDS)

    # Schedule job deleting users who blocked the bot
    schedule_daily_job(disptacher)

    # Set up bot_data
    bot_data = disptacher.bot_data
    if not bot_data.get(ORCHESTRA_KEY):
        bot_data[ORCHESTRA_KEY] = Orchestra()
    if not bot_data.get(PENDING_REGISTRATIONS_KEY):
        bot_data[PENDING_REGISTRATIONS_KEY] = dict()
    if not bot_data.get(DENIED_USERS_KEY):
        bot_data[DENIED_USERS_KEY] = list()
    bot_data[ADMIN_KEY] = int(admin)
